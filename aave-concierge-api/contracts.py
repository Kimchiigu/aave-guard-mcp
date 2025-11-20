from web3 import Web3
from config import NETWORK_CONFIG

def get_network_config(name: str):
    """Get network configuration by name."""
    key = name.lower().replace(" ", "-")
    if key not in NETWORK_CONFIG:
        from fastapi import HTTPException
        raise HTTPException(400, f"Unsupported network: {name}")
    return NETWORK_CONFIG[key]


def init_web3(network_name: str, with_executor: bool = False):
    """Initialize Web3 connection for a given network."""
    cfg = get_network_config(network_name)
    w3 = Web3(Web3.HTTPProvider(cfg["rpc"]))

    if with_executor:
        from config import EXECUTOR_PRIVATE_KEY
        executor = w3.eth.account.from_key(EXECUTOR_PRIVATE_KEY)
        return w3, executor, cfg
    else:
        return w3, None, cfg


def get_pool_contract_with_abi(w3):
    """Get the Aave pool contract instance with full ABI for transaction building."""
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
    return pool_abi


def get_pool_address(w3, provider_addr):
    """Get the Aave pool address from the provider."""
    provider_abi = [
        {"inputs": [], "name": "getPool", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    ]
    provider = w3.eth.contract(address=provider_addr, abi=provider_abi)
    return provider.functions.getPool().call()


def get_pool_contract(w3, provider_addr):
    """Get the Aave pool contract instance."""
    pool_addr = get_pool_address(w3, provider_addr)
    pool_abi = get_pool_contract_with_abi(w3)
    return w3.eth.contract(address=pool_addr, abi=pool_abi)


def build_pool_transaction(w3, provider_addr, function_name: str, *args):
    """Build transaction data for pool contract function."""
    pool_addr = get_pool_address(w3, provider_addr)
    pool_abi = get_pool_contract_with_abi(w3)
    pool_contract = w3.eth.contract(address=pool_addr, abi=pool_abi)

    # Get the function and build transaction data
    function = getattr(pool_contract.functions, function_name)

    # Build transaction with minimal parameters to get correct data
    tx_data = function(*args).build_transaction({
        'from': args[-1] if function_name in ['supply', 'borrow', 'repay'] else None,  # User address is last arg
        'gas': 0,  # Will be estimated later
        'gasPrice': 0,
        'nonce': 0,
        'chainId': None
    })

    # Set the correct to address
    tx_data['to'] = pool_addr
    return tx_data


def get_token_contract(w3, token_addr):
    """Get ERC20 token contract instance for balance queries."""
    token_abi = [
        {
            "name": "balanceOf",
            "inputs": [{"type": "address"}],
            "outputs": [{"type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    return w3.eth.contract(address=token_addr, abi=token_abi)