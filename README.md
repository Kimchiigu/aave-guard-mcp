# Aave Concierge API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0-green.svg)](https://fastapi.tiangolo.com)
[![Node.js 16+](https://img.shields.io/badge/node-16%2B-green.svg)](https://nodejs.org/)
[![Hedera HCS](https://img.shields.io/badge/Hedera-HCS-blueviolet.svg)](https://www.hedera.com/)
[![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black.svg)](https://vercel.com/)

# LoanGuardian - Aave Concierge API & Hedera Logger

## 🚀 Project Overview

**Aave Concierge API** is an MCP-compliant API that lets AI agents like Aya's manage Aave loans, supplies, and borrows using simple natural language commands.

### Project Description
**LoanGuardian** is a comprehensive DeFi platform that combines Aave protocol integration with decentralized consensus logging. The project consists of two complementary APIs:

**Aave Concierge API:** DeFi protocols like Aave are powerful but their complexity creates a barrier for AI agents. The Aave Concierge API solves this by acting as a simple, intelligent bridge.

Our serverless API, built with Python and FastAPI, exposes a suite of clean endpoints (/health, /supply, /borrow, /repay) that are fully compliant with the Model Context Protocol (MCP). This allows an AI agent, such as the one in Aya Wallet, to discover and use these tools to execute on-chain transactions based on a user's natural language commands.

**Hedera Consensus Logger API:** To ensure transparency and immutability, we've implemented a decentralized logging service using Hedera Hashgraph Consensus Service (HCS). This API provides immutable audit trails for all transactions, creating a trustworthy record that can be verified by anyone on the Hedera network.

For this hackathon, both APIs are deployed on Vercel - the Aave API operates on the Base Sepolia testnet, while the Hedera Logger runs on Hedera Testnet, providing a complete solution with decentralized consensus features.

## 📋 Features

### Aave Concierge API
A comprehensive MCP-compliant API for Aave V3 protocol interaction with built-in safety features:

- **GET /health/{network}/{user}**: Real-time health factor monitoring with borrowing safety assessment
- **POST /supply**: Secure asset supplying with automatic transaction logging to Hedera HCS
- **POST /borrow**: Intelligent borrowing with automatic health factor checks and liquidation protection
- **POST /repay**: Safe debt repayment with executor wallet management
- **GET /balance/{network}/{user}**: Multi-token balance checking across supported networks
- **POST /simulate**: Risk-free transaction simulation to preview health factor impacts
- **Built-in Safety Features**: Automatic health factor monitoring, gas optimization, and transaction failure handling
- **Multi-Network Support**: Currently supports Base Sepolia and ETH Sepolia testnets
- **AI Agent Ready**: Full MCP compliance with comprehensive manifest for AI integration

### Hedera Consensus Logger API
A decentralized logging service that provides immutable audit trails using Hedera Hashgraph Consensus Service (HCS):

- **POST /api/log**: Submits log messages to Hedera HCS for decentralized consensus
- Immutable transaction logging with sequence numbers
- Serverless architecture with Node.js/TypeScript
- Graceful failure handling that doesn't block main API operations

## 👥 Team Information

**Team Name:** LoanGuardian

**Primary Contact (Team Lead):**
- **Name:** Christopher Hardy Gunawan
- **Email:** christopher.hygunawan@gmail.com
- **Telegram:** [@kimchiigu](https://t.me/kimchiigu)
- **X/Twitter:** [@Kimchiigu73](https://twitter.com/Kimchiigu73)

**Team Members:** 1

## 🛠️ Installation and Setup

### Prerequisites
- Python 3.8+ (for Aave API)
- Node.js 16+ (for Hedera Logger API)
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Kimchiigu/aave-guard-mcp.git
cd aave-guard-mcp
```

### Step 2: Aave Concierge API Setup

#### 2.1 Create Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 2.2 Install Dependencies
```bash
cd aave-concierge-api
pip install -r requirements.txt
```

#### 2.3 Environment Variables for Aave API
Create a file named `.env` in the `aave-concierge-api` directory:

```env
ALCHEMY_API_KEY="your_alchemy_api_key_for_base_sepolia"
EXECUTOR_PRIVATE_KEY="your_secure_executor_wallet_private_key"
AAVE_POOL_ADDRESS_PROVIDER_V3_BASE_SEPOLIA="0xE4C23309117Aa30342BFaae6c95c6478e0A4Ad00"
HEDERA_LOGGER_URL="https://your-hedera-api-url.vercel.app/api/log"
NETWORK="base-sepolia"
```

#### 2.4 Run the Aave API Locally
```bash
uvicorn main:app --reload
```

### Step 3: Hedera Logger API Setup

#### 3.1 Install Dependencies
```bash
cd hedera-logger-api
npm install
```

#### 3.2 Create Hedera Topic
```bash
node create_topic.js
```
This will create a new HCS topic and provide you with a Topic ID.

#### 3.3 Environment Variables for Hedera API
Create a file named `.env` in the `hedera-logger-api` directory:

```env
HEDERA_ACCOUNT_ID="your_hedera_account_id"
HEDERA_PRIVATE_KEY="your_hedera_private_key"
HEDERA_TOPIC_ID="topic_id_from_create_topic_script"
```

### API Documentation
- **Aave API Docs:** http://127.0.0.1:8000/docs
- **Aave Alternative Docs:** http://127.0.0.1:8000/redoc
- **Hedera Logger Endpoint:** POST /api/log

## 🚀 Deployment

### Vercel Deployment
Both APIs are designed to be deployed as serverless functions on Vercel.

#### Aave Concierge API Deployment
1. **Create vercel.json in aave-concierge-api:**
```json
{
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

#### Hedera Logger API Deployment
1. **Create vercel.json in hedera-logger-api:**
```json
{
  "builds": [
    {
      "src": "api/log.ts",
      "use": "@vercel/node"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/log.ts"
    }
  ]
}
```

2. **Deploy Both APIs:**
   - Connect your GitHub repository to Vercel
   - Deploy each API as separate projects or use monorepo setup
   - Add environment variables in Vercel project settings for each API

**Live Instances:**
- **Aave Concierge API:** https://aave-guard-mcp.vercel.app/
- **Hedera Logger API:** Deployed separately (URL depends on your Vercel setup)

## 🤖 AI Agent Integration

### MCP (Model Context Protocol) Integration
The project includes a comprehensive MCP manifest file (`mcp-manifest.json`) that describes the API's capabilities in a machine-readable format that AI agents can understand.

**Built-in Features:**
- **Automatic Hedera Logging**: All Aave transactions automatically log to Hedera HCS via the `schedule_log()` function
- **Multi-Network Support**: Built-in support for Base Sepolia and ETH Sepolia testnets
- **Health Factor Safety**: Automatic health factor checks before borrowing operations
- **Simulation Mode**: Dry-run simulations for safe testing without real transactions

**MCP Methods Available:**
- `supply`: Supply tokens to Aave
- `borrow`: Borrow tokens with safety checks
- `repay`: Repay borrowed tokens
- `health`: Check user health factor
- `balance`: Get token balances
- `simulate`: Simulate transactions without execution

## 📖 Usage Examples

### Aave Concierge API Examples

#### Check User Health
```bash
curl -X GET "https://aave-guard-mcp.vercel.app/health/base-sepolia/0x123...abc"
```

#### Supply Assets
```bash
curl -X POST "https://aave-guard-mcp.vercel.app/supply" \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x123...abc", "token": "USDC", "amount": 1000, "network": "base-sepolia"}'
```

#### Borrow Assets
```bash
curl -X POST "https://aave-guard-mcp.vercel.app/borrow" \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x123...abc", "token": "USDC", "amount": 500, "network": "base-sepolia"}'
```

#### Repay Debt
```bash
curl -X POST "https://aave-guard-mcp.vercel.app/repay" \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x123...abc", "token": "USDC", "amount": 250, "network": "base-sepolia"}'
```

#### Get Token Balances
```bash
curl -X GET "https://aave-guard-mcp.vercel.app/balance/base-sepolia/0x123...abc"
```

#### Simulate Transaction
```bash
curl -X POST "https://aave-guard-mcp.vercel.app/simulate" \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x123...abc", "token": "USDC", "amount": 1000, "network": "base-sepolia"}'
```

### Hedera Logger API Examples

#### Submit Log Message
```bash
curl -X POST "https://your-hedera-api-url.vercel.app/api/log" \
  -H "Content-Type: application/json" \
  -d '{"log_message": "User 0x123...abc supplied 1000 USDC to Aave"}'
```

#### Submit Transaction Log
```bash
curl -X POST "https://your-hedera-api-url.vercel.app/api/log" \
  -H "Content-Type: application/json" \
  -d '{"log_message": "TX_HASH: 0xabc...123 | ACTION: borrow | ASSET: USDC | AMOUNT: 500 | USER: 0x123...abc"}'
```

### Built-in Integration Example
The Aave API already includes built-in Hedera logging integration. Here's how it works automatically:

**Automatic Logging in Aave API:**
```python
# From main.py - this happens automatically for every transaction
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
```

**Environment Variable Configuration:**
```env
# In Aave API .env file
HEDERA_LOGGER_URL="https://your-hedera-api-url.vercel.app/api/log"
```

**Sample Automatic Log Messages:**
- `SUPPLY 1000 USDC on base-sepolia by 0x123...abc, status=1`
- `BORROW 500 USDC on base-sepolia, HF_before=2.5, status=1`
- `REPAY 250 USDC on base-sepolia by 0x123...abc, status=1`

## ⚠️ Current Limitations & Future Plans

### Current Testnet-Only Deployment
**Current Status:**
- **Aave API**: Operating on Base Sepolia and ETH Sepolia testnets only
- **Hedera Logger**: Operating on Hedera Testnet only
- **All transactions**: Use testnet tokens with no real value

### Known Technical Issues
- **Topic Configuration**: Hedera topic creation requires manual setup via `create_topic.js` script
- **Cross-API Configuration**: `HEDERA_LOGGER_URL` environment variable needs proper configuration for production deployment

### Future Development Roadmap
**Phase 1 - Mainnet Integration:**
- Deploy Aave API on Ethereum Mainnet and Polygon networks
- Deploy Hedera Logger on Hedera Mainnet for production audit trails
- Implement real asset support with proper risk management

**Phase 2 - Network Expansion:**
- Add support for additional EVM-compatible networks (Arbitrum, Optimism, Avalanche)
- Implement multi-chain logging with Hedera consensus service
- Enhanced AI agent capabilities with cross-chain operations

**Phase 3 - Advanced Features:**
- Liquidity pool analytics and optimization suggestions
- Automated risk management and liquidation protection
- Advanced simulation and forecasting tools
- Integration with additional DeFi protocols beyond Aave

## 🔗 Links

- **GitHub Repository:** https://github.com/Kimchiigu/aave-guard-mcp
- **Aave Concierge API:** https://aave-guard-mcp.vercel.app/
- **Aave API Documentation:** https://aave-guard-mcp.vercel.app/docs
- **MCP Manifest:** https://github.com/Kimchiigu/aave-guard-mcp/blob/main/aave-concierge-api/mcp-manifest.json
- **Hedera Hashgraph Docs:** https://docs.hedera.com/hedera/getting-started/mainnet
- **Aave V3 Documentation:** https://docs.aave.com/developers/guides/liquidations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support, questions, or collaboration:
- **Telegram:** [@kimchiigu](https://t.me/kimchiigu)
- **Email:** christopher.hygunawan@gmail.com
- **X/Twitter:** [@Kimchii73](https://twitter.com/Kimchii73)

---

Built with ❤️ for the [Aya Wallet Hackathon](https://aya.wallet/)