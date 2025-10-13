import os, asyncio, aiohttp, traceback
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# ENVIRONMENT SETUP
# ============================================================

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
EXECUTOR_PRIVATE_KEY = os.getenv("EXECUTOR_PRIVATE_KEY")
AAVE_POOL_PROVIDER_BASE_SEPOLIA = os.getenv("AAVE_POOL_ADDRESS_PROVIDER_V3_BASE_SEPOLIA")
HEDERA_LOGGER_URL = os.getenv("HEDERA_LOGGER_URL", "https://aave-guard-mcp.vercel.app/hedera")
DEFAULT_NETWORK = os.getenv("NETWORK", "base-sepolia").lower()

if not (ALCHEMY_API_KEY and EXECUTOR_PRIVATE_KEY):
    raise ValueError("Missing ALCHEMY_API_KEY or EXECUTOR_PRIVATE_KEY in .env")

# ============================================================
# NETWORK CONFIGURATIONS
# ============================================================

NETWORK_CONFIG = {
    "base-sepolia": {
        "chain_id": 84532,
        "rpc": f"https://base-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
        "pool_provider": AAVE_POOL_PROVIDER_BASE_SEPOLIA,
        "assets": {
            "USDC": "0xba50cd2a20f6da35d788639e581bca8d0b5d4d5f",
            "WETH": "0x4200000000000000000000000000000000000006",
            "USDT": "0x0a215d8ba66387dca84b284d18c3b4ec3de6e54a",
            "WBTC": "0x54114591963cf60ef3aa63befd6ec263d98145a4",
            "cbETH": "0xd171b9694f7a2597ed006d41f7509aad4b485c4b",
            "LINK": "0x810d46f9a9027e28f9b01f75e2bdde839da61115",
        },
    },
    "eth-sepolia": {
        "chain_id": 11155111,
        "rpc": f"https://eth-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
        "assets": {
            "WBTC": "0x29f2d40b0605204364af54ec677bd022da425d03",
            "GHO": "0xc4bf5cbdabe595361438f8c6a187bdc330539c60",
            "LINK": "0xf8fb3713d459d7c1018bd0a49d19b4c44290ebe5",
            "DAI": "0xff34b3d4aee8ddcd6f9afffb6fe49bd371b8a357",
            "USDT": "0xaa8e23fb1079ea71e0a56f48a2aa51851d8433d0",
            "USDC": "0x94a9d9ac8a22534e3faca9f4e7f2e2cf85d5e4c8",
            "AAVE": "0x88541670e55cc00beefd87eb59edd1b7c511ac9a",
            "WETH": "0xc558dbdd856501fcd9aaf1e62eae57a9f0629a3c",
            "EURS": "0x6d906e526a4e2ca02097ba9d0caa3c382f52278e",
        },
    },
}

for net in NETWORK_CONFIG.values():
    net["assets"] = {k: Web3.to_checksum_address(v) for k, v in net["assets"].items()}
    if "pool_provider" in net:
        net["pool_provider"] = Web3.to_checksum_address(net["pool_provider"])

# ============================================================
# HELPERS
# ============================================================

def get_network_config(name: str):
    key = name.lower().replace(" ", "-")
    if key not in NETWORK_CONFIG:
        raise HTTPException(400, f"Unsupported network: {name}")
    return NETWORK_CONFIG[key]


def init_web3(network_name: str):
    cfg = get_network_config(network_name)
    w3 = Web3(Web3.HTTPProvider(cfg["rpc"]))
    executor = w3.eth.account.from_key(EXECUTOR_PRIVATE_KEY)
    return w3, executor, cfg


async def log_to_hedera(msg: str):
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(HEDERA_LOGGER_URL, json={"log_message": msg}, timeout=5)
        except Exception as e:
            print("[WARN] Hedera log failed:", e)


def schedule_log(msg: str):
    try:
        asyncio.create_task(log_to_hedera(msg))
    except RuntimeError:
        asyncio.run(log_to_hedera(msg))


