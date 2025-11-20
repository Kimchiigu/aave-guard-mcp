import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# ENVIRONMENT SETUP
# ============================================================

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
EXECUTOR_PRIVATE_KEY = os.getenv("EXECUTOR_PRIVATE_KEY")
HEDERA_LOGGER_URL = os.getenv("HEDERA_LOGGER_URL", "http://localhost:3001/test-hedera")
DEFAULT_NETWORK = os.getenv("NETWORK", "base-sepolia").lower()

if not (ALCHEMY_API_KEY and EXECUTOR_PRIVATE_KEY):
    raise ValueError("Missing ALCHEMY_API_KEY or EXECUTOR_PRIVATE_KEY in .env")

# ============================================================
# NETWORK CONFIGURATIONS
# ============================================================

def load_network_configurations():
    """Load network configurations from JSON files."""
    network_config = {}

    # Get the directory of the current file to locate the JSON files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)

    # Load mainnet configurations
    mainnet_path = os.path.join(parent_dir, "aave-updater", "aave_addresses_mainnet.json")
    testnet_path = os.path.join(parent_dir, "aave-updater", "aave_addresses_testnet.json")

    try:
        # Load mainnet configurations
        with open(mainnet_path, "r") as f:
            mainnet_data = json.load(f)

        # Load testnet configurations
        with open(testnet_path, "r") as f:
            testnet_data = json.load(f)

        # Combine configurations
        all_data = {**mainnet_data, **testnet_data}

        # Process each network
        for network_name, network_data in all_data.items():
            # Skip if no ASSETS or POOL_ADDRESSES_PROVIDER
            if "ASSETS" not in network_data or "POOL_ADDRESSES_PROVIDER" not in network_data:
                continue

            # Extract chain ID and Protocol Data Provider
            chain_id = network_data.get("CHAIN_ID")
            pdp_address = network_data.get("AAVE_PROTOCOL_DATA_PROVIDER")

            # Build RPC URL based on chain_id
            if chain_id == 1:  # Ethereum Mainnet
                rpc = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 11155111:  # Ethereum Sepolia
                rpc = f"https://eth-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 84532:  # Base Sepolia
                rpc = f"https://base-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 8453:  # Base Mainnet
                rpc = f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 42161:  # Arbitrum Mainnet
                rpc = f"https://arb-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 421614:  # Arbitrum Sepolia
                rpc = f"https://arb-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 137:  # Polygon Mainnet
                rpc = f"https://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 80001:  # Polygon Mumbai -> Change to Amoy
                rpc = f"https://polygon-amoy.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 10:  # Optimism Mainnet
                rpc = f"https://opt-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 11155420:  # Optimism Sepolia
                rpc = f"https://opt-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 43114:  # Avalanche Mainnet
                rpc = f"https://avax-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 43113:  # Avalanche Fuji
                rpc = f"https://avax-fuji.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 534351:  # Scroll Sepolia
                rpc = f"https://scroll-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 534352:  # Scroll Mainnet
                rpc = f"https://scroll-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 56:  # BNB Chain (BSC)
                rpc = f"https://bnb-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 42220:  # Celo Mainnet
                rpc = f"https://celo-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 100:  # Gnosis Chain
                rpc = f"https://gnosis-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 1088:  # Metis Mainnet
                rpc = f"https://metis-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 146:  # Sonic Mainnet
                rpc = f"https://sonic-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 324:  # zkSync Mainnet
                rpc = f"https://zksync-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            elif chain_id == 59144:  # Linea Mainnet
                rpc = f"https://linea-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            else:
                # Default to Ethereum mainnet RPC for unknown chains
                rpc = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

            # Extract assets (map from symbol to complete asset data)
            assets = {}
            for symbol, asset_data in network_data["ASSETS"].items():
                if "UNDERLYING" in asset_data:
                    # Store complete asset data including A_TOKEN, V_TOKEN, and ORACLE
                    # Note: JSON uses "ORACLE" (uppercase), we store as lowercase for consistency
                    assets[symbol] = {
                        "underlying": asset_data["UNDERLYING"],
                        "a_token": asset_data.get("A_TOKEN"),
                        "v_token": asset_data.get("V_TOKEN"),
                        "oracle": asset_data.get("ORACLE"),  # Per-token oracle address from JSON
                        "decimals": asset_data.get("decimals", 18)  # Default to 18 decimals
                    }

            # Skip if no assets found
            if not assets:
                continue

            # Create normalized network name
            normalized_name = network_name.lower().replace("aavev3", "")

            # Handle special cases for network naming
            if normalized_name == "ethereum":
                normalized_name = "eth-mainnet"
            elif normalized_name == "ethereumhorizon":
                normalized_name = "eth-horizon"
            elif normalized_name == "ethereumetherfi":
                normalized_name = "eth-etherfi"
            elif normalized_name == "ethereumlido":
                normalized_name = "eth-lido"
            elif normalized_name == "arbitrum":
                normalized_name = "arbitrum-mainnet"
            elif normalized_name == "avalanche":
                normalized_name = "avalanche-mainnet"
            elif normalized_name == "optimism":
                normalized_name = "optimism-mainnet"
            elif normalized_name == "scroll":
                normalized_name = "scroll-mainnet"
            elif normalized_name == "fuji":
                normalized_name = "avalanche-fuji"

            # Handle sepolia naming
            if "sepolia" in normalized_name:
                if normalized_name == "sepolia":
                    normalized_name = "eth-sepolia"
                else:
                    normalized_name = normalized_name.replace("sepolia", "-sepolia")

            # Handle mainnet naming
            if normalized_name and not normalized_name.endswith("-mainnet") and not normalized_name.endswith("-sepolia"):
                if chain_id == 1:
                    normalized_name = normalized_name.replace("ethereum", "")
                    if not normalized_name:
                        normalized_name = "eth-mainnet"
                elif chain_id not in [1, 84532, 421614, 11155111, 42161, 11155420, 534351, 534352, 43113, 43114, 137, 10, 80001]:
                    # For chains that are not Ethereum or testnets, add mainnet
                    if not any(str(testnet_id) == str(chain_id) for testnet_id in [84532, 421614, 11155111, 11155420, 534351, 43113]):
                        normalized_name += "-mainnet"

            network_config[normalized_name] = {
                "chain_id": chain_id,
                "rpc": rpc,
                "pool_provider": network_data["POOL_ADDRESSES_PROVIDER"],
                "AAVE_PROTOCOL_DATA_PROVIDER": pdp_address,
                "assets": assets,
                "oracle": network_data.get("ORACLE"),  # Network-level oracle address
                "raw_network_name": network_name,
            }

    except FileNotFoundError as e:
        print(f"Warning: Could not load network configuration files: {e}")
        # Fallback to basic configuration
        return get_fallback_config()
    except json.JSONDecodeError as e:
        print(f"Error parsing network configuration JSON: {e}")
        return get_fallback_config()
    except Exception as e:
        print(f"Error loading network configurations: {e}")
        return get_fallback_config()

    return network_config

