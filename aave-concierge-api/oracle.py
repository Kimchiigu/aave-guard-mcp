"""
Aave Oracle Integration Module
Provides real-time price feeds and asset data from Aave's oracle contracts
"""

from web3 import Web3
from contracts import init_web3


def get_token_price_oracle(w3: Web3, token_address: str, oracle_address: str) -> float:
    """
    Get real-time token price from Aave's price oracle

    Args:
        w3: Web3 instance
        token_address: The underlying token contract address
        oracle_address: The Aave oracle contract address

    Returns:
        Token price in USD (human-readable)
    """
    try:
        # AaveOracle ABI for getting asset prices
        oracle_abi = [
            {
                "constant": True,
                "inputs": [{"name": "asset", "type": "address"}],
                "name": "getAssetPrice",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "asset", "type": "address"}],
                "name": "getSourceOfAsset",
                "outputs": [{"name": "", "type": "address"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]

        oracle_contract = w3.eth.contract(address=oracle_address, abi=oracle_abi)

        # Get price from oracle (returns price in base currency, usually 1e8 precision)
        price_raw = oracle_contract.functions.getAssetPrice(token_address).call()

        # Debug: Log the raw price and oracle info
        print(f"[DEBUG] Oracle {oracle_address} price for {token_address}: {price_raw}")

        # Aave prices are typically in base currency with 8 decimals for USD
        # So we divide by 1e8 to get the USD price
        price_usd = price_raw / 1e8

        # Additional validation: price should be reasonable
        if price_usd <= 0 or price_usd > 1000000:  # Sanity check: price between $0 and $1M
            print(f"[WARN] Unreasonable price detected: ${price_usd} for {token_address}")
            return 0.0

        print(f"[DEBUG] Converted price: ${price_usd:.6f} for {token_address}")
        return float(price_usd)

    except Exception as e:
        print(f"[WARN] Failed to get oracle price for {token_address}: {e}")
        return 0.0


def get_protocol_data_provider(w3: Web3, pdp_address: str) -> dict:
    """
    Get real-time asset data from Aave's Protocol Data Provider

    Args:
        w3: Web3 instance
        pdp_address: Protocol Data Provider contract address

    Returns:
        Dictionary containing real-time asset configuration data
    """
    try:
        # AaveProtocolDataProvider ABI (simplified)
        pdp_abi = [
            {
                "constant": True,
                "inputs": [{"name": "asset", "type": "address"}],
                "name": "getReserveConfigurationData",
                "outputs": [
                    {"name": "decimals", "type": "uint256"},
                    {"name": "ltv", "type": "uint256"},
                    {"name": "liquidationThreshold", "type": "uint256"},
                    {"name": "liquidationBonus", "type": "uint256"},
                    {"name": "reserveFactor", "type": "uint256"},
                    {"name": "usageAsCollateralEnabled", "type": "bool"},
                    {"name": "borrowingEnabled", "type": "bool"},
                    {"name": "stableBorrowRateEnabled", "type": "bool"},
                    {"name": "isActive", "type": "bool"},
                    {"name": "isFrozen", "type": "bool"}
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "getAllATokens",
                "outputs": [{"name": "", "type": "address[]"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]

        pdp_contract = w3.eth.contract(address=pdp_address, abi=pdp_abi)

        return {
            "contract": pdp_contract,
            "abi": pdp_abi
        }

    except Exception as e:
        print(f"[WARN] Failed to initialize Protocol Data Provider: {e}")
        return None


def get_asset_real_time_data(w3: Web3, pdp_contract, token_address: str) -> dict:
    """
    Get real-time asset configuration data including liquidation threshold

    Args:
        w3: Web3 instance
        pdp_contract: Protocol Data Provider contract instance
        token_address: The token contract address

    Returns:
        Dictionary with asset configuration data
    """
    try:
        config_data = pdp_contract.functions.getReserveConfigurationData(token_address).call()

        # Debug: Print the raw config data to understand the format
        print(f"[DEBUG] Raw config data for {token_address}: {config_data}")

        ltv = config_data[1] / 10000  # Convert from basis points to decimal (e.g., 7500 -> 0.75)
        liquidation_threshold = config_data[2] / 10000  # Convert from basis points

        print(f"[DEBUG] Processed data for {token_address}: LTV={ltv:.2%}, LT={liquidation_threshold:.2%}")

        return {
            "decimals": config_data[0],
            "ltv": ltv,
            "liquidation_threshold": liquidation_threshold,
            "liquidation_bonus": config_data[3] / 10000,
            "reserve_factor": config_data[4] / 10000,
            "usage_as_collateral": config_data[5],
            "borrowing_enabled": config_data[6],
            "stable_borrow_enabled": config_data[7],
            "is_active": config_data[8],
            "is_frozen": config_data[9]
        }

    except Exception as e:
        print(f"[WARN] Failed to get asset configuration for {token_address}: {e}")
        return None


def get_all_real_time_asset_data(network: str, cfg: dict) -> dict:
    """
    Get real-time data for all assets in the configuration

    Args:
        network: Network name (e.g., 'base-sepolia')
        cfg: Network configuration dictionary

    Returns:
        Dictionary containing real-time prices and liquidation thresholds for all assets
    """
    try:
        w3, _, _ = init_web3(network)

        # Get Protocol Data Provider
        pdp_address = cfg.get("AAVE_PROTOCOL_DATA_PROVIDER")
        if not pdp_address:
            print(f"[WARN] No Protocol Data Provider found for {network}")
            return {}

        pdp_data = get_protocol_data_provider(w3, pdp_address)
        if not pdp_data:
            return {}

        real_time_data = {}

        for token_symbol, asset_data in cfg["assets"].items():
            token_address = asset_data["underlying"]
            oracle_address = asset_data.get("oracle")

            if not oracle_address:
                print(f"[DEBUG] No per-token oracle found for {token_symbol}, checking network-level oracle")
                # Fall back to network-level oracle if available
                network_oracle = cfg.get("oracle")
                if network_oracle:
                    oracle_address = network_oracle
                    print(f"[DEBUG] Using network-level oracle: {oracle_address} for {token_symbol}")
                else:
                    print(f"[WARN] No oracle address found for {token_symbol}")
                    continue

            # Get real-time price
            price = get_token_price_oracle(w3, token_address, oracle_address)

            # Get real-time asset configuration
            asset_config = get_asset_real_time_data(w3, pdp_data["contract"], token_address)

            real_time_data[token_symbol] = {
                "price": price,
                "liquidation_threshold": asset_config["liquidation_threshold"] if asset_config else 0.80,
                "ltv": asset_config["ltv"] if asset_config else 0.0,
                "is_active": asset_config["is_active"] if asset_config else True,
                "borrowing_enabled": asset_config["borrowing_enabled"] if asset_config else True,
                "oracle_address": oracle_address  # Store oracle address for debugging
            }

            print(f"[DEBUG] Real-time data for {token_symbol}: ${price:.2f}, LT: {real_time_data[token_symbol]['liquidation_threshold']:.2%} (Oracle: {oracle_address[:10]}...)")

        return real_time_data

    except Exception as e:
        print(f"[ERROR] Failed to get real-time asset data: {e}")
        return {}


def get_real_time_token_price(network: str, token_symbol: str, cfg: dict) -> float:
    """
    Get real-time price for a specific token

    Args:
        network: Network name
        token_symbol: Token symbol (e.g., 'USDC')
        cfg: Network configuration

    Returns:
        Token price in USD
    """
    try:
        w3, _, _ = init_web3(network)

        if token_symbol not in cfg["assets"]:
            print(f"[WARN] Token {token_symbol} not found in network configuration")
            return get_fallback_price(token_symbol)

        asset_data = cfg["assets"][token_symbol]
        token_address = asset_data["underlying"]
        oracle_address = asset_data.get("oracle")

        if not oracle_address:
            print(f"[DEBUG] No per-token oracle for {token_symbol}, checking network-level oracle...")
            # Fall back to network-level oracle if available
            network_oracle = cfg.get("oracle")
            if network_oracle:
                oracle_address = network_oracle
                print(f"[DEBUG] Using network-level oracle: {oracle_address} for {token_symbol}")
            else:
                print(f"[WARN] No oracle for {token_symbol}, using fallback price")
                return get_fallback_price(token_symbol)
        else:
            print(f"[DEBUG] Using per-token oracle: {oracle_address} for {token_symbol}")

        return get_token_price_oracle(w3, token_address, oracle_address)

    except Exception as e:
        print(f"[ERROR] Failed to get real-time price for {token_symbol}: {e}")
        return get_fallback_price(token_symbol)


def get_real_time_liquidation_threshold(network: str, token_symbol: str, cfg: dict) -> float:
    """
    Get real-time liquidation threshold for a specific token

    Args:
        network: Network name
        token_symbol: Token symbol
        cfg: Network configuration

    Returns:
        Liquidation threshold as decimal (e.g., 0.85 for 85%)
    """
    try:
        w3, _, _ = init_web3(network)

        pdp_address = cfg.get("AAVE_PROTOCOL_DATA_PROVIDER")
        if not pdp_address:
            print(f"[DEBUG] No Protocol Data Provider found for {network}, using fallback LT for {token_symbol}")
            return get_fallback_liquidation_threshold(token_symbol)

        pdp_data = get_protocol_data_provider(w3, pdp_address)
        if not pdp_data:
            print(f"[DEBUG] Could not initialize Protocol Data Provider, using fallback LT for {token_symbol}")
            return get_fallback_liquidation_threshold(token_symbol)

        token_address = cfg["assets"][token_symbol]["underlying"]
        asset_config = get_asset_real_time_data(w3, pdp_data["contract"], token_address)

        lt = asset_config["liquidation_threshold"] if asset_config else get_fallback_liquidation_threshold(token_symbol)
        print(f"[DEBUG] Real-time LT for {token_symbol}: {lt:.2%}")

        return lt

    except Exception as e:
        print(f"[ERROR] Failed to get real-time liquidation threshold for {token_symbol}: {e}")
        return get_fallback_liquidation_threshold(token_symbol)


def get_fallback_price(token_symbol: str) -> float:
    """Fallback prices when oracle is unavailable"""
    fallback_prices = {
        "USDC": 1.0,
        "USDT": 1.0,
        "DAI": 1.0,
        "WETH": 2000.0,
        "WBTC": 50000.0,
        "LINK": 15.0,
        "cbETH": 3000.0,
    }
    return fallback_prices.get(token_symbol, 1.0)


def get_fallback_liquidation_threshold(token_symbol: str) -> float:
    """Fallback liquidation thresholds when oracle is unavailable"""
    fallback_thresholds = {
        "USDC": 0.90,
        "USDT": 0.90,
        "DAI": 0.90,
        "WETH": 0.85,
        "WBTC": 0.85,
        "LINK": 0.80,
        "cbETH": 0.85,
    }
    return fallback_thresholds.get(token_symbol, 0.80)