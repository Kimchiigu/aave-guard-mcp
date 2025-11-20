from pydantic import BaseModel
from config import DEFAULT_NETWORK
from typing import Optional, Literal

class AaveRequest(BaseModel):
    """Base request model for Aave operations."""
    amount: float
    token: str
    network: str = DEFAULT_NETWORK
    user_address: str
    action: Optional[Literal["supply", "borrow"]] = None  # New optional action parameter


class TransactionRequest(BaseModel):
    """Request model for transaction building."""
    amount: float
    token: str
    network: str = DEFAULT_NETWORK
    user_address: str
    slippage_tolerance_bps: int = 50  # 0.5% default slippage tolerance


class TransactionResponse(BaseModel):
    """Response model with unsigned transaction data."""
    status: str
    transaction_data: dict  # Unsigned transaction data for user to sign
    gas_estimate: int
    estimated_gas_cost: Optional[float] = None  # In native token (ETH, etc.)
    approval_tx_data: Optional[dict] = None  # For tokens that need approval
    note: str


class ExecuteTransactionRequest(BaseModel):
    """Request model for executing a signed transaction."""
    signed_transaction: str
    network: str = DEFAULT_NETWORK


class SupplyResponse(BaseModel):
    """Response model for supply operations."""
    status: str
    tx_hash: str | None = None
    transaction_data: Optional[dict] = None  # New: include transaction data


class BorrowResponse(BaseModel):
    """Response model for borrow operations."""
    status: str
    tx_hash: str | None = None
    health_factor_before: float | None = None
    transaction_data: Optional[dict] = None  # New: include transaction data


class RepayResponse(BaseModel):
    """Response model for repay operations."""
    status: str
    tx_hash: str | None = None
    transaction_data: Optional[dict] = None  # New: include transaction data


class TokenBalance(BaseModel):
    """Individual token balance information."""
    underlying: float = 0
    aToken: float = 0
    vToken: float = 0
    underlying_address: str | None = None
    aToken_address: str | None = None
    vToken_address: str | None = None


class BalanceResponse(BaseModel):
    """Response model for balance queries with all token types."""
    address: str
    network: str
    total_supply_value: float = 0
    total_borrow_value: float = 0
    tokens: dict[str, TokenBalance]


class HealthResponse(BaseModel):
    """Response model for health factor queries."""
    health_factor: float
    safe_to_borrow: bool


class SimulateResponse(BaseModel):
    """Response model for simulation operations."""
    action: str
    token: str
    amount: float
    network: str
    health_factor_before: float
    health_factor_after_est: float
    safety: str
    note: str
    available_borrows: float | None = None
    current_capacity_check: str | None = None