def get_pool_contract(w3, provider_addr):
    provider_abi = [
        {"inputs": [], "name": "getPool", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    ]
    provider = w3.eth.contract(address=provider_addr, abi=provider_abi)
    pool_addr = provider.functions.getPool().call()
    pool_abi = [
        {
            "inputs": [{"type": "address", "name": "user"}],
            "name": "getUserAccountData",
            "outputs": [
                {"type": "uint256", "name": "totalCollateralBase"},
                {"type": "uint256", "name": "totalDebtBase"},
                {"type": "uint256", "name": "availableBorrowsBase"},
                {"type": "uint256", "name": "currentLiquidationThreshold"},
                {"type": "uint256", "name": "ltv"},
                {"type": "uint256", "name": "healthFactor"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"type": "address", "name": "asset"},
                {"type": "uint256", "name": "amount"},
                {"type": "address", "name": "onBehalfOf"},
                {"type": "uint16", "name": "referralCode"},
            ],
            "name": "supply",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"type": "address", "name": "asset"},
                {"type": "uint256", "name": "amount"},
                {"type": "uint256", "name": "interestRateMode"},
                {"type": "uint16", "name": "referralCode"},
                {"type": "address", "name": "onBehalfOf"},
            ],
            "name": "borrow",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"type": "address", "name": "asset"},
                {"type": "uint256", "name": "amount"},
                {"type": "uint256", "name": "rateMode"},
                {"type": "address", "name": "onBehalfOf"},
            ],
            "name": "repay",
            "outputs": [{"type": "uint256", "name": ""}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
    ]
    return w3.eth.contract(address=pool_addr, abi=pool_abi)


