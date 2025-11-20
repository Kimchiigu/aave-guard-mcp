import os
import time
import traceback
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from web3 import Web3

from models import (
    AaveRequest, SupplyResponse, BorrowResponse, RepayResponse,
    BalanceResponse, HealthResponse, SimulateResponse, TokenBalance,
    TransactionRequest, TransactionResponse, ExecuteTransactionRequest
)
from contracts import init_web3, get_pool_contract, get_token_contract, get_pool_address, build_pool_transaction
from utils import (
    log_to_hedera, schedule_log, get_health_factor,
    amount_to_wei, validate_user_address, build_transaction,
    build_approval_transaction, estimate_gas_cost, get_token_allowance,
    get_token_decimals
)
from oracle import (
    get_real_time_token_price, get_real_time_liquidation_threshold,
    get_all_real_time_asset_data
)

router = APIRouter()

# ============================================================
# API ENDPOINTS
# ============================================================

@router.post("/supply", response_model=SupplyResponse)
async def supply(req: AaveRequest):
    """Supply tokens - build transaction for user to sign."""
    try:
        w3, _, cfg = init_web3(req.network, with_executor=False)
        token = req.token.upper()
        if token not in cfg["assets"]:
            raise HTTPException(400, f"{token} not supported on {req.network}")

        asset_data = cfg["assets"][token]
        user = validate_user_address(req.user_address)
        provider_addr = cfg["pool_provider"]
        pool_addr = get_pool_address(w3, provider_addr)
        amount_wei = amount_to_wei(req.amount, token, cfg)

        # Check if approval is needed
        approval_tx_data = None
        if asset_data["underlying"] != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeEee":
            current_allowance = get_token_allowance(w3, asset_data["underlying"], user, pool_addr)
            if current_allowance < amount_wei:
                approval_tx_data = build_approval_transaction(
                    w3, user, asset_data["underlying"], pool_addr, amount_wei, cfg["chain_id"]
                )

        # Build supply transaction
        tx_data = build_pool_transaction(
            w3, provider_addr, "supply",
            asset_data["underlying"], amount_wei, user, 0
        )

        # Complete transaction
        transaction = {
            "to": tx_data["to"],
            "data": tx_data["data"],
            "from": user,
            "nonce": w3.eth.get_transaction_count(user),
            "chainId": cfg["chain_id"],
            "gas": tx_data.get("gas", 300000),
            "value": tx_data.get("value", 0)
        }

        gas_cost = estimate_gas_cost(w3, transaction["gas"])

        msg = f"Built supply transaction for {req.amount} {token} on {req.network} for {user}"
        schedule_log(msg)

        return {
            "status": "ready_for_signing",
            "tx_hash": None,
            "transaction_data": {
                "transaction": transaction,
                "approval_transaction": approval_tx_data,
                "gas_cost": gas_cost,
                "note": "Please sign the approval transaction first (if provided), then sign the supply transaction"
            }
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@router.post("/borrow", response_model=BorrowResponse)
async def borrow(req: AaveRequest):
    """Borrow tokens safely with health factor check - build transaction for user to sign."""
    try:
        w3, _, cfg = init_web3(req.network, with_executor=False)
        token = req.token.upper()
        if token not in cfg["assets"]:
            raise HTTPException(400, f"{token} not supported on {req.network}")

        provider_addr = cfg["pool_provider"]
        pool = get_pool_contract(w3, provider_addr)
        user = validate_user_address(req.user_address)
        hf = get_health_factor(pool, user)

        if hf < 1.1:
            msg = f"❌ Borrow blocked — health factor={hf}"
            schedule_log(msg)
            raise HTTPException(400, f"Health factor too low ({hf}). Borrowing not safe.")

        asset_data = cfg["assets"][token]
        amount_wei = amount_to_wei(req.amount, token, cfg)

        # Build borrow transaction (variable interest rate mode = 2, referral code = 0)
        tx_data = build_pool_transaction(
            w3, provider_addr, "borrow",
            asset_data["underlying"], amount_wei, 2, 0, user
        )

        # Complete transaction
        transaction = {
            "to": tx_data["to"],
            "data": tx_data["data"],
            "from": user,
            "nonce": w3.eth.get_transaction_count(user),
            "chainId": cfg["chain_id"],
            "gas": tx_data.get("gas", 400000),  # Borrow operations might need more gas
            "value": tx_data.get("value", 0)
        }

        gas_cost = estimate_gas_cost(w3, transaction["gas"])

        msg = f"Built borrow transaction for {req.amount} {token} on {req.network} for {user}, HF_before={hf}"
        schedule_log(msg)

        return {
            "status": "ready_for_signing",
            "tx_hash": None,
            "health_factor_before": hf,
            "transaction_data": {
                "transaction": transaction,
                "gas_cost": gas_cost,
                "note": f"Safe to borrow. Health factor: {hf}. Please sign the transaction to complete borrowing."
            }
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@router.post("/repay", response_model=RepayResponse)
async def repay(req: AaveRequest):
    """Repay borrowed tokens - build transaction for user to sign."""
    try:
        w3, _, cfg = init_web3(req.network, with_executor=False)
        token = req.token.upper()
        if token not in cfg["assets"]:
            raise HTTPException(400, f"{token} not supported on {req.network}")

        asset_data = cfg["assets"][token]
        amount_wei = amount_to_wei(req.amount, token, cfg)
        user = validate_user_address(req.user_address)
        provider_addr = cfg["pool_provider"]

        # Build repay transaction (variable interest rate mode = 2)
        tx_data = build_pool_transaction(
            w3, provider_addr, "repay",
            asset_data["underlying"], amount_wei, 2, user
        )

        # Complete transaction
        transaction = {
            "to": tx_data["to"],
            "data": tx_data["data"],
            "from": user,
            "nonce": w3.eth.get_transaction_count(user),
            "chainId": cfg["chain_id"],
            "gas": tx_data.get("gas", 350000),
            "value": tx_data.get("value", 0)
        }

        gas_cost = estimate_gas_cost(w3, transaction["gas"])

        msg = f"Built repay transaction for {req.amount} {token} on {req.network} for {user}"
        schedule_log(msg)

        return {
            "status": "ready_for_signing",
            "tx_hash": None,
            "transaction_data": {
                "transaction": transaction,
                "gas_cost": gas_cost,
                "note": "Please sign the transaction to complete repayment. Make sure you have sufficient tokens to repay."
            }
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@router.get("/health/{network}/{user}", response_model=HealthResponse)
async def health(network: str, user: str):
    """Get user's health factor and borrowing safety status."""
    w3, _, cfg = init_web3(network)
    pool = get_pool_contract(w3, Web3.to_checksum_address(cfg["pool_provider"]))
    user_address = validate_user_address(user)
    hf = get_health_factor(pool, user_address)
    return {"health_factor": hf, "safe_to_borrow": hf >= 1.1}


@router.get("/balance/{network}/{user}", response_model=BalanceResponse)
async def balance(network: str, user: str):
    """Get token balances for a user on a specific network including all token types."""
    w3, _, cfg = init_web3(network)
    user_address = validate_user_address(user)

    # ERC20 ABI for balanceOf function
    erc20_abi = [
        {
            "name": "balanceOf",
            "inputs": [{"type": "address"}],
            "outputs": [{"type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

  
    tokens = {}
    total_supply_value = 0
    total_borrow_value = 0

    for token_symbol, asset_data in cfg["assets"].items():
        token_info = TokenBalance()

        # Set addresses from config
        token_info.underlying_address = asset_data["underlying"]
        token_info.aToken_address = asset_data.get("a_token")
        token_info.vToken_address = asset_data.get("v_token")

        # Check underlying token balance
        try:
            underlying_token = get_token_contract(w3, asset_data["underlying"])
            raw_balance = underlying_token.functions.balanceOf(user_address).call()
            from utils import format_token_amount
            token_info.underlying = format_token_amount(raw_balance, token_symbol, cfg)
        except Exception:
            token_info.underlying = 0

        # Check aToken balance
        if token_info.aToken_address:
            try:
                a_token = w3.eth.contract(address=token_info.aToken_address, abi=erc20_abi)
                raw_balance = a_token.functions.balanceOf(user_address).call()
                token_info.aToken = format_token_amount(raw_balance, token_symbol, cfg)
                # Approximate supply value (simplified - assumes 1:1 with underlying)
                total_supply_value += token_info.aToken
            except Exception:
                token_info.aToken = 0

        # Check vToken balance
        if token_info.vToken_address:
            try:
                v_token = w3.eth.contract(address=token_info.vToken_address, abi=erc20_abi)
                raw_balance = v_token.functions.balanceOf(user_address).call()
                token_info.vToken = format_token_amount(raw_balance, token_symbol, cfg)
                # Approximate borrow value (simplified)
                total_borrow_value += token_info.vToken
            except Exception:
                token_info.vToken = 0

        tokens[token_symbol] = token_info

    return {
        "address": user,
        "network": network,
        "total_supply_value": total_supply_value,
        "total_borrow_value": total_borrow_value,
        "tokens": tokens
    }


# Optional: Add a simple cache for real-time data (cache lasts 60 seconds)
_real_time_data_cache = {}
_cache_timestamps = {}

def get_cached_real_time_data(network: str, cfg: dict, cache_duration: int = 60) -> dict:
    """Get cached real-time data or fetch fresh data if cache expired"""
    cache_key = f"{network}_realtime_data"
    current_time = time.time()

    # Check if we have valid cached data
    if (cache_key in _real_time_data_cache and
        cache_key in _cache_timestamps and
        current_time - _cache_timestamps[cache_key] < cache_duration):
        return _real_time_data_cache[cache_key]

    # Fetch fresh data
    print(f"[DEBUG] Cache miss or expired, fetching fresh real-time data...")
    fresh_data = get_all_real_time_asset_data(network, cfg)

    # Update cache
    _real_time_data_cache[cache_key] = fresh_data
    _cache_timestamps[cache_key] = current_time

    return fresh_data


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(req: AaveRequest):
    """Dry-run simulation of supply or borrow to estimate health factor effect."""
    w3, _, cfg = init_web3(req.network)
    user = validate_user_address(req.user_address)
    pool = get_pool_contract(w3, Web3.to_checksum_address(cfg["pool_provider"]))
    token = req.token.upper()

    if token not in cfg["assets"]:
        raise HTTPException(400, f"{token} not supported on {req.network}")

    # Input validation - prevent unrealistic amounts
    max_reasonable_amount = 1000000000  # 1 billion tokens
    if abs(req.amount) > max_reasonable_amount:
        raise HTTPException(400, f"Amount too large. Maximum reasonable amount is {max_reasonable_amount:,} tokens")

    # Determine action based on the action parameter
    if req.action:
        if req.action not in ["supply", "borrow"]:
            raise HTTPException(400, "Action must be either 'supply' or 'borrow'")
        action = req.action
    else:
        # Backward compatibility: positive = supply, negative = borrow (deprecated)
        action = "supply" if req.amount > 0 else "borrow"
        if req.amount < 0:
            # Convert negative amount to positive for borrow
            req.amount = abs(req.amount)

    # Get current account data
    try:
        # Debug pool contract info
        pool_address = pool.address
        print(f"[DEBUG] Pool Contract Address: {pool_address}")
        print(f"[DEBUG] Network: {req.network}")
        print(f"[DEBUG] User Address: {user}")

        account_data = pool.functions.getUserAccountData(user).call()
        total_collateral_base = account_data[0]  # Total collateral in base currency (not scaled by 1e18)
        total_debt_base = account_data[1]        # Total debt in base currency (not scaled by 1e18)
        available_borrows_base = account_data[2]  # Available borrowing capacity (not scaled by 1e18)
        current_liquidation_threshold = account_data[3]  # Weighted avg liquidation threshold (Ray format: 1e27)
        current_ltv = account_data[4]  # Weighted avg LTV (Ray format: 1e27)
        hf_before = round(account_data[5] / 1e18 if account_data[5] else 100.0, 3)  # Health Factor is in 1e18 format

        # Convert Ray format (1e27) to human-readable for liquidation threshold and LTV
        liquidation_threshold_human = current_liquidation_threshold / 1e27 if current_liquidation_threshold > 0 else 0
        ltv_human = current_ltv / 1e27 if current_ltv > 0 else 0

        # Convert base currency to human-readable (assuming 8 decimals for USD-like values)
        total_collateral_usd = total_collateral_base / 1e8
        total_debt_usd = total_debt_base / 1e8
        available_borrows_usd = available_borrows_base / 1e8

        # Convert liquidation threshold from Ray format to multiplier
        # The liquidation threshold seems to be in a different format than expected
        # Let's try multiple interpretations to find the correct one
        lt_interpretation_1 = current_liquidation_threshold / 1e27  # Standard Ray format
        lt_interpretation_2 = current_liquidation_threshold / 1e4   # Maybe it's percentage basis points (8505 = 85.05%)
        lt_interpretation_3 = current_liquidation_threshold / 10000  # Similar to interpretation 2

        print(f"[DEBUG] Liquidation Threshold Interpretations:")
        print(f"  Raw Value: {current_liquidation_threshold}")
        print(f"  As Ray format (÷1e27): {lt_interpretation_1}")
        print(f"  As basis points (÷1e4): {lt_interpretation_2}")
        print(f"  As percentage (÷100): {current_liquidation_threshold / 100}")

        # Use the interpretation that makes most sense (basis points seems most likely)
        weighted_avg_lt = lt_interpretation_2  # 8505 / 10000 = 0.8505 = 85.05%

        # Debug logging
        print(f"[DEBUG] User Account Data for {user}:")
        print(f"  Total Collateral (USD): ${total_collateral_usd:.2f}")
        print(f"  Total Debt (USD): ${total_debt_usd:.2f}")
        print(f"  Available Borrows (USD): ${available_borrows_usd:.2f}")
        print(f"  Liquidation Threshold (using basis points): {weighted_avg_lt:.4f} ({weighted_avg_lt*100:.2f}%)")
        print(f"  LTV: {ltv_human:.4f} ({ltv_human*100:.2f}%)")

        # Debug: Check if we can get LTV from real-time data
        try:
            real_time_data = get_all_real_time_asset_data(req.network, cfg)
            if token_symbol in real_time_data:
                real_ltv = real_time_data[token_symbol].get("ltv", 0)
                print(f"  Real-time LTV for {token}: {real_ltv:.4f} ({real_ltv*100:.2f}%)")
        except Exception as e:
            print(f"[DEBUG] Could not get real-time LTV data: {e}")
        print(f"  Health Factor: {hf_before}")
        print(f"  Raw Account Data: {account_data}")
        print(f"  Raw Liquidation Threshold: {current_liquidation_threshold}")
        print(f"  Raw LTV: {current_ltv}")
        print(f"  Raw Health Factor (1e18): {account_data[5]}")

        # Additional debug for formula verification (now that weighted_avg_lt is defined)
        if total_debt_base > 0:
            calculated_hf = (total_collateral_base * weighted_avg_lt) / total_debt_base
            print(f"  Manual HF Calculation: (Collateral:{total_collateral_base} × LT:{weighted_avg_lt}) ÷ Debt:{total_debt_base} = {calculated_hf}")
            print(f"  Expected HF from contract: {hf_before}")
            print(f"  Difference: {abs(calculated_hf - hf_before)}")
        else:
            print(f"  Manual HF Calculation: No debt, HF should be infinite/high")

    except Exception as e:
        raise HTTPException(500, f"Failed to get account data: {str(e)}")

    # Get real-time asset data from Aave protocol (includes both LTV and liquidation threshold)
    print(f"[DEBUG] Fetching real-time asset data for {token}...")
    real_time_data = get_all_real_time_asset_data(req.network, cfg)

    token_lt = 0.80  # Default liquidation threshold
    token_ltv = 0.0  # Default LTV

    if token in real_time_data:
        token_data = real_time_data[token]
        token_lt = token_data.get("liquidation_threshold", 0.80)
        token_ltv = token_data.get("ltv", 0.0)
        print(f"[DEBUG] Real-time LT for {token}: {token_lt:.2%}, LTV: {token_ltv:.2%}")
    else:
        print(f"[WARN] No real-time data for {token}, using fallback LT=80%, LTV=0%")

    # Debug: Check if oracle is loaded from config
    if token in cfg["assets"] and "oracle" in cfg["assets"][token]:
        oracle_address = cfg["assets"][token]["oracle"]
        print(f"[DEBUG] Oracle address for {token} from config: {oracle_address}")
    else:
        print(f"[DEBUG] No oracle address found in config for {token}")

    # Get token decimals from config (dynamic)
    token_decimals = cfg["assets"][token]["decimals"]
    print(f"[DEBUG] Using dynamic token decimals: {token} has {token_decimals} decimals")

    # Get real-time token price from Aave oracle
    print(f"[DEBUG] Fetching real-time price for {token}...")
    token_price = get_real_time_token_price(req.network, token, cfg)
    if token_price <= 0:
        print(f"[WARN] Using fallback price for {token}")
        token_price = 1.0  # Default fallback
    else:
        print(f"[DEBUG] Real-time price for {token}: ${token_price:.2f}")

    # Debug: Check if oracle is loaded from config for pricing
    if token in cfg["assets"] and "oracle" in cfg["assets"][token]:
        oracle_address = cfg["assets"][token]["oracle"]
        print(f"[DEBUG] Using oracle address: {oracle_address}")
    else:
        print(f"[DEBUG] No oracle address found in config for {token}")

    # Calculate new health factor based on the determined action
    if action == "supply":

        # For supply, calculate the token value in base currency correctly
        # Step 1: Convert human-readable amount to token wei (respecting token decimals)
        token_amount_wei = int(req.amount * (10 ** token_decimals))

        # Step 2: Convert token wei to human-readable amount for USD calculation
        token_amount_human = token_amount_wei / (10 ** token_decimals)

        # Step 3: Calculate USD value and convert to base currency format (8 decimals to match contract)
        token_value_usd = token_amount_human * token_price
        token_value_base = int(token_value_usd * 1e8)  # Use 8 decimals to match contract format

        print(f"[DEBUG] Supply calculation for {req.amount} {token}:")
        print(f"  Token value USD: ${token_value_usd:.2f}")
        print(f"  Token value base: {token_value_base}")
        print(f"  Current collateral base: {total_collateral_base}")
        print(f"  Current debt base: {total_debt_base}")
        print(f"  Current weighted LT: {weighted_avg_lt:.4f}")
        print(f"  Token LT: {token_lt:.4f}")
        print(f"  Token LTV: {token_ltv:.4f}")

        # For supply, we need to recalculate the weighted average liquidation threshold
        # Weighted Avg LT = (Sum of (Collateral Value × LT)) / Total Collateral Value

        # Current weighted collateral value (Total Collateral × Weighted Avg LT)
        current_weighted_collateral = total_collateral_base * weighted_avg_lt

        # New asset contribution to weighted collateral (using token's liquidation threshold)
        new_weighted_contribution = token_value_base * token_lt

        # New total weighted collateral and total collateral
        new_weighted_collateral = current_weighted_collateral + new_weighted_contribution
        new_total_collateral = total_collateral_base + token_value_base
        new_total_debt = total_debt_base

        # Calculate new weighted average liquidation threshold
        new_weighted_avg_lt = new_weighted_collateral / new_total_collateral if new_total_collateral > 0 else 0

        print(f"  New weighted collateral: {new_weighted_collateral}")
        print(f"  New total collateral: {new_total_collateral}")
        print(f"  New weighted avg LT: {new_weighted_avg_lt:.4f}")

        # Calculate new health factor using Aave formula
        if new_total_debt == 0:
            hf_after = 100.0  # Very high health factor when no debt
        else:
            # HF = (Total Collateral Value × Weighted Average Liquidation Threshold) ÷ Total Borrow Value
            # Note: Using base currency format from contract
            hf_after = (new_total_collateral * new_weighted_avg_lt) / new_total_debt
            print(f"  HF calculation: ({new_total_collateral} × {new_weighted_avg_lt}) ÷ {new_total_debt} = {hf_after}")

    else:  # action == "borrow"
        borrow_amount = req.amount  # Amount is already positive

        # Calculate the USD value of the token being borrowed correctly
        # Step 1: Convert human-readable amount to token wei (respecting token decimals)
        token_amount_wei = int(borrow_amount * (10 ** token_decimals))

        # Step 2: Convert token wei to human-readable amount for USD calculation
        token_amount_human = token_amount_wei / (10 ** token_decimals)

        # Step 3: Calculate USD value and convert to base currency format (8 decimals)
        token_value_usd = token_amount_human * token_price
        borrow_value_base = int(token_value_usd * 1e8)  # Use 8 decimals to match contract format

        # Debug logging for borrow calculation
        print(f"[DEBUG] Borrow Calculation for {borrow_amount} {token}:")
        print(f"  Token Decimals: {token_decimals}")
        print(f"  Token Amount (wei): {token_amount_wei}")
        print(f"  Token Amount (human): {token_amount_human}")
        print(f"  Token Price: ${token_price}")
        print(f"  USD Value: ${token_value_usd}")
        print(f"  Borrow Value (base): {borrow_value_base}")
        print(f"  Available Borrows (base): {available_borrows_base}")
        print(f"  Available Borrows (USD): ${available_borrows_usd:.2f}")
        print(f"  Comparison: {borrow_value_base} > {available_borrows_base} = {borrow_value_base > available_borrows_base}")

        # Check if user has enough borrowing capacity
        if borrow_value_base > available_borrows_base:
            hf_after = 0
            safety = "insufficient capacity ❌"
            return {
                "action": action,
                "token": token,
                "amount": borrow_amount,
                "network": req.network,
                "health_factor_before": hf_before,
                "health_factor_after_est": hf_after,
                "safety": safety,
                "available_borrows": available_borrows_usd,
                "current_capacity_check": "❌ Insufficient capacity",
                "note": f"Insufficient borrowing capacity. Available: ${available_borrows_usd:.2f}, Requested: ${token_value_usd}"
            }

        # For borrow, the weighted average liquidation threshold remains the same
        # since we're not changing the collateral composition
        new_weighted_avg_lt = weighted_avg_lt
        new_total_collateral = total_collateral_base
        new_total_debt = total_debt_base + borrow_value_base

        # Calculate new health factor using Aave formula
        if new_total_debt == 0:
            hf_after = 100.0
        else:
            # HF = (Total Collateral Value × Weighted Average Liquidation Threshold) ÷ Total Borrow Value
            hf_after = (new_total_collateral * new_weighted_avg_lt) / new_total_debt

    # Cap health factor to prevent overflow and keep it realistic
    hf_after = min(hf_after, 999.999)  # Cap at 999.999 to prevent display issues
    hf_after = round(hf_after, 3)
    safety = "safe ✅" if hf_after >= 1.1 else "risky ⚠️"

    msg = f"Simulated {action} {abs(req.amount)} {token} on {req.network}: HF {hf_before}→{hf_after} ({safety})"
    schedule_log(msg)

    # Build result dict properly to avoid key issues
    result = {
        "action": action,
        "token": token,
        "amount": req.amount,
        "network": req.network,
        "health_factor_before": hf_before,
        "health_factor_after_est": hf_after,
        "safety": safety,
        "token_data": {
            "price_usd": round(token_price, 6),
            "ltv": round(token_ltv, 4),
            "liquidation_threshold": round(token_lt, 4)
        },
        "note": "Dry-run only; no blockchain transaction executed. Using Aave HF formula."
    }

    if action == "borrow":
        result["available_borrows"] = round(available_borrows_base / 1e8, 6)
        result["current_capacity_check"] = "✅ Sufficient capacity" if borrow_value_base <= available_borrows_base else "❌ Insufficient capacity"

    return result


@router.get("/prices/{network}")
async def get_real_time_prices(network: str):
    """Get real-time prices for all supported tokens on a network."""
    try:
        w3, _, cfg = init_web3(network)

        print(f"[DEBUG] Fetching real-time prices for {network}")
        print(f"[DEBUG] Network config: oracle={cfg.get('oracle')}, assets={len(cfg.get('assets', {}))}")

        # Get cached real-time data
        real_time_data = get_cached_real_time_data(network, cfg)

        if not real_time_data:
            raise HTTPException(500, "Failed to fetch real-time data")

        print(f"[DEBUG] Real-time data retrieved for {len(real_time_data)} tokens")
        for token, data in real_time_data.items():
            print(f"  {token}: ${data.get('price', 0):.4f}, LT={data.get('liquidation_threshold', 0):.2%}, LTV={data.get('ltv', 0):.2%}")

        return {
            "network": network,
            "timestamp": _cache_timestamps.get(f"{network}_realtime_data", time.time()),
            "oracle_address": cfg.get("oracle"),
            "prices": real_time_data
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Failed to get real-time prices: {str(e)}")

@router.post("/build/transaction", response_model=TransactionResponse)
async def build_transaction_endpoint(req: TransactionRequest):
    """Build transaction data for user to sign."""
    try:
        w3, _, cfg = init_web3(req.network, with_executor=False)
        token = req.token.upper()
        if token not in cfg["assets"]:
            raise HTTPException(400, f"{token} not supported on {req.network}")

        asset_data = cfg["assets"][token]
        user = validate_user_address(req.user_address)
        provider_addr = cfg["pool_provider"]
        pool_addr = get_pool_address(w3, provider_addr)
        amount_wei = amount_to_wei(req.amount, token, cfg)

        # For supply operations, check if approval is needed
        approval_tx_data = None

        # Only supply operations need approval (borrow/repay don't need token approval)
        # Supply operations need to transfer tokens to Aave pool
        if asset_data["underlying"] != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeEee":  # Not native token
            current_allowance = get_token_allowance(w3, asset_data["underlying"], user, pool_addr)
            if current_allowance < amount_wei:
                # Build approval transaction
                approval_tx_data = build_approval_transaction(
                    w3, user, asset_data["underlying"], pool_addr, amount_wei, cfg["chain_id"]
                )

        # Determine action type - for simplicity, default to supply
        # In a real implementation, you'd have separate endpoints or an action parameter
        action = "supply"
        referral_code = 0

        # Build the main transaction
        if action == "supply":
            tx_data = build_pool_transaction(
                w3, provider_addr, "supply",
                asset_data["underlying"], amount_wei, user, referral_code
            )
        else:
            raise HTTPException(400, f"Action {action} not implemented in builder yet")

        # Complete transaction with proper fields
        transaction = {
            "to": tx_data["to"],
            "data": tx_data["data"],
            "from": user,
            "nonce": w3.eth.get_transaction_count(user),
            "chainId": cfg["chain_id"],
            "gas": tx_data.get("gas", 300000),  # Default gas limit
            "value": tx_data.get("value", 0)
        }

        # Estimate gas cost
        gas_estimate = transaction["gas"]
        estimated_gas_cost = estimate_gas_cost(w3, gas_estimate)

        msg = f"Built {action} transaction for {req.amount} {token} on {req.network} for {user}"
        schedule_log(msg)

        return TransactionResponse(
            status="ready",
            transaction_data=transaction,
            gas_estimate=gas_estimate,
            estimated_gas_cost=estimated_gas_cost,
            approval_tx_data=approval_tx_data,
            note=f"Transaction ready for signing. Gas cost: {estimated_gas_cost:.6f} native tokens."
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@router.post("/execute/transaction")
async def execute_transaction_endpoint(req: ExecuteTransactionRequest):
    """Execute a signed transaction from user."""
    try:
        w3, _, cfg = init_web3(req.network, with_executor=False)

        # Send the signed transaction
        tx_hash = w3.eth.send_raw_transaction(req.signed_transaction)

        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        msg = f"Executed transaction on {req.network}: {tx_hash.hex()}, status={receipt.status}"
        schedule_log(msg)

        if receipt.status == 1:
            return {
                "status": "success",
                "tx_hash": tx_hash.hex(),
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "effective_gas_price": receipt.effectiveGasPrice
            }
        else:
            raise HTTPException(500, "Transaction failed")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@router.get("/gas/estimate/{network}/{token}/{amount}")
async def estimate_gas(network: str, token: str, amount: float):
    """Estimate gas costs for transactions."""
    try:
        w3, _, cfg = init_web3(network, with_executor=False)
        token_symbol = token.upper()
        if token_symbol not in cfg["assets"]:
            raise HTTPException(400, f"{token} not supported on {network}")

        asset_data = cfg["assets"][token_symbol]
        provider_addr = cfg["pool_provider"]
        amount_wei = amount_to_wei(amount, token_symbol, cfg)

        # Estimate supply transaction gas
        try:
            tx_data = build_pool_transaction(
                w3, provider_addr, "supply",
                asset_data["underlying"], amount_wei,
                validate_user_address("0x0000000000000000000000000000000000000000"), 0
            )

            # Get more accurate gas estimate
            pool_addr = get_pool_address(w3, provider_addr)
            pool_abi = [
                {
                    "inputs": [
                        {"type": "address", "name": "asset"},
                        {"type": "uint256", "name": "amount"},
                        {"type": "address", "name": "onBehalfOf"},
                        {"type": "uint16", "name": "referralCode"},
                    ],
                    "name": "supply",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function",
                }
            ]
            pool_contract = w3.eth.contract(address=pool_addr, abi=pool_abi)
            gas_estimate = pool_contract.functions.supply(
                asset_data["underlying"], amount_wei,
                validate_user_address("0x0000000000000000000000000000000000000000"), 0
            ).estimate_gas({'from': validate_user_address("0x0000000000000000000000000000000000000000")})
        except Exception:
            gas_estimate = 300000  # Fallback estimate

        # Estimate gas cost
        gas_cost = estimate_gas_cost(w3, gas_estimate)

        # Check if approval is needed and its cost
        approval_gas = 0
        approval_cost = 0
        if asset_data["underlying"] != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeEee":
            approval_gas = 50000  # Standard approval gas
            approval_cost = estimate_gas_cost(w3, approval_gas)

        return {
            "network": network,
            "token": token_symbol,
            "amount": amount,
            "supply_gas_estimate": gas_estimate,
            "supply_gas_cost": gas_cost,
            "approval_gas_estimate": approval_gas,
            "approval_gas_cost": approval_cost,
            "total_gas_estimate": gas_estimate + approval_gas,
            "total_gas_cost": gas_cost + approval_cost,
            "needs_approval": approval_gas > 0,
            "gas_price_gwei": float(w3.from_wei(w3.eth.gas_price, 'gwei'))
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))