def get_fallback_config():
    """Fallback configuration in case JSON files can't be loaded."""
    return {
        "base-sepolia": {
            "chain_id": 84532,
            "rpc": f"https://base-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
            "pool_provider": "0xE4C23309117Aa30342BFaae6c95c6478e0A4Ad00",
            "AAVE_PROTOCOL_DATA_PROVIDER": "0xBc9f5b7E248451CdD7cA54e717a2BFe1F32b566b",
            "oracle": "0x943b0dE18d4abf4eF02A85912F8fc07684C141dF",
            "assets": {
                "USDC": {
                    "underlying": "0xba50cd2a20f6da35d788639e581bca8d0b5d4d5f",
                    "a_token": "0x10F1A9D11CDf50041f3f8cB7191CBE2f31750ACC",
                    "v_token": "0xFB3e85601b7fEb3691bbb8779Ef0E1069E347204",
                    "oracle": "0xd30e2101a97dcbAeBCBC04F14C3f624E67A35165",
                    "decimals": 6
                },
                "WETH": {
                    "underlying": "0x4200000000000000000000000000000000000006",
                    "a_token": "0x73a5bB60b0B0fc35710DDc0ea9c407031E31Bdbb",
                    "v_token": "0x562abf6562d6A2b165aDa02b5946bc3E7b4dD653",
                    "oracle": "0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1",
                    "decimals": 18
                },
                "USDT": {
                    "underlying": "0x0a215D8ba66387DCA84B284D18c3B4ec3de6E54a",
                    "a_token": "0xcE3CAae5Ed17A7AafCEEbc897DE843fA6CC0c018",
                    "v_token": "0xE3C742c88EE6A610157C16b60bBDD62351daeE39",
                    "oracle": "0x3ec8593F930EA45ea58c968260e6e9FF53FC934f",
                    "decimals": 6
                },
                "WBTC": {
                    "underlying": "0x54114591963CF60EF3aA63bEfD6eC263D98145a4",
                    "a_token": "0x47Db195BAf46898302C06c31bCF46c01C64ACcF9",
                    "v_token": "0x638291B5Ccb9fEd339FdD351Eb086e607fCA9561",
                    "oracle": "0x0FB99723Aee6f420beAD13e6bBB79b7E6F034298",
                    "decimals": 8
                },
                "cbETH": {
                    "underlying": "0xD171b9694f7A2597Ed006D41f7509aaD4B485c4B",
                    "a_token": "0x9Fd6d1DBAd7c052e0c43f46df36eEc6a68814B63",
                    "v_token": "0xa1a483652b157FF006292CDb0e9EB7FFad2a5142",
                    "oracle": "0x3c65e28D357a37589e1C7C86044a9f44dDC17134",
                    "decimals": 18
                },
                "LINK": {
                    "underlying": "0x810D46F9a9027E28F9B01F75E2bdde839dA61115",
                    "a_token": "0x0aD46dE765522399d7b25B438b230A894d72272B",
                    "v_token": "0xBA42C6752F347e3c22DD0A4e5578dCB0137C1325",
                    "oracle": "0xb113F5A928BCfB189C998ab20d753a47F9dE5A61",
                    "decimals": 18
                },
            },
        },
        "eth-sepolia": {
            "chain_id": 11155111,
            "rpc": f"https://eth-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
            "pool_provider": "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A",
            "AAVE_PROTOCOL_DATA_PROVIDER": "0x3e9708d80f7B3e43118013075F7e95CE3AB31F31",
            "oracle": "0x2da88497588bf89281816106C7259e31AF45a663",
            "assets": {
                "WBTC": {
                    "underlying": "0x29f2D40B0605204364af54EC677bD022DA425d03",
                    "a_token": "0x1804Bf30507dc2EB3bDEbbbdd859991EAeF6EefF",
                    "v_token": "0xEB016dFd303F19fbDdFb6300eB4AeB2DA7Ceac37",
                    "decimals": 8
                },
                "GHO": {
                    "underlying": "0xc4bF5CbDaBE595361438F8c6a187bDc330539c60",
                    "a_token": "0xd190eF37dB51Bb955A680fF1A85763CC72d083D4",
                    "v_token": "0x67ae46EF043F7A4508BD1d6B94DB6c33F0915844",
                    "decimals": 18
                },
                "LINK": {
                    "underlying": "0xf8Fb3713D459D7C1018BD0A49D19b4C44290EBE5",
                    "a_token": "0x3FfAf50D4F4E96eB78f2407c090b72e86eCaed24",
                    "v_token": "0x34a4d932E722b9dFb492B9D8131127690CE2430B",
                    "decimals": 18
                },
                "DAI": {
                    "underlying": "0xFF34B3d4Aee8ddCd6F9AFFFB6Fe49bD371b8a357",
                    "a_token": "0x29598b72eb5CeBd806C5dCD549490FdA35B13cD8",
                    "v_token": "0x22675C506A8FC26447aFFfa33640f6af5d4D4cF0",
                    "decimals": 18
                },
                "USDT": {
                    "underlying": "0xaA8E23Fb1079EA71e0a56F48a2aa51851D8433D0",
                    "a_token": "0xAF0F6e8b0Dc5c913bbF4d14c22B4E78Dd14310B6",
                    "v_token": "0x9844386d29EEd970B9F6a2B9a676083b0478210e",
                    "decimals": 6
                },
                "USDC": {
                    "underlying": "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8",
                    "a_token": "0x16dA4541aD1807f4443d92D26044C1147406EB80",
                    "v_token": "0x36B5dE936eF1710E1d22EabE5231b28581a92ECc",
                    "decimals": 6
                },
                "AAVE": {
                    "underlying": "0x88541670E55cC00bEEFD87eB59EDd1b7C511AC9a",
                    "a_token": "0x6b8558764d3b7572136F17174Cb9aB1DDc7E1259",
                    "v_token": "0xf12fdFc4c631F6D361b48723c2F2800b84B519e6",
                    "decimals": 18
                },
                "WETH": {
                    "underlying": "0xC558DBdd856501fcd9aaF1E62eae57A9F0629a3c",
                    "a_token": "0x5b071b590a59395fE4025A0Ccc1FcC931AAc1830",
                    "v_token": "0x22a35DB253f4F6D0029025D6312A3BdAb20C2c6A",
                    "decimals": 18
                },
                "EURS": {
                    "underlying": "0x6d906e526a4e2ca02097ba9d0caA3c382f52278E",
                    "a_token": "0xB20691021F9AcED8631eDaa3c0Cd2949EB45662D",
                    "v_token": "0x94482C7A7477196259D8a0f74fB853277Fa5a75b",
                    "decimals": 2
                },
            },
        },
    }

# Load network configurations
NETWORK_CONFIG = load_network_configurations()

# Normalize addresses to checksum format
for net in NETWORK_CONFIG.values():
    # Handle the new asset structure with underlying, a_token, and v_token
    normalized_assets = {}
    for symbol, asset_data in net["assets"].items():
        if isinstance(asset_data, dict):
            # New structure with complete asset data
            normalized_assets[symbol] = {
                "underlying": Web3.to_checksum_address(asset_data["underlying"]),
                "a_token": Web3.to_checksum_address(asset_data["a_token"]) if asset_data.get("a_token") else None,
                "v_token": Web3.to_checksum_address(asset_data["v_token"]) if asset_data.get("v_token") else None,
                "decimals": asset_data.get("decimals", 18)
            }
        else:
            # Legacy structure (just underlying address)
            normalized_assets[symbol] = {
                "underlying": Web3.to_checksum_address(asset_data),
                "a_token": None,
                "v_token": None,
                "decimals": 18
            }
    net["assets"] = normalized_assets

    if "pool_provider" in net:
        net["pool_provider"] = Web3.to_checksum_address(net["pool_provider"])