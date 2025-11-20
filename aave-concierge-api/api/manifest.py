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
        "description": "AI-powered DeFi assistant for Aave Protocol v3. Execute safe lending operations across multiple networks with real-time health factor monitoring, gas optimization, and immutable audit logging on Hedera.",
        "version": "1.0.0",
        "contact_email": "christopher.hygunawan@gmail.com",
        "license": "MIT",
        "documentation": "https://github.com/Kimchiigu/aave-guard-mcp",
        "servers": [
            {
                "url": "https://aave-guard-mcp.vercel.app",
                "description": "Production deployment on Vercel",
                "variables": {
                    "network": {
                        "default": DEFAULT_NETWORK,
                        "enum": ["base-sepolia", "eth-sepolia"],
                        "description": "Target blockchain network for Aave operations"
                    }
                }
            }
        ],
        "ai_guidelines": {
            "recommended_workflow": [
                "1. GET /health/{network}/{user} - Check current position",
                "2. GET /balance/{network}/{user} - Review available tokens",
                "3. POST /simulate?action=supply - Test supply operations",
                "4. POST /simulate?action=borrow - Test borrow operations",
                "5. POST /supply or /borrow - Execute transactions",
                "6. POST /execute/transaction - Submit signed transaction"
            ],
            "safety_checks": [
                "Always simulate before executing transactions",
                "Monitor health factor (HF should stay > 1.1)",
                "Check gas costs before execution",
                "Review real-time prices before decisions",
                "Verify user has sufficient token balances"
            ],
            "risk_management": {
                "minimum_health_factor": 1.1,
                "recommended_health_factor": 2.0,
                "max_borrow_percentage": 0.75
            }
        },
        "methods": {
            "supply": {
                "endpoint": "POST /supply",
                "description": "Supply tokens to Aave lending protocol to earn interest and increase borrowing capacity. Automatically handles token approvals and provides gas estimates.",
                "ai_usage": "Call this when user wants to deposit tokens into Aave. ALWAYS simulate first using POST /simulate?action=supply.",
                "parameters": {
                    "amount": {
                        "type": "float",
                        "description": "Amount of tokens to supply (e.g., 100.5 for USDC, 0.1 for WETH)",
                        "validation": "Must be > 0 and user must have sufficient balance"
                    },
                    "token": {
                        "type": "string",
                        "description": "Token symbol (e.g., 'USDC', 'WETH', 'WBTC', 'USDT')",
                        "enum": ["USDC", "USDT", "WETH", "WBTC", "cbETH", "LINK"]
                    },
                    "network": {
                        "type": "string",
                        "description": "Target network (e.g., 'base-sepolia', 'eth-sepolia')",
                        "default": DEFAULT_NETWORK
                    },
                    "user_address": {
                        "type": "string",
                        "description": "User's wallet address (0x format, checksummed)",
                        "validation": "Must be valid Ethereum address"
                    }
                },
                "returns": {
                    "status": "Transaction status",
                    "transaction_data": {
                        "transaction": "Signed transaction data",
                        "approval_transaction": "Token approval transaction if needed",
                        "gas_cost": "Estimated gas cost in native tokens",
                        "note": "Execution instructions"
                    },
                    "safety_check": "Health factor analysis"
                }
            },
            "borrow": {
                "endpoint": "POST /borrow",
                "description": "Borrow tokens against supplied collateral. Automatically checks health factor to prevent liquidation risk and rejects unsafe requests.",
                "ai_usage": "Call this when user wants to borrow tokens. ALWAYS simulate first using POST /simulate?action=borrow. Ensure health factor > 1.1.",
                "parameters": {
                    "amount": {
                        "type": "float",
                        "description": "Amount of tokens to borrow",
                        "validation": "Must be > 0 and within borrowing capacity"
                    },
                    "token": {
                        "type": "string",
                        "description": "Token symbol to borrow",
                        "enum": ["USDC", "USDT", "WETH", "WBTC", "cbETH", "LINK"]
                    },
                    "network": {
                        "type": "string",
                        "description": "Target network",
                        "default": DEFAULT_NETWORK
                    },
                    "user_address": {
                        "type": "string",
                        "description": "User's wallet address"
                    }
                },
                "returns": {
                    "status": "success | blocked",
                    "health_factor_before": "Health factor before borrowing",
                    "transaction_data": {
                        "transaction": "Ready-to-sign transaction",
                        "gas_cost": "Gas estimate",
                        "note": "Safety analysis"
                    }
                }
            },
            "repay": {
                "endpoint": "POST /repay",
                "description": "Repay borrowed tokens to improve health factor and reduce liquidation risk. Supports partial or full repayment.",
                "ai_usage": "Call this when user wants to repay borrowed tokens. Consider simulating impact on health factor first.",
                "parameters": {
                    "amount": {
                        "type": "float",
                        "description": "Amount to repay",
                        "validation": "Must be > 0"
                    },
                    "token": {
                        "type": "string",
                        "description": "Token symbol to repay"
                    },
                    "network": {
                        "type": "string",
                        "description": "Target network",
                        "default": DEFAULT_NETWORK
                    },
                    "user_address": {
                        "type": "string",
                        "description": "User's wallet address"
                    }
                },
                "returns": {
                    "status": "Transaction status",
                    "transaction_data": {
                        "transaction": "Ready-to-sign transaction",
                        "gas_cost": "Gas estimate"
                    }
                }
            },
            "simulate": {
                "endpoint": "POST /simulate",
                "description": "Risk-free simulation of supply or borrow operations. Shows exact impact on health factor without spending gas. ESSENTIAL for AI decision making.",
                "ai_usage": "ALWAYS call this before executing any transaction. Use for planning, risk assessment, and optimizing amounts.",
                "parameters": {
                    "amount": {
                        "type": "float",
                        "description": "Amount to simulate (always positive)"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to simulate",
                        "enum": ["supply", "borrow"],
                        "default": "supply"
                    },
                    "token": {
                        "type": "string",
                        "description": "Token symbol"
                    },
                    "network": {
                        "type": "string",
                        "description": "Target network"
                    },
                    "user_address": {
                        "type": "string",
                        "description": "User's wallet address"
                    }
                },
                "returns": {
                    "action": "Simulated action",
                    "health_factor_before": "Current health factor",
                    "health_factor_after_est": "Estimated health factor after action",
                    "safety": "Risk assessment (safe/risky)",
                    "token_data": {
                        "price_usd": "Current token price",
                        "ltv": "Loan-to-value ratio",
                        "liquidation_threshold": "Liquidation threshold"
                    },
                    "available_borrows": "Available borrowing capacity (for borrow actions)",
                    "note": "Detailed analysis and recommendations"
                }
            },
            "health": {
                "endpoint": "GET /health/{network}/{user}",
                "description": "Get current Aave health factor and borrowing safety status. Critical for risk assessment.",
                "ai_usage": "Call this first to understand user's current position and borrowing capacity.",
                "parameters": {
                    "network": "string — Network name",
                    "user": "string — Wallet address (0x format)"
                },
                "returns": {
                    "health_factor": "Current health factor (>1.1 = safe)",
                    "safe_to_borrow": "Whether borrowing is safe",
                    "risk_level": "Risk assessment (safe/cautionary/dangerous)"
                }
            },
            "balance": {
                "endpoint": "GET /balance/{network}/{user}",
                "description": "Get comprehensive token balances including underlying tokens, aTokens, and variable debt tokens across all supported assets.",
                "ai_usage": "Call this to understand user's available assets for supplying or tokens for repayment.",
                "parameters": {
                    "network": "string — Network name",
                    "user": "string — Wallet address"
                },
                "returns": {
                    "address": "User address",
                    "network": "Network name",
                    "total_supply_value": "Total value of supplied collateral",
                    "total_borrow_value": "Total value of borrowed tokens",
                    "tokens": "Detailed breakdown per token including underlying, aToken, and vToken balances"
                }
            },
            "prices": {
                "endpoint": "GET /prices/{network}",
                "description": "Get real-time oracle prices for all supported tokens with current LTV and liquidation thresholds.",
                "ai_usage": "Call this for market analysis and to understand current token valuations.",
                "parameters": {
                    "network": "string — Network name"
                },
                "returns": {
                    "network": "Network name",
                    "timestamp": "Price timestamp",
                    "oracle_address": "Aave oracle contract address",
                    "prices": "Token prices and risk parameters"
                }
            },
            "gas_estimate": {
                "endpoint": "GET /gas/estimate/{network}/{token}/{amount}",
                "description": "Get detailed gas cost estimates for transactions. Essential for cost optimization.",
                "ai_usage": "Call this to estimate transaction costs before execution.",
                "parameters": {
                    "network": "string — Network name",
                    "token": "string — Token symbol",
                    "amount": "float — Transaction amount"
                },
                "returns": {
                    "supply_gas_estimate": "Gas units needed for supply",
                    "supply_gas_cost": "Cost in native tokens",
                    "approval_gas_cost": "Cost for token approval (if needed)",
                    "total_gas_cost": "Total estimated cost",
                    "gas_price_gwei": "Current gas price"
                }
            }
        },
        "risk_management": {
            "automatic_protections": [
                "Health factor validation",
                "Borrowing capacity checks",
                "Gas cost warnings",
                "Token balance verification"
            ],
            "safety_thresholds": {
                "minimum_health_factor": 1.1,
                "recommended_health_factor": 2.0,
                "max_single_borrow_percentage": 0.5
            }
        },
        "auditing": {
            "hedera_logger": {
                "endpoint": "https://aave-guard-mcp.vercel.app/api/hedera",
                "description": "Immutable audit logging on Hedera Consensus Service (HCS) for all major actions. Every transaction is permanently recorded for transparency and compliance.",
                "features": ["Immutable storage", "Timestamp verification", "Transaction tracking"]
            }
        },
        "monitoring": {
            "real_time_data": "Live oracle prices and risk parameters",
            "health_factor_monitoring": "Continuous position safety checks",
            "gas_optimization": "Dynamic gas cost estimation"
        }
    }
    return manifest