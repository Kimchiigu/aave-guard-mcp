import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from web3 import Web3
from dotenv import load_dotenv

# --- 1. SETUP & CONFIGURATION ---
load_dotenv()

# --- Environment Variables ---
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
EXECUTOR_PRIVATE_KEY = os.getenv("EXECUTOR_PRIVATE_KEY")
AAVE_POOL_ADDRESS_PROVIDER = os.getenv("AAVE_POOL_ADDRESS_PROVIDER_V3_BASE_SEPOLIA")

if not all([ALCHEMY_API_KEY, EXECUTOR_PRIVATE_KEY, AAVE_POOL_ADDRESS_PROVIDER]):
    raise ValueError("❌ Missing required .env variables.")

# --- Web3 Connection ---
w3 = Web3(Web3.HTTPProvider(f"https://base-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}"))
executor_account = w3.eth.account.from_key(EXECUTOR_PRIVATE_KEY)
print(f"✅ API Server starting with executor wallet: {executor_account.address}")

# --- Asset Registry for AI Agent ---
ASSET_REGISTRY = {
    "USDC": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "WETH": "0x4200000000000000000000000000000000000006",
}

# --- Aave Contract ABIs ---
POOL_ADDRESS_PROVIDER_ABI = '[{"inputs":[],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getPoolDataProvider","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]'
AAVE_POOL_ABI = '[{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserAccountData","outputs":[{"internalType":"uint256","name":"totalCollateralBase","type":"uint256"},{"internalType":"uint256","name":"totalDebtBase","type":"uint256"},{"internalType":"uint256","name":"availableBorrowsBase","type":"uint256"},{"internalType":"uint256","name":"currentLiquidationThreshold","type":"uint256"},{"internalType":"uint256","name":"ltv","type":"uint256"},{"internalType":"uint256","name":"healthFactor","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"supply","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"interestRateMode","type":"uint256"},{"internalType":"uint16","name":"referralCode","type":"uint16"},{"internalType":"address","name":"onBehalfOf","type":"address"}],"name":"borrow","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"rateMode","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"}],"name":"repay","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"payable","type":"function"}]'
AAVE_DATA_PROVIDER_ABI = '[{"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"address","name":"user","type":"address"}],"name":"getUserReserveData","outputs":[{"internalType":"uint256","name":"currentATokenBalance","type":"uint256"},{"internalType":"uint256","name":"currentStableDebt","type":"uint256"},{"internalType":"uint256","name":"currentVariableDebt","type":"uint256"},{"internalType":"uint256","name":"principalStableDebt","type":"uint256"},{"internalType":"uint256","name":"scaledVariableDebt","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint40","name":"stableRateLastUpdated","type":"uint40"},{"internalType":"bool","name":"usageAsCollateralEnabled","type":"bool"}],"stateMutability":"view","type":"function"}]'
ERC20_ABI = '[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]'

# --- Contract Initialization ---
address_provider = w3.eth.contract(address=Web3.to_checksum_address(AAVE_POOL_ADDRESS_PROVIDER), abi=POOL_ADDRESS_PROVIDER_ABI)
pool_address = address_provider.functions.getPool().call()
data_provider_address = address_provider.functions.getPoolDataProvider().call()
pool_contract = w3.eth.contract(address=pool_address, abi=AAVE_POOL_ABI)
data_provider = w3.eth.contract(address=data_provider_address, abi=AAVE_DATA_PROVIDER_ABI)
print(f"📘 Aave Pool Address: {pool_address}")

# --- 2. CORE AAVE LOGIC ---
def get_health_factor(user_address: str):
    user_data = pool_contract.functions.getUserAccountData(Web3.to_checksum_address(user_address)).call()
    return user_data[5] / 1e18

def get_asset_decimals(asset_address: str):
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(asset_address), abi=ERC20_ABI)
    return token_contract.functions.decimals().call()

