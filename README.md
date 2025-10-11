Aave Concierge API
🚀 Project Overview
The Aave Concierge API is a serverless backend service designed to act as a powerful interface between an AI agent (like the one in Aya Wallet) and the Aave V3 protocol. It simplifies complex blockchain interactions into a suite of clean, human-readable API endpoints.

This allows a user to perform Aave actions using natural language, with the AI agent translating their intent into calls to this API.

This project is designed for the Base Sepolia testnet.

✨ Features
The API provides a suite of "concierge" services for Aave:

GET /health/{user_address}: Instantly checks a user's health factor.

POST /supply: Supplies assets to Aave on behalf of a user.

POST /borrow: Borrows assets from Aave for a user.

POST /repay: Repays a user's debt from the executor wallet.

🛠️ Setup and Installation
Clone the repository:

git clone <your-repo-url>
cd aave-guard-mcp

Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

Install dependencies:

pip install -r requirements.txt

Create a .env file:
Create a file named .env in the root of the project and add the following variables:

ALCHEMY_API_KEY="your_alchemy_api_key_for_base_sepolia"
EXECUTOR_PRIVATE_KEY="your_secure_executor_wallet_private_key"
AAVE_POOL_ADDRESS_PROVIDER_V3_BASE_SEPOLIA="0xE4C23309117Aa30342BFaae6c95c6478e0A4Ad00"

🏃 Running the API Locally
Start the server:

uvicorn main:app --reload

Access the documentation:
The API documentation (powered by Swagger UI) will be available at http://127.0.0.1:8000/docs. You can test all the endpoints directly from your browser.

🚀 Deployment
This API is designed to be deployed as a serverless function on a platform like Vercel.

Create vercel.json:

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

Deploy: Connect your GitHub repository to Vercel and deploy. Remember to add your environment variables in the Vercel project settings.

🤖 AI Agent Integration
To use this API with an AI agent, you will need the tool_spec.json file. This file describes the API's capabilities in a machine-readable format that the AI can understand.