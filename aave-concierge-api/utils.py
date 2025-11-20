import asyncio
import aiohttp
from web3 import Web3
from contracts import get_pool_contract


async def log_to_hedera(msg: str):
    """Asynchronously log a message to Hedera Consensus Service."""
    try:
        from config import HEDERA_LOGGER_URL
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(HEDERA_LOGGER_URL, json={"log_message": msg}, timeout=5)
            except Exception as e:
                print("[WARN] Hedera log failed:", e)
    except ImportError:
        print("[WARN] Could not import HEDERA_LOGGER_URL, skipping logging")


def schedule_log(msg: str):
    """Schedule a log message to be sent to Hedera asynchronously."""
    try:
        asyncio.create_task(log_to_hedera(msg))
    except RuntimeError:
        # Fallback for when no event loop is running
        asyncio.run(log_to_hedera(msg))


def get_health_factor(pool, user):
    """Get the health factor for a user from the Aave pool contract."""
    try:
        data = pool.functions.getUserAccountData(user).call()
        return round(data[5] / 1e18 if data[5] else 100.0, 3)
    except Exception:
        return 100.0


def get_token_decimals(token_symbol: str, cfg=None) -> int:
    """Get the decimal places for a token based on its symbol."""
    # If config is provided, use dynamic decimals from config
    if cfg and token_symbol in cfg.get("assets", {}):
        return cfg["assets"][token_symbol].get("decimals", 18)

    # Fallback to hardcoded values for backward compatibility
    if token_symbol.startswith("USDC") or token_symbol.startswith("USDT"):
        return 6
    elif token_symbol == "WBTC":
        return 8
    elif token_symbol == "EURS":
        return 2
    else:
        return 18


def format_token_amount(amount_wei: int, token_symbol: str, cfg=None) -> float:
    """Convert token amount from wei to human-readable format."""
    decimals = get_token_decimals(token_symbol, cfg)
    return round(amount_wei / (10 ** decimals), 6)


def amount_to_wei(amount: float, token_symbol: str, cfg=None) -> int:
    """Convert human-readable token amount to wei."""
    decimals = get_token_decimals(token_symbol, cfg)
    return int(amount * 10 ** decimals)


def validate_user_address(address: str) -> str:
    """Validate and convert user address to checksum format."""
    return Web3.to_checksum_address(address)


def build_transaction(w3, user_address: str, chain_id: int, gas_limit: int = 300000,
                     to: str = None, data: str = "0x", value: int = 0) -> dict:
    """Build a basic transaction template for user to sign."""
    return {
        "from": user_address,
        "to": to,
        "nonce": w3.eth.get_transaction_count(user_address),
        "chainId": chain_id,
        "gas": gas_limit,
        "data": data,
        "value": value,
    }


def build_approval_transaction(w3, user_address: str, token_address: str,
                              spender_address: str, amount: int, chain_id: int) -> dict:
    """Build ERC20 approval transaction for user to sign."""
    # ERC20 approve function signature: approve(address,uint256)
    # Method ID: 0x095ea7b3
    # Parameters: spender (32 bytes), amount (32 bytes)
    method_id = "0x095ea7b3"
    spender_padded = spender_address[2:].zfill(64)  # Remove 0x and pad to 64 chars
    amount_padded = hex(amount)[2:].zfill(64)  # Convert to hex, remove 0x, pad to 64 chars
    data = method_id + spender_padded + amount_padded

    return build_transaction(
        w3=w3,
        user_address=user_address,
        chain_id=chain_id,
        to=token_address,
        data=data,
        gas_limit=50000  # Standard approval gas limit
    )


def estimate_gas_cost(w3, gas_limit: int) -> float:
    """Estimate gas cost in native token (ETH, MATIC, etc.)."""
    try:
        gas_price = w3.eth.gas_price
        gas_cost_wei = gas_limit * gas_price
        return float(w3.from_wei(gas_cost_wei, 'ether'))
    except Exception:
        return 0.0


def get_token_allowance(w3, token_address: str, owner_address: str, spender_address: str) -> int:
    """Get ERC20 token allowance."""
    try:
        # ERC20 allowance function signature
        allowance_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        token_contract = w3.eth.contract(address=token_address, abi=allowance_abi)
        return token_contract.functions.allowance(owner_address, spender_address).call()
    except Exception:
        return 0