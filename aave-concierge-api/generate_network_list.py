#!/usr/bin/env python3
"""
Script to generate a list of all available networks from the Aave configuration.
"""

import sys
import os
from datetime import datetime

# Add current directory to path to import config
sys.path.append('.')

try:
    from config import NETWORK_CONFIG

    def generate_network_list():
        """Generate a formatted list of all available networks."""

        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"network_list_{timestamp}.txt"

        # Sort networks by chain ID for better organization
        sorted_networks = sorted(NETWORK_CONFIG.items(), key=lambda x: x[1]['chain_id'])

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("AAVE GUARD MCP - AVAILABLE NETWORKS\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Networks: {len(NETWORK_CONFIG)}\n\n")

            # Group by type (mainnet vs testnet)
            mainnets = []
            testnets = []

            for name, config in sorted_networks:
                chain_id = config['chain_id']
                network_info = {
                    'name': name,
                    'chain_id': chain_id,
                    'assets': len(config['assets']),
                    'pool_provider': config['pool_provider']
                }

                # Testnets typically have higher chain IDs or specific patterns
                if any(testnet_pattern in name.lower() for testnet_pattern in ['sepolia', 'testnet', 'fuji']) or chain_id in [11155111, 84532, 421614, 11155420, 534351, 43113]:
                    testnets.append(network_info)
                else:
                    mainnets.append(network_info)

            # Write mainnets
            f.write("MAINNETS\n")
            f.write("-" * 20 + "\n")
            for net in mainnets:
                f.write(f"{net['name']:<25} | Chain ID: {net['chain_id']:<10} | Assets: {net['assets']:<3}\n")

            f.write(f"\nTOTAL MAINNETS: {len(mainnets)}\n\n")

            # Write testnets
            f.write("TESTNETS\n")
            f.write("-" * 20 + "\n")
            for net in testnets:
                f.write(f"{net['name']:<25} | Chain ID: {net['chain_id']:<10} | Assets: {net['assets']:<3}\n")

            f.write(f"\nTOTAL TESTNETS: {len(testnets)}\n\n")

            # Detailed breakdown
            f.write("DETAILED BREAKDOWN\n")
            f.write("=" * 50 + "\n")

            for name, config in sorted_networks:
                f.write(f"\nNetwork: {name}\n")
                f.write(f"  Chain ID: {config['chain_id']}\n")
                f.write(f"  Pool Provider: {config['pool_provider']}\n")
                f.write(f"  RPC URL: {config['rpc'][:80]}...\n")
                f.write(f"  Assets ({len(config['assets'])}):\n")

                # List first 10 assets, then show count if more
                assets = list(config['assets'].keys())
                shown_assets = assets[:10]
                for asset in shown_assets:
                    f.write(f"    - {asset}\n")

                if len(assets) > 10:
                    f.write(f"    ... and {len(assets) - 10} more assets\n")

            f.write(f"\n" + "=" * 50 + "\n")
            f.write("END OF REPORT\n")

        return output_file

    if __name__ == "__main__":
        try:
            output_file = generate_network_list()
            print(f"[SUCCESS] Network list saved to: {output_file}")
            print(f"[INFO] Total networks: {len(NETWORK_CONFIG)}")

        except Exception as e:
            print(f"[ERROR] Error: {e}")
            import traceback
            traceback.print_exc()

except ImportError as e:
    print(f"[ERROR] Could not import config module: {e}")
    print("Make sure you're running this from the aave-concierge-api directory")
    print("and that all dependencies are installed: pip install -r requirements.txt")