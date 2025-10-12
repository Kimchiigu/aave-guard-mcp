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

### One-Sentence Elevator Pitch
An MCP-compliant API that lets AI agents like Aya's manage Aave loans, supplies, and borrows using simple natural language commands

### Detailed Project Description
**LoanGuardian** (solo) is a comprehensive DeFi platform that combines Aave protocol integration with decentralized consensus logging. The project consists of two complementary APIs:

**Aave Concierge API:** DeFi protocols like Aave are powerful but their complexity creates a barrier for AI agents. The Aave Concierge API solves this by acting as a simple, intelligent bridge.

Our serverless API, built with Python and FastAPI, exposes a suite of clean endpoints (/health, /supply, /borrow, /repay) that are fully compliant with the Model Context Protocol (MCP). This allows an AI agent, such as the one in Aya Wallet, to discover and use these tools to execute on-chain transactions based on a user's natural language commands.

**Hedera Consensus Logger API:** To ensure transparency and immutability, we've implemented a decentralized logging service using Hedera Hashgraph Consensus Service (HCS). This API provides immutable audit trails for all transactions, creating a trustworthy record that can be verified by anyone on the Hedera network.

For this hackathon, both APIs are deployed on Vercel - the Aave API operates on the Base Sepolia testnet, while the Hedera Logger runs on Hedera Testnet, providing a complete solution with decentralized consensus features.

## 📋 Features

### Aave Concierge API
The API provides a suite of "concierge" services for Aave:

- **GET /health/{user_address}**: Instantly checks a user's health factor
- **POST /supply**: Supplies assets to Aave on behalf of a user
- **POST /borrow**: Borrows assets from Aave for a user
- **POST /repay**: Repays a user's debt from the executor wallet

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

To use this API with an AI agent, you will need the `tool_spec.json` file. This file describes the API's capabilities in a machine-readable format that the AI can understand.

## 📖 Usage Examples

### Aave Concierge API Examples

#### Check User Health
```bash
curl -X GET "https://aave-guard-mcp.vercel.app/health/0x123...abc"
```

#### Supply Assets
```bash
curl -X POST "https://aave-guard-mcp.vercel.app/supply" \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x123...abc", "asset": "USDC", "amount": "1000"}'
```

#### Borrow Assets
```bash
curl -X POST "https://aave-guard-mcp.vercel.app/borrow" \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x123...abc", "asset": "USDC", "amount": "500"}'
```

#### Repay Debt
```bash
curl -X POST "https://aave-guard-mcp.vercel.app/repay" \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x123...abc", "asset": "USDC", "amount": "250"}'
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

### Integration Example
The Aave API can be configured to automatically log transactions to the Hedera Logger API:

```python
# Example integration in Aave API
import requests

def log_transaction_to_hedera(action, user_address, asset, amount, tx_hash):
    log_message = f"TX_HASH: {tx_hash} | ACTION: {action} | ASSET: {asset} | AMOUNT: {amount} | USER: {user_address}"

    response = requests.post(
        "https://your-hedera-api-url.vercel.app/api/log",
        json={"log_message": log_message}
    )

    return response.json()
```

## ⚠️ Known Issues

### Current Known Issues

#### Aave Concierge API Issues
- **Transaction Rejections**: The methods for repay, borrow, and supply are currently being rejected by the EVM, but the API endpoints work correctly. This is likely related to gas configuration, smart contract interactions, or testnet-specific issues that need to be resolved.

#### Hedera Logger API Issues
- **Topic Configuration**: Users need to manually create a Hedera topic using the `create_topic.js` script before the logger API can function properly.
- **Testnet Limitations**: Currently operating on Hedera Testnet, which may have different performance characteristics compared to mainnet.

#### Integration Issues
- **Cross-API Communication**: While both APIs are designed to work together, the automatic logging integration between Aave transactions and Hedera consensus logging needs to be implemented in the Aave API code.

## 🔗 Links

- **GitHub Repository:** https://github.com/Kimchiigu/aave-guard-mcp
- **Aave Concierge API:** https://aave-guard-mcp.vercel.app/
- **Hedera Logger API:** Deployed separately (URL depends on your Vercel setup)
- **Aave API Documentation:** Available at `/docs` endpoint
- **Hedera Hashgraph Docs:** https://docs.hedera.com/hedera/getting-started/mainnet

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support, questions, or collaboration:
- **Telegram:** [@kimchiigu](https://t.me/kimchiigu)
- **Email:** christopher.hygunawan@gmail.com
- **X/Twitter:** [@Kimchiigu73](https://twitter.com/Kimchiigu73)

---

Built with ❤️ for the [Aya Wallet Hackathon](https://aya.wallet/)