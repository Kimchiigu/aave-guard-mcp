import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from web3 import Web3
from dotenv import load_dotenv
from hexbytes import HexBytes
import traceback

# --- 1. SETUP & CONFIGURATION ---
load_dotenv()

# --- Environment Variables ---
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
EXECUTOR_PRIVATE_KEY = os.getenv("EXECUTOR_PRIVATE_KEY")
AAVE_POOL_ADDRESS_PROVIDER = os.getenv("AAVE_POOL_ADDRESS_PROVIDER_V3_BASE_SEPOLIA")
HEDERA_LOGGER_API_URL = os.getenv("HEDERA_LOGGER_API_URL")

if not all([ALCHEMY_API_KEY, EXECUTOR_PRIVATE_KEY, AAVE_POOL_ADDRESS_PROVIDER]):
    raise ValueError("❌ Missing required .env variables.")

# --- Web3 Connection ---
w3 = Web3(Web3.HTTPProvider(f"https://base-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}"))
executor_account = w3.eth.account.from_key(EXECUTOR_PRIVATE_KEY)
EXECUTOR_ADDRESS = Web3.to_checksum_address(executor_account.address)
CHAIN_ID = 84532  # Base Sepolia chain id
print(f"✅ API Server starting with executor wallet: {EXECUTOR_ADDRESS}")

# --- Asset Registry for AI Agent ---
# Base Sepolia Testnet
ASSET_REGISTRY = {
    "USDC": "0xba50cd2a20f6da35d788639e581bca8d0b5d4d5f",
    "WETH": "0x4200000000000000000000000000000000000006",
    "USDT": "0x0a215d8ba66387dca84b284d18c3b4ec3de6e54a",
    "WBTC": "0x54114591963cf60ef3aa63befd6ec263d98145a4",
    "cbETH": "0xd171b9694f7a2597ed006d41f7509aad4b485c4b",
    "LINK": "0x810d46f9a9027e28f9b01f75e2bdde839da61115"
}

# --- Aave Contract ABIs ---
POOL_ADDRESS_PROVIDER_ABI = """
[
  {"inputs":[],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getPoolDataProvider","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]
"""

AAVE_POOL_ABI = """
[
  {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserAccountData","outputs":[{"internalType":"uint256","name":"totalCollateralBase","type":"uint256"},{"internalType":"uint256","name":"totalDebtBase","type":"uint256"},{"internalType":"uint256","name":"availableBorrowsBase","type":"uint256"},{"internalType":"uint256","name":"currentLiquidationThreshold","type":"uint256"},{"internalType":"uint256","name":"ltv","type":"uint256"},{"internalType":"uint256","name":"healthFactor","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"supply","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"interestRateMode","type":"uint256"},{"internalType":"uint16","name":"referralCode","type":"uint16"},{"internalType":"address","name":"onBehalfOf","type":"address"}],"name":"borrow","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"rateMode","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"}],"name":"repay","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]
"""

AAVE_DATA_PROVIDER_ABI = """
[
  {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"address","name":"user","type":"address"}],"name":"getUserReserveData","outputs":[{"internalType":"uint256","name":"currentATokenBalance","type":"uint256"},{"internalType":"uint256","name":"currentStableDebt","type":"uint256"},{"internalType":"uint256","name":"currentVariableDebt","type":"uint256"},{"internalType":"uint256","name":"principalStableDebt","type":"uint256"},{"internalType":"uint256","name":"scaledVariableDebt","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint40","name":"stableRateLastUpdated","type":"uint40"},{"internalType":"bool","name":"usageAsCollateralEnabled","type":"bool"}],"stateMutability":"view","type":"function"}
]
"""

ERC20_ABI = """
[
  {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
]
"""

# --- Contract Initialization ---
address_provider = w3.eth.contract(address=Web3.to_checksum_address(AAVE_POOL_ADDRESS_PROVIDER), abi=POOL_ADDRESS_PROVIDER_ABI)
pool_address = Web3.to_checksum_address(address_provider.functions.getPool().call())
data_provider_address = Web3.to_checksum_address(address_provider.functions.getPoolDataProvider().call())
pool_contract = w3.eth.contract(address=pool_address, abi=AAVE_POOL_ABI)
data_provider = w3.eth.contract(address=data_provider_address, abi=AAVE_DATA_PROVIDER_ABI)
print(f"📘 Aave Pool Address: {pool_address}")
print(f"📗 Aave PoolDataProvider Address: {data_provider_address}")

