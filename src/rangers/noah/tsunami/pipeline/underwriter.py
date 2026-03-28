# src/rangers/noah/tsunami/pipeline/underwriter.py
"""Stage 6: Underwriter -- strike selection and execution matrix generation.

Selects the optimal put contract (strike, expiry) and calculates
the Return on Premium (ROP) for each signal.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from ..adapters.base import DataAdapter
from ..config import (
    DB_PATH,
    ROP_MINIMUM,
    TARGET_DTE_MAX,
    TARGET_DTE_MIN,
)
from ..db import get_connection
from ..models.schemas import ExecutionRow, Position, Signal

logger = logging.getLogger(__name__)

TARGET_DTE_IDEAL = 240  # ideal days to expiry


def select_strike(
    current_spot: float,
    predicted_drop_pct: float,
    available_strikes: list[float],
) -> float:
    """Select the listed strike nearest to the midpoint between spot and target.

    midpoint = current_spot * (1 - predicted_drop / 2)

    This targets "halfway to the target" to maximize the balance between
    intrinsic value at target and premium cost.
    """
    target_strike = current_spot * (1.0 - predicted_drop_pct / 2.0)
    best = min(available_strikes, key=lambda s: abs(s - target_strike))
    logger.info(
        "Strike selection: spot=%.2f, drop=%.2f%%, target=%.2f, selected=%.2f",
        current_spot,
        predicted_drop_pct * 100,
        target_strike,
        best,
    )
    return best


def select_expiry(expiry_dates: list[str]) -> str | None:
    """Select the expiration date closest to 240 DTE within [180, 300] range.

    Parameters
    ----------
    expiry_dates : list[str]
        Dates in YYYY-MM-DD format.

    Returns
    -------
    str or None
        Selected expiry date string, or None if nothing in range.
    """
    now = datetime.utcnow()
    candidates = []

    for exp_str in expiry_dates:
        exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
        dte = (exp_dt - now).days
        if TARGET_DTE_MIN <= dte <= TARGET_DTE_MAX:
            candidates.append((exp_str, abs(dte - TARGET_DTE_IDEAL)))

    if not candidates:
        logger.warning("No expiry dates within DTE range [%d, %d]", TARGET_DTE_MIN, TARGET_DTE_MAX)
        return None

    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]


def compute_rop(
    strike: float, projected_price: float, premium: float
) -> float:
    """Compute Return on Premium.

    ROP = (intrinsic_at_target - premium) / premium

    where intrinsic_at_target = max(0, strike - projected_price).

    Must be >= ROP_MINIMUM (3.0) to EXECUTE.
    """
    if premium <= 0:
        return -1.0

    intrinsic_at_target = max(0.0, strike - projected_price)
    return (intrinsic_at_target - premium) / premium


def underwrite_signal(
    signal: Signal,
    adapter: DataAdapter,
    db_path: str | None = None,
) -> Optional[ExecutionRow]:
    """Underwrite a single signal into an execution row.

    Selects strike and expiry from the live options chain, computes ROP,
    and determines EXECUTE or REJECT.

    Parameters
    ----------
    signal : Signal
        Sized signal from the Kelly sizer.
    adapter : DataAdapter
        Financial data source for options chain.
    db_path : str, optional
        Override for the SQLite database path.

    Returns
    -------
    ExecutionRow or None
        None only if no options chain is available at all.
    """
    path = db_path or DB_PATH
    ticker = signal.ticker

    # Get options chain
    try:
        chain = adapter.get_options_chain(ticker, min_dte=TARGET_DTE_MIN)
    except Exception as exc:
        logger.error("Cannot fetch options chain for %s: %s", ticker, exc)
        return None

    if chain is None or chain.empty:
        logger.warning("No options chain for %s -- cannot underwrite", ticker)
        return None

    # Select expiry
    expiry_dates = sorted(chain["expiry"].unique().tolist())
    expiry = select_expiry(expiry_dates)
    if expiry is None:
        # Fall back to any available expiry
        expiry = expiry_dates[-1] if expiry_dates else None
        if expiry is None:
            logger.warning("No expiry dates available for %s", ticker)
            return None

    # Filter chain to selected expiry
    exp_chain = chain[chain["expiry"] == expiry]
    available_strikes = sorted(exp_chain["strike"].tolist())
    if not available_strikes:
        logger.warning("No strikes available for %s at expiry %s", ticker, expiry)
        return None

    # Select strike
    strike = select_strike(
        current_spot=signal.current_spot,
        predicted_drop_pct=signal.predicted_drop_pct,
        available_strikes=available_strikes,
    )

    # Get premium for the selected strike
    strike_row = exp_chain.loc[(exp_chain["strike"] - strike).abs().idxmin()]
    bid = float(strike_row.get("bid", 0))
    ask = float(strike_row.get("ask", 0))
    premium_per_share = (bid + ask) / 2.0 if (bid + ask) > 0 else ask

    if premium_per_share <= 0:
        logger.warning("Zero premium for %s strike %.2f -- cannot underwrite", ticker, strike)
        return None

    # Compute ROP
    rop = compute_rop(strike, signal.projected_price, premium_per_share)

    # Calculate contracts
    # Each contract = 100 shares
    cost_per_contract = premium_per_share * 100.0
    if cost_per_contract <= 0:
        return None
    contracts = max(1, int(signal.capital_to_deploy / cost_per_contract))
    actual_capital = contracts * cost_per_contract

    # Intrinsic at target for reporting
    intrinsic_at_target = max(0.0, strike - signal.projected_price)

    # Decision
    decision = "EXECUTE" if rop >= ROP_MINIMUM else "REJECT"

    logger.info(
        "Underwrite %s: strike=%.2f, expiry=%s, premium=%.2f, "
        "contracts=%d, ROP=%.2f, decision=%s",
        ticker,
        strike,
        expiry,
        premium_per_share,
        contracts,
        rop,
        decision,
    )

    row = ExecutionRow(
        ticker=ticker,
        strike=strike,
        expiry_date=expiry,
        contracts=contracts,
        premium_per_share=premium_per_share,
        capital_deployed=actual_capital,
        projected_price=signal.projected_price,
        intrinsic_at_target=intrinsic_at_target,
        rop=rop,
        kelly_pct=signal.kelly_pct,
        decision=decision,
    )

    # Persist position to DB if EXECUTE
    if decision == "EXECUTE":
        try:
            with get_connection(path) as conn:
                conn.execute(
                    """
                    INSERT INTO positions (
                        target_id, strike, expiry_date, premium_paid,
                        contracts, capital_deployed, kelly_pct, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
                    """,
                    (
                        signal.target_id,
                        strike,
                        expiry,
                        premium_per_share,
                        contracts,
                        actual_capital,
                        signal.kelly_pct,
                    ),
                )
        except Exception as exc:
            logger.error("Failed to persist position for %s: %s", ticker, exc)

    return row


def underwrite_all(
    signals: list[Signal],
    adapter: DataAdapter,
    db_path: str | None = None,
) -> list[ExecutionRow]:
    """Underwrite all signals and return the execution matrix.

    Parameters
    ----------
    signals : list[Signal]
        Sized signals from the Kelly sizer.
    adapter : DataAdapter
        Financial data source.
    db_path : str, optional
        Override for the SQLite database path.

    Returns
    -------
    list[ExecutionRow]
        The full execution matrix (includes both EXECUTE and REJECT rows).
    """
    rows = []
    for signal in signals:
        row = underwrite_signal(signal, adapter, db_path)
        if row is not None:
            rows.append(row)

    execute_count = sum(1 for r in rows if r.decision == "EXECUTE")
    reject_count = sum(1 for r in rows if r.decision == "REJECT")
    logger.info(
        "Execution matrix: %d EXECUTE, %d REJECT out of %d signals",
        execute_count,
        reject_count,
        len(signals),
    )

    return rows