def execute_supply(user_address: str, asset_address: str, amount: float):
    user_checksum = Web3.to_checksum_address(user_address)
    asset_checksum = Web3.to_checksum_address(asset_address)
    decimals = get_asset_decimals(asset_checksum)
    amount_in_wei = int(amount * (10**decimals))
    asset_contract = w3.eth.contract(address=asset_checksum, abi=ERC20_ABI)
    executor_balance = asset_contract.functions.balanceOf(executor_account.address).call()
    if executor_balance < amount_in_wei:
        return {"status": "error", "message": f"Executor has insufficient balance to supply {amount}. Has: {executor_balance / (10**decimals)}"}
    allowance = asset_contract.functions.allowance(executor_account.address, pool_address).call()
    if allowance < amount_in_wei:
        approve_tx = asset_contract.functions.approve(pool_address, amount_in_wei).build_transaction({
            "from": executor_account.address, "chainId": 84532, "nonce": w3.eth.get_transaction_count(executor_account.address)
        })
        signed_approve = w3.eth.account.sign_transaction(approve_tx, EXECUTOR_PRIVATE_KEY)
        tx_hash_approve = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash_approve)
    supply_tx = pool_contract.functions.supply(asset_checksum, amount_in_wei, user_checksum, 0).build_transaction({
        "from": executor_account.address, "chainId": 84532, "nonce": w3.eth.get_transaction_count(executor_account.address)
    })
    signed_tx = w3.eth.account.sign_transaction(supply_tx, EXECUTOR_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return {"status": "success", "message": "Supply transaction sent successfully.", "tx_hash": tx_hash.hex()}

def execute_borrow(user_address: str, asset_address: str, amount: float, rate_mode: int):
    user_checksum = Web3.to_checksum_address(user_address)
    asset_checksum = Web3.to_checksum_address(asset_address)
    decimals = get_asset_decimals(asset_checksum)
    amount_in_wei = int(amount * (10**decimals))
    borrow_tx = pool_contract.functions.borrow(asset_checksum, amount_in_wei, rate_mode, 0, user_checksum).build_transaction({
        "from": executor_account.address, "chainId": 84532, "nonce": w3.eth.get_transaction_count(executor_account.address)
    })
    signed_tx = w3.eth.account.sign_transaction(borrow_tx, EXECUTOR_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return {"status": "success", "message": "Borrow transaction sent successfully.", "tx_hash": tx_hash.hex()}

def execute_repay(user_address: str, asset_address: str):
    user_checksum = Web3.to_checksum_address(user_address)
    asset_checksum = Web3.to_checksum_address(asset_address)
    data = data_provider.functions.getUserReserveData(asset_checksum, user_checksum).call()
    stable_debt, variable_debt = data[1], data[2]
    rate_mode = 1 if stable_debt > 0 else 2 if variable_debt > 0 else 0
    if rate_mode == 0: return {"status": "success", "message": "No active debt found to repay."}
    user_total_debt = stable_debt + variable_debt
    debt_token_contract = w3.eth.contract(address=asset_checksum, abi=ERC20_ABI)
    executor_balance = debt_token_contract.functions.balanceOf(executor_account.address).call()
    if executor_balance == 0: return {"status": "error", "message": "Executor wallet has zero balance for the specified asset."}
    amount_to_repay = min(user_total_debt, executor_balance)
    allowance = debt_token_contract.functions.allowance(executor_account.address, pool_address).call()
    if allowance < amount_to_repay:
        approve_tx = debt_token_contract.functions.approve(pool_address, 2**256 - 1).build_transaction({
            "from": executor_account.address, "chainId": 84532, "nonce": w3.eth.get_transaction_count(executor_account.address)
        })
        signed_approve = w3.eth.account.sign_transaction(approve_tx, EXECUTOR_PRIVATE_KEY)
        tx_hash_approve = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash_approve)
    repay_tx = pool_contract.functions.repay(asset_checksum, amount_to_repay, rate_mode, user_checksum).build_transaction({
        "from": executor_account.address, "chainId": 84532, "nonce": w3.eth.get_transaction_count(executor_account.address)
    })
    signed_tx = w3.eth.account.sign_transaction(repay_tx, EXECUTOR_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return {"status": "success", "message": "Repay transaction sent successfully.", "tx_hash": tx_hash.hex()}


# --- 3. API DEFINITION ---
app = FastAPI(
    title="Aave Concierge API (MCP Compliant)",
    description="A serverless API for executing Aave V3 actions, compliant with the Model Context Protocol.",
    version="6.0.0",
)

# --- NEW: MCP Discovery Endpoint ---
@app.get("/mcp")
def mcp_discovery():
    """
    The official discovery endpoint that describes this API's capabilities to an AI.
    """
    return {
        "service": {
            "name": "aave_concierge",
            "display_name": "Aave Concierge",
            "description": "An API to supply, borrow, repay, and check health on the Aave V3 protocol."
        },
        "resources": [
            {
                "name": "Loan",
                "display_name": "Aave Loan",
                "description": "Represents a user's loan position on Aave.",
                "operations": [
                    {
                        "name": "check_health",
                        "description": "Checks the health factor of a user's loan.",
                        "http_handler": { "method": "GET", "path": "/health/{user_address}" },
                        "parameters": [
                            {"name": "user_address", "type": "string", "in": "path", "description": "The user's wallet address."}
                        ]
                    },
                    {
                        "name": "repay",
                        "description": "Repays a user's debt for a specific asset.",
                        "http_handler": { "method": "POST", "path": "/repay" },
                        "parameters": [
                             {"name": "user_address", "type": "string", "in": "body", "description": "The user's wallet address."},
                             {"name": "asset_symbol", "type": "string", "in": "body", "description": "The symbol of the asset to repay, e.g., 'USDC'."}
                        ]
                    },
                    {
                        "name": "supply",
                        "description": "Supplies an asset to Aave on behalf of a user.",
                        "http_handler": { "method": "POST", "path": "/supply" },
                         "parameters": [
                             {"name": "user_address", "type": "string", "in": "body", "description": "The user's wallet address."},
                             {"name": "asset_symbol", "type": "string", "in": "body", "description": "The symbol of the asset to supply, e.g., 'WETH'."},
                             {"name": "amount", "type": "number", "in": "body", "description": "The amount to supply."}
                        ]
                    },
                    {
                        "name": "borrow",
                        "description": "Borrows an asset from Aave for a user.",
                        "http_handler": { "method": "POST", "path": "/borrow" },
                        "parameters": [
                             {"name": "user_address", "type": "string", "in": "body", "description": "The user's wallet address."},
                             {"name": "asset_symbol", "type": "string", "in": "body", "description": "The symbol of the asset to borrow, e.g., 'USDC'."},
                             {"name": "amount", "type": "number", "in": "body", "description": "The amount to borrow."}
                        ]
                    }
                ]
            }
        ]
    }


# --- Pydantic Models ---
class HealthResponse(BaseModel):
    user_address: str
    health_factor: float

class TxRequestSymbol(BaseModel):
    user_address: str
    asset_symbol: str = Field(..., description="The symbol of the asset, e.g., 'USDC' or 'WETH'")
    amount: float

class BorrowRequestSymbol(BaseModel):
    user_address: str
    asset_symbol: str = Field(..., description="The symbol of the asset, e.g., 'USDC' or 'WETH'")
    amount: float
    interest_rate_mode: int = Field(default=2, description="1 for Stable, 2 for Variable")

class RepayRequestSymbol(BaseModel):
    user_address: str
    asset_symbol: str = Field(..., description="The symbol of the asset to repay, e.g., 'USDC'")

class TxResponse(BaseModel):
    status: str
    message: str
    tx_hash: str | None = None

# --- API Endpoints ---
@app.get("/health/{user_address}", response_model=HealthResponse)
async def check_health(user_address: str):
    health = get_health_factor(user_address)
    return HealthResponse(user_address=user_address, health_factor=health)

@app.post("/supply", response_model=TxResponse)
async def supply(req: TxRequestSymbol):
    asset_address = ASSET_REGISTRY.get(req.asset_symbol.upper())
    if not asset_address:
        raise HTTPException(status_code=400, detail=f"Asset symbol '{req.asset_symbol}' not found.")
    try:
        result = execute_supply(req.user_address, asset_address, req.amount)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/borrow", response_model=TxResponse)
async def borrow(req: BorrowRequestSymbol):
    asset_address = ASSET_REGISTRY.get(req.asset_symbol.upper())
    if not asset_address:
        raise HTTPException(status_code=400, detail=f"Asset symbol '{req.asset_symbol}' not found.")
    try:
        result = execute_borrow(req.user_address, asset_address, req.amount, req.interest_rate_mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/repay", response_model=TxResponse)
async def repay(req: RepayRequestSymbol):
    asset_address = ASSET_REGISTRY.get(req.asset_symbol.upper())
    if not asset_address:
        raise HTTPException(status_code=400, detail=f"Asset symbol '{req.asset_symbol}' not found.")
    try:
        result = execute_repay(req.user_address, asset_address)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

