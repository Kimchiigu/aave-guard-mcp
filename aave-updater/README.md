# Guide for Updating Aave Addresses

So for context, for the MCP AI to work, it needs a list of addresses covering the pool address provider (Ethereum, Base, etc) and reserves addresses (USDC, USDT, etc) for each networks. 

1. Run `update-addresses.ts` file
```bash
npx ts-node update-addresses.ts
```

2. See the outputted addresses file in `json` format
```bash
aave-updater/aave_addresses_all.json // include all mainnet and testnet addresses
aave-updater/aave_addresses_mainnet.json // include only mainnet addresses
aave-updater/aave_addresses_testnet.json // include only testnet addresses
```

The outputted `json` file will be used in the aave-concierge-api folder especially the `main.py` so the MCP/AI can execute actions (health, repay, borrow, supply)