def get_health_factor(pool, user):
    try:
        data = pool.functions.getUserAccountData(user).call()
        return round(data[5] / 1e18 if data[5] else 0, 3)
    except Exception:
        return 0

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Aave Concierge API - MCP Compliant",
    description="MCP-compliant API for AI agents to manage Aave loans, supplies, and borrows with natural language commands. Built for Aya Wallet integration.",
    version="6.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "LoanGuardian Team",
        "email": "christopher.hygunawan@gmail.com",
        "url": "https://github.com/Kimchiigu/aave-guard-mcp"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "https://aave-guard-mcp.vercel.app",
            "description": "Production deployment"
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development"
        }
    ],
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
        "docExpansion": "none"
    }
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_mcp_headers(request: Request, call_next):
    """Add MCP-specific headers for AI agent discovery."""
    response = await call_next(request)

    # Add MCP discovery headers
    response.headers["X-MCP-Version"] = "1.0"
    response.headers["X-MCP-Endpoint"] = "/mcp-manifest"
    response.headers["X-AI-Agent-Friendly"] = "true"
    response.headers["X-API-Purpose"] = "Aave DeFi Operations"

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serve the landing page HTML content.
    Users are directed to visit /docs to try the API.
    """
    with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/landing")
async def landing():
    """
    Redirect to the landing page.
    """
    return RedirectResponse(url="/")


@app.get("/mcp-manifest")
async def mcp_manifest():
    """
    Serve the MCP manifest file for AI agent discovery.
    """
    manifest_path = os.path.join(static_dir, "mcp-manifest.json")
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_content = f.read()
        return JSONResponse(content=json.loads(manifest_content))
    except FileNotFoundError:
        raise HTTPException(404, "MCP manifest not found")
    except json.JSONDecodeError:
        raise HTTPException(500, "Invalid MCP manifest format")


class AaveRequest(BaseModel):
    amount: float
    token: str
    network: str = DEFAULT_NETWORK
    user_address: str


# ============================================================
# API ENDPOINTS
# ============================================================

@app.post("/supply")
async def supply(req: AaveRequest):
    """Supply tokens and log to Hedera."""
    try:
        w3, executor, cfg = init_web3(req.network)
        token = req.token.upper()
        if token not in cfg["assets"]:
            raise HTTPException(400, f"{token} not supported on {req.network}")

        asset = Web3.to_checksum_address(cfg["assets"][token])
        decimals = 6 if token.startswith("USDC") else 18
        amount_wei = int(req.amount * 10**decimals)
        user = Web3.to_checksum_address(req.user_address)
        provider_addr = Web3.to_checksum_address(cfg["pool_provider"])
        pool = get_pool_contract(w3, provider_addr)

        tx = {
            "from": user,
            "nonce": w3.eth.get_transaction_count(user),
            "chainId": cfg["chain_id"],
            "gas": 300000,
        }
        fn = pool.functions.supply(asset, amount_wei, user, 0)
        signed = executor.sign_transaction(fn.build_transaction(tx))
        txh = w3.eth.send_raw_transaction(signed.raw_transaction)
        rc = w3.eth.wait_for_transaction_receipt(txh)

        msg = f"SUPPLY {req.amount} {token} on {req.network} by {user}, status={rc.status}"
        schedule_log(msg)

        if rc.status == 1:
            return {"status": "success", "tx_hash": txh.hex()}
        raise HTTPException(500, "Supply failed")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.post("/borrow")
async def borrow(req: AaveRequest):
    """Borrow tokens safely with health factor check."""
    try:
        w3, executor, cfg = init_web3(req.network)
        token = req.token.upper()
        if token not in cfg["assets"]:
            raise HTTPException(400, f"{token} not supported on {req.network}")

        provider_addr = Web3.to_checksum_address(cfg["pool_provider"])
        pool = get_pool_contract(w3, provider_addr)
        user = Web3.to_checksum_address(req.user_address)
        hf = get_health_factor(pool, user)

        if hf < 1.1:
            msg = f"❌ Borrow blocked — health factor={hf}"
            schedule_log(msg)
            raise HTTPException(400, f"Health factor too low ({hf}). Borrowing not safe.")

        asset = Web3.to_checksum_address(cfg["assets"][token])
        decimals = 6 if token.startswith("USDC") else 18
        amount_wei = int(req.amount * 10**decimals)

        fn = pool.functions.borrow(asset, amount_wei, 2, 0, user)
        tx = {
            "from": user,
            "nonce": w3.eth.get_transaction_count(user),
            "chainId": cfg["chain_id"],
            "gas": 400000,
        }
        signed = executor.sign_transaction(fn.build_transaction(tx))
        txh = w3.eth.send_raw_transaction(signed.raw_transaction)
        rc = w3.eth.wait_for_transaction_receipt(txh)

        msg = f"BORROW {req.amount} {token} on {req.network}, HF_before={hf}, status={rc.status}"
        schedule_log(msg)

        if rc.status == 1:
            return {"status": "success", "tx_hash": txh.hex(), "health_factor_before": hf}
        raise HTTPException(500, "Borrow failed")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.post("/repay")
async def repay(req: AaveRequest):
    """Repay borrowed tokens."""
    try:
        w3, executor, cfg = init_web3(req.network)
        token = req.token.upper()
        if token not in cfg["assets"]:
            raise HTTPException(400, f"{token} not supported on {req.network}")

        asset = Web3.to_checksum_address(cfg["assets"][token])
        decimals = 6 if token.startswith("USDC") else 18
        amount_wei = int(req.amount * 10**decimals)
        user = Web3.to_checksum_address(req.user_address)
        provider_addr = Web3.to_checksum_address(cfg["pool_provider"])
        pool = get_pool_contract(w3, provider_addr)

        fn = pool.functions.repay(asset, amount_wei, 2, user)
        tx = {
            "from": user,
            "nonce": w3.eth.get_transaction_count(user),
            "chainId": cfg["chain_id"],
            "gas": 300000,
        }
        signed = executor.sign_transaction(fn.build_transaction(tx))
        txh = w3.eth.send_raw_transaction(signed.raw_transaction)
        rc = w3.eth.wait_for_transaction_receipt(txh)

        msg = f"REPAY {req.amount} {token} on {req.network} by {user}, status={rc.status}"
        schedule_log(msg)

        if rc.status == 1:
            return {"status": "success", "tx_hash": txh.hex()}
        raise HTTPException(500, "Repay failed")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))

@app.get("/health/{network}/{user}")
async def health(network: str, user: str):
    w3, _, cfg = init_web3(network)
    pool = get_pool_contract(w3, Web3.to_checksum_address(cfg["pool_provider"]))
    hf = get_health_factor(pool, Web3.to_checksum_address(user))
    return {"health_factor": hf, "safe_to_borrow": hf >= 1.1}


@app.get("/balance/{network}/{user}")
async def balance(network: str, user: str):
    w3, _, cfg = init_web3(network)
    balances = {}
    for t, addr in cfg["assets"].items():
        abi = [{"name": "balanceOf", "inputs": [{"type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]
        token = w3.eth.contract(address=addr, abi=abi)
        try:
            raw = token.functions.balanceOf(Web3.to_checksum_address(user)).call()
            decimals = 6 if t.startswith("USDC") else 18
            balances[t] = round(raw / (10 ** decimals), 6)
        except Exception:
            balances[t] = 0
    return {"address": user, "network": network, "balances": balances}


@app.post("/simulate")
async def simulate(req: AaveRequest):
    """Dry-run simulation of supply or borrow to estimate health factor effect."""
    w3, _, cfg = init_web3(req.network)
    user = Web3.to_checksum_address(req.user_address)
    pool = get_pool_contract(w3, Web3.to_checksum_address(cfg["pool_provider"]))
    hf_before = get_health_factor(pool, user)
    action = "supply" if req.amount > 0 else "borrow"
    hf_after = round(hf_before * (1.02 if action == "supply" else 0.97), 3)
    safety = "safe ✅" if hf_after >= 1.1 else "risky ⚠️"
    msg = f"Simulated {action} {req.amount} {req.token} on {req.network}: HF {hf_before}→{hf_after} ({safety})"
    schedule_log(msg)
    return {
        "action": action,
        "token": req.token.upper(),
        "amount": req.amount,
        "network": req.network,
        "health_factor_before": hf_before,
        "health_factor_after_est": hf_after,
        "safety": safety,
        "note": "Dry-run only; no blockchain transaction executed."
    }
