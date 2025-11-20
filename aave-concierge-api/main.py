import os
import sys
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modular components
from api.routes import router as api_router
from api.manifest import router as manifest_router

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Aave Concierge API - MCP Compliant",
    description="MCP-compliant API for AI agents to manage Aave loans, supplies, and borrows with natural language commands. Built for Aya Wallet integration.",
    version="6.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "LoanGuardian Team",
        "email": "christopher.hygunawan@gmail.com",
        "url": "https://github.com/Kimchiigu/aave-guard-mcp"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "https://aave-guard-mcp.vercel.app",
            "description": "Production deployment"
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development"
        }
    ],
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
        "docExpansion": "none"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://aave-guard-mcp.vercel.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.middleware("http")
async def add_mcp_headers(request: Request, call_next):
    """Add MCP-specific headers for AI agent discovery."""
    response = await call_next(request)

    # Add MCP discovery headers
    response.headers["X-MCP-Version"] = "1.0"
    response.headers["X-MCP-Endpoint"] = "/mcp-manifest"
    response.headers["X-AI-Agent-Friendly"] = "true"
    response.headers["X-API-Purpose"] = "Aave DeFi Operations"

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response

# Include routers
app.include_router(api_router, prefix="/api", tags=["Aave Operations"])
app.include_router(manifest_router, tags=["MCP Manifest"])

# Also include manifest route directly to ensure it works
@app.get("/mcp-manifest")
async def mcp_manifest():
    """Serve the MCP manifest for AI agent discovery."""
    from config import DEFAULT_NETWORK

    manifest = {
        "name": "Aave Concierge MCP",
        "description": "An intelligent multi-network Aave concierge that can supply, borrow, repay, and simulate lending actions with automatic health factor checks and Hedera audit logging.",
        "version": "1.0.0",
        "contact_email": "christopher.hygunawan@gmail.com",
        "license": "MIT",
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "Local development",
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
                "endpoint": "POST /api/supply",
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
                "endpoint": "POST /api/borrow",
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
                "endpoint": "POST /api/repay",
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
                "endpoint": "GET /api/balance/{network}/{user}",
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
                "endpoint": "GET /api/health/{network}/{user}",
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
                "endpoint": "POST /api/simulate",
                "summary": "Simulate the effect of supplying or borrowing on the user's health factor without sending a transaction.",
                "parameters": {
                    "amount": "float — Positive for supply, negative for borrow",
                    "token": "string — Token symbol",
                    "network": "string — Network name",
                    "user_address": "string — Wallet address"
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
                "endpoint": "http://localhost:8000/api/hedera",
                "description": "Asynchronous audit log to Hedera Consensus Service (HCS) for all major actions."
            }
        }
    }
    return manifest

# Landing page routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serve the landing page HTML content.
    Users are directed to visit /docs to try the API.
    """
    if os.path.exists(os.path.join(static_dir, "index.html")):
        with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>Aave Concierge API</title></head>
            <body>
                <h1>Aave Concierge API</h1>
                <p>Visit <a href="/docs">/docs</a> to try the API.</p>
            </body>
        </html>
        """)

@app.get("/landing")
async def landing():
    """
    Redirect to the landing page.
    """
    return RedirectResponse(url="/")

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy", "message": "Aave Concierge API is running"}

@app.get("/api/health")
async def api_health_check():
    """
    API health check endpoint.
    """
    return {"status": "healthy", "message": "Aave Concierge API endpoints are working"}
