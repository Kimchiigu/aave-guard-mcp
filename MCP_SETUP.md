# Aave Guard MCP Integration Guide

## Overview

Your Aave Guard API is successfully deployed and fully MCP-compliant! The API is available at `https://aave-guard-mcp.vercel.app` and includes:

- ✅ MCP Discovery Endpoint (`/mcp`)
- ✅ Health Check (`/health/{user_address}`)
- ✅ Repay Debt (`/repay`)
- ✅ Supply Asset (`/supply`)
- ✅ Borrow Asset (`/borrow`)

## Current Status

The API is **fully functional** and tested:

- Health factor for `0x...`: **12.73** (Safe!)
- MCP discovery endpoint returns proper tool definitions
- All endpoints are working as expected

## Available Tools

### 1. check_aave_health
- **Description**: Checks the Aave V3 health factor for a user's loan position
- **Parameters**: `user_address` (string)
- **Method**: GET `/health/{user_address}`
- **Returns**: Health factor (below 1.0 = liquidation risk)

### 2. repay_aave_debt
- **Description**: Repays a user's debt using executor wallet funds
- **Parameters**: `user_address` (string), `asset_symbol` (string)
- **Method**: POST `/repay`
- **Assets**: USDC, WETH

### 3. supply_aave_asset
- **Description**: Supplies assets to Aave on behalf of a user
- **Parameters**: `user_address`, `asset_symbol`, `amount`
- **Method**: POST `/supply`
- **Assets**: USDC, WETH

### 4. borrow_aave_asset
- **Description**: Borrows assets from Aave for a user
- **Parameters**: `user_address`, `asset_symbol`, `amount`, `interest_rate_mode`
- **Method**: POST `/borrow`
- **Assets**: USDC, WETH
- **Rate Modes**: 1 (Stable), 2 (Variable)

## Integration Examples

### Direct API Usage

```python
import requests

# Health check
response = requests.get("https://aave-guard-mcp.vercel.app/health/0x..")
health_factor = response.json()["health_factor"]

# Repay debt
response = requests.post("https://aave-guard-mcp.vercel.app/repay", json={
    "user_address": "0x...",
    "asset_symbol": "USDC"
})
```

### MCP Discovery

```python
response = requests.get("https://aave-guard-mcp.vercel.app/mcp")
tools = response.json()
```

## Security Configuration

Your API is configured with:
- Alchemy API integration for Base Sepolia testnet
- Private key secured via environment variables
- Web3 contract interactions with proper error handling
- Transaction signing and receipt verification

## Next Steps

Your MCP integration is complete! The API is:
1. ✅ Deployed on Vercel
2. ✅ MCP-compliant with discovery endpoint
3. ✅ Tested and functional
4. ✅ Ready for AI agent integration

The service can now be used by any MCP-compatible AI system to interact with Aave V3 on Base Sepolia.