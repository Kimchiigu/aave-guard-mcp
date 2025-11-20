from fastapi import APIRouter
from config import DEFAULT_NETWORK

router = APIRouter()

@router.get("/mcp-manifest")
async def mcp_manifest():
    """
    Serve the MCP manifest for AI agent discovery.
    """
    manifest = {
        "name": "Aave Concierge MCP",
        "description": "An intelligent multi-network Aave concierge that can supply, borrow, repay, and simulate lending actions with automatic health factor checks and Hedera audit logging.",
        "version": "1.0.0",
        "contact_email": "christopher.hygunawan@gmail.com",
        "license": "MIT",
        "servers": [
            {
                "url": "https://aave-guard-mcp.vercel.app",
                "description": "Production deployment on Vercel",
                "variables": {
                    "network": {
                        "default": DEFAULT_NETWORK,
                        "enum": ["base-sepolia", "eth-sepolia"]
                    }
                }
            }
        ],
        "methods": {
            "supply": {
                "endpoint": "POST /supply",
                "summary": "Supply tokens to Aave on a given network.",
                "parameters": {
                    "amount": "float — Amount of tokens to supply (e.g., 0.1)",
                    "token": "string — Token symbol (e.g., 'USDC', 'WETH')",
                    "network": "string — Target network (e.g., 'base-sepolia')",
                    "user_address": "string — User's wallet address"
                },
                "returns": {
                    "status": "success | failure",
                    "tx_hash": "Transaction hash on success"
                }
            },
            "borrow": {
                "endpoint": "POST /borrow",
                "summary": "Borrow tokens safely. Automatically checks health factor before borrowing to prevent liquidation risk.",
                "parameters": {
                    "amount": "float — Amount of tokens to borrow",
                    "token": "string — Token symbol",
                    "network": "string — Target network",
                    "user_address": "string — User's wallet address"
                },
                "returns": {
                    "status": "success | rejected",
                    "health_factor_before": "float — Health factor before borrowing",
                    "message": "string — Human-readable message"
                }
            },
            "repay": {
                "endpoint": "POST /repay",
                "summary": "Repay a borrowed amount on Aave.",
                "parameters": {
                    "amount": "float — Amount to repay",
                    "token": "string — Token symbol",
                    "network": "string — Target network",
                    "user_address": "string — User's wallet address"
                },
                "returns": {
                    "status": "success | failure",
                    "tx_hash": "Transaction hash on success"
                }
            },
            "balance": {
                "endpoint": "GET /balance/{network}/{user}",
                "summary": "Retrieve token balances for a wallet address on the specified network.",
                "parameters": {
                    "network": "string — Network name",
                    "user": "string — Wallet address"
                },
                "returns": {
                    "balances": "Dictionary mapping token symbols to their current balances"
                }
            },
            "health": {
                "endpoint": "GET /health/{network}/{user}",
                "summary": "Fetch the user's Aave health factor and determine if borrowing is safe.",
                "parameters": {
                    "network": "string — Network name",
                    "user": "string — Wallet address"
                },
                "returns": {
                    "health_factor": "float — User's health factor",
                    "safe_to_borrow": "boolean — Whether borrowing is considered safe"
                }
            },
            "simulate": {
                "endpoint": "POST /simulate",
                "summary": "Simulate the effect of supplying or borrowing on the user's health factor without sending a transaction.",
                "parameters": {
                    "amount": "float — Amount of tokens to supply or borrow (always positive)",
                    "token": "string — Token symbol",
                    "network": "string — Network name",
                    "user_address": "string — Wallet address",
                    "action": "string — 'supply' or 'borrow' (optional, defaults to 'supply')"
                },
                "returns": {
                    "health_factor_before": "float",
                    "health_factor_after_est": "float",
                    "safety": "string — 'safe' or 'risky'",
                    "note": "string — Informational message"
                }
            }
        },
        "auditing": {
            "hedera_logger": {
                "endpoint": "https://aave-guard-mcp.vercel.app/api/hedera",
                "description": "Asynchronous audit log to Hedera Consensus Service (HCS) for all major actions."
            }
        }
    }
    return manifest