# --- Debug Utilities ---
def debug_call(func, *args, **kwargs):
    """Try eth_call before send to capture revert reasons."""
    try:
        func(*args, **kwargs).call({"from": EXECUTOR_ADDRESS})
        print("🟢 Dry run succeeded.")
    except Exception as e:
        print("🔴 Dry run reverted!")
        print(traceback.format_exc())

# --- Helpers ---
def log_to_hedera(log_message: str):
    if not HEDERA_LOGGER_API_URL:
        print("🟡 HCS Log skipped (URL not set).")
        return
    try:
        response = requests.post(
            HEDERA_LOGGER_API_URL,
            json={"log_message": log_message},
            timeout=10
        )
        response.raise_for_status()
        print(f"✅ HCS Log successful: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"🔴 HCS Log Error: {e}")

def get_health_factor(user_address: str):
    user_data = pool_contract.functions.getUserAccountData(Web3.to_checksum_address(user_address)).call()
    return user_data[5] / 1e18

def get_asset_decimals(asset_address: str):
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(asset_address), abi=ERC20_ABI)
    return token_contract.functions.decimals().call()

def _send_and_wait(signed_raw_tx: HexBytes, timeout: int = 120):
    tx_hash = w3.eth.send_raw_transaction(signed_raw_tx)
    print(f"🔁 Sent tx: {tx_hash.hex()} — waiting for receipt...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
    print(f"✅ Receipt: status={receipt.status}, blockNumber={receipt.blockNumber}")
    return tx_hash, receipt

def _safe_approve_if_needed(token_contract, owner_addr, spender_addr, required_amount, nonce):
    allowance = token_contract.functions.allowance(owner_addr, spender_addr).call()
    print(f"💳 Allowance check: {allowance}, required: {required_amount}")
    if allowance >= required_amount:
        print("✅ Enough allowance, skip approve.")
        return nonce
    approve_tx = token_contract.functions.approve(spender_addr, required_amount).build_transaction({
        "from": owner_addr,
        "chainId": CHAIN_ID,
        "nonce": nonce,
        "gas": 100000,
        "gasPrice": w3.eth.gas_price,
    })
    signed_approve = w3.eth.account.sign_transaction(approve_tx, EXECUTOR_PRIVATE_KEY)
    tx_hash_approve, receipt_approve = _send_and_wait(signed_approve.raw_transaction)
    if receipt_approve.status != 1:
        raise Exception("Approve transaction failed")
    return nonce + 1

# --- Supply / Borrow / Repay (with debug) ---
def execute_supply(user_address: str, asset_symbol: str, asset_address: str, amount: float):
    print("\n🚀 Executing SUPPLY...")
    try:
        user_checksum = Web3.to_checksum_address(user_address)
        asset_checksum = Web3.to_checksum_address(asset_address)
        decimals = get_asset_decimals(asset_checksum)
        amount_in_wei = int(amount * (10 ** decimals))
        print(f"🔢 Supply {amount} {asset_symbol} = {amount_in_wei} (wei)")

        asset_contract = w3.eth.contract(address=asset_checksum, abi=ERC20_ABI)
        executor_balance = asset_contract.functions.balanceOf(EXECUTOR_ADDRESS).call()
        print(f"💰 Executor balance: {executor_balance / (10 ** decimals)} {asset_symbol}")

        if executor_balance < amount_in_wei:
            return {"status": "error", "message": f"Executor insufficient {asset_symbol} balance."}

        nonce = w3.eth.get_transaction_count(EXECUTOR_ADDRESS)
        nonce = _safe_approve_if_needed(asset_contract, EXECUTOR_ADDRESS, pool_address, amount_in_wei, nonce)

        # Dry run to capture revert reason
        debug_call(pool_contract.functions.supply, asset_checksum, amount_in_wei, user_checksum, 0)

        try:
            gas_estimate = pool_contract.functions.supply(asset_checksum, amount_in_wei, user_checksum, 0).estimate_gas({"from": EXECUTOR_ADDRESS})
        except Exception as e:
            print(f"⚠️ Gas estimate failed: {e}")
            gas_estimate = 300000

        print(f"⛽ Gas estimate: {gas_estimate}")

        supply_tx = pool_contract.functions.supply(asset_checksum, amount_in_wei, user_checksum, 0).build_transaction({
            "from": EXECUTOR_ADDRESS,
            "chainId": CHAIN_ID,
            "gas": gas_estimate,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
        })
        signed_tx = w3.eth.account.sign_transaction(supply_tx, EXECUTOR_PRIVATE_KEY)
        tx_hash, receipt = _send_and_wait(signed_tx.raw_transaction)
        if receipt.status != 1:
            return {"status": "error", "message": "Supply transaction reverted."}
        log_to_hedera(f"AAVE_SUPPLY: {user_address} supplied {amount} {asset_symbol}. Tx: {tx_hash.hex()}")
        return {"status": "success", "message": "Supply OK", "tx_hash": tx_hash.hex()}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": f"Supply error: {e}"}

def execute_borrow(user_address: str, asset_symbol: str, asset_address: str, amount: float, rate_mode: int):
    print("\n🚀 Executing BORROW...")
    try:
        user_checksum = Web3.to_checksum_address(user_address)
        asset_checksum = Web3.to_checksum_address(asset_address)
        decimals = get_asset_decimals(asset_checksum)
        amount_in_wei = int(amount * (10 ** decimals))
        print(f"🔢 Borrow {amount} {asset_symbol} = {amount_in_wei} (wei)")

        acct = pool_contract.functions.getUserAccountData(user_checksum).call()
        print(f"📊 Account data: {acct}")

        nonce = w3.eth.get_transaction_count(EXECUTOR_ADDRESS)

        # Dry run to capture revert reason
        debug_call(pool_contract.functions.borrow, asset_checksum, amount_in_wei, rate_mode, 0, user_checksum)

        try:
            gas_estimate = pool_contract.functions.borrow(asset_checksum, amount_in_wei, rate_mode, 0, user_checksum).estimate_gas({"from": EXECUTOR_ADDRESS})
        except Exception as e:
            print(f"⚠️ Gas estimate failed: {e}")
            gas_estimate = 400000

        print(f"⛽ Gas estimate: {gas_estimate}")

        borrow_tx = pool_contract.functions.borrow(asset_checksum, amount_in_wei, rate_mode, 0, user_checksum).build_transaction({
            "from": EXECUTOR_ADDRESS,
            "chainId": CHAIN_ID,
            "gas": gas_estimate,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
        })
        signed_tx = w3.eth.account.sign_transaction(borrow_tx, EXECUTOR_PRIVATE_KEY)
        tx_hash, receipt = _send_and_wait(signed_tx.raw_transaction)
        if receipt.status != 1:
            return {"status": "error", "message": "Borrow transaction reverted."}
        log_to_hedera(f"AAVE_BORROW: {user_address} borrowed {amount} {asset_symbol}. Tx: {tx_hash.hex()}")
        return {"status": "success", "message": "Borrow OK", "tx_hash": tx_hash.hex()}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": f"Borrow error: {e}"}

def execute_repay(user_address: str, asset_symbol: str, asset_address: str):
    print("\n🚀 Executing REPAY...")
    try:
        user_checksum = Web3.to_checksum_address(user_address)
        asset_checksum = Web3.to_checksum_address(asset_address)
        decimals = get_asset_decimals(asset_checksum)
        data = data_provider.functions.getUserReserveData(asset_checksum, user_checksum).call()
        print(f"📊 Reserve data: {data}")
        stable_debt = data[1]
        variable_debt = data[2]
        rate_mode = 1 if stable_debt > 0 else 2 if variable_debt > 0 else 0
        if rate_mode == 0:
            return {"status": "success", "message": "No active debt found to repay."}

        user_total_debt = stable_debt + variable_debt
        token_contract = w3.eth.contract(address=asset_checksum, abi=ERC20_ABI)
        executor_balance = token_contract.functions.balanceOf(EXECUTOR_ADDRESS).call()
        print(f"💰 Executor balance: {executor_balance / (10 ** decimals)} {asset_symbol}")
        amount_to_repay = min(user_total_debt, executor_balance)
        print(f"🔢 Repay amount: {amount_to_repay}")

        nonce = w3.eth.get_transaction_count(EXECUTOR_ADDRESS)
        nonce = _safe_approve_if_needed(token_contract, EXECUTOR_ADDRESS, pool_address, amount_to_repay, nonce)

        debug_call(pool_contract.functions.repay, asset_checksum, amount_to_repay, rate_mode, user_checksum)

        try:
            gas_estimate = pool_contract.functions.repay(asset_checksum, amount_to_repay, rate_mode, user_checksum).estimate_gas({"from": EXECUTOR_ADDRESS})
        except Exception as e:
            print(f"⚠️ Gas estimate failed: {e}")
            gas_estimate = 300000

        print(f"⛽ Gas estimate: {gas_estimate}")

        repay_tx = pool_contract.functions.repay(asset_checksum, amount_to_repay, rate_mode, user_checksum).build_transaction({
            "from": EXECUTOR_ADDRESS,
            "chainId": CHAIN_ID,
            "gas": gas_estimate,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
        })
        signed_tx = w3.eth.account.sign_transaction(repay_tx, EXECUTOR_PRIVATE_KEY)
        tx_hash, receipt = _send_and_wait(signed_tx.raw_transaction)
        if receipt.status != 1:
            return {"status": "error", "message": "Repay transaction reverted."}
        log_to_hedera(f"AAVE_REPAY: {user_address} repaid {asset_symbol}. Tx: {tx_hash.hex()}")
        return {"status": "success", "message": "Repay OK", "tx_hash": tx_hash.hex()}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": f"Repay error: {e}"}

def wrap_eth(amount_eth):
    weth_address = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
    weth = w3.eth.contract(address=weth_address, abi=[
        {"inputs": [], "name": "deposit", "outputs": [], "stateMutability": "payable", "type": "function"},
        {"inputs": [{"internalType": "uint256", "name": "wad", "type": "uint256"}], "name": "withdraw", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
    ])

    value = int(amount_eth * 10**18)
    nonce = w3.eth.get_transaction_count(EXECUTOR_ADDRESS)
    tx = weth.functions.deposit().build_transaction({
        "from": EXECUTOR_ADDRESS,
        "value": value,
        "nonce": nonce,
        "gas": 100000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })
    signed_tx = w3.eth.account.sign_transaction(tx, EXECUTOR_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"🔁 Wrapping {amount_eth} ETH into WETH... tx = {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ WETH wrap complete — status={receipt.status}")

# wrap_eth(1)

def check_balances(address):
    print(f"🔍 Checking balances for {address}")
    for symbol, token_addr in ASSET_REGISTRY.items():
        token = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
        bal = token.functions.balanceOf(Web3.to_checksum_address(address)).call()
        decimals = token.functions.decimals().call()
        print(f"{symbol}: {bal / (10 ** decimals)}")

check_balances("0x10c959Cf9994e95fc7354855c0f2Bd639E499179")

# --- 3. API DEFINITION ---
app = FastAPI(title="Aave Concierge API", version="7.0.0")

class HealthResponse(BaseModel):
    user_address: str
    health_factor: float

class TxRequestSymbol(BaseModel):
    user_address: str
    asset_symbol: str
    amount: float

class BorrowRequestSymbol(BaseModel):
    user_address: str
    asset_symbol: str
    amount: float
    interest_rate_mode: int = 2

class RepayRequestSymbol(BaseModel):
    user_address: str
    asset_symbol: str

class TxResponse(BaseModel):
    status: str
    message: str
    tx_hash: str | None = None

@app.get("/health/{user_address}", response_model=HealthResponse)
async def check_health(user_address: str):
    health = get_health_factor(user_address)
    return HealthResponse(user_address=user_address, health_factor=health)

@app.post("/supply", response_model=TxResponse)
async def supply(req: TxRequestSymbol):
    asset_address = ASSET_REGISTRY.get(req.asset_symbol.upper())
    if not asset_address:
        raise HTTPException(status_code=400, detail="Asset not found")
    result = execute_supply(req.user_address, req.asset_symbol, asset_address, req.amount)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.post("/borrow", response_model=TxResponse)
async def borrow(req: BorrowRequestSymbol):
    asset_address = ASSET_REGISTRY.get(req.asset_symbol.upper())
    if not asset_address:
        raise HTTPException(status_code=400, detail="Asset not found")
    result = execute_borrow(req.user_address, req.asset_symbol, asset_address, req.amount, req.interest_rate_mode)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.post("/repay", response_model=TxResponse)
async def repay(req: RepayRequestSymbol):
    asset_address = ASSET_REGISTRY.get(req.asset_symbol.upper())
    if not asset_address:
        raise HTTPException(status_code=400, detail="Asset not found")
    result = execute_repay(req.user_address, req.asset_symbol, asset_address)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result
