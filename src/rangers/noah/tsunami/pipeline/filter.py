# src/rangers/noah/tsunami/pipeline/filter.py
"""Stage 4: VRP Filter.

Compares implied volatility to realized volatility to reject
overpriced puts.  VRP = atm_put_iv - hv_252d.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from ..adapters.base import DataAdapter
from ..config import DB_PATH, VRP_REJECT_THRESHOLD
from ..db import get_connection
from ..models.schemas import FrictionData, Prediction

logger = logging.getLogger(__name__)


def compute_hv_252d(price_df: pd.DataFrame) -> float | None:
    """Compute annualized 252-day historical volatility from daily closes.

    Parameters
    ----------
    price_df : pd.DataFrame
        Must contain a 'Close' column with at least 253 rows.

    Returns
    -------
    float or None
        Annualized HV, or None if insufficient data.
    """
    if price_df is None or price_df.empty or len(price_df) < 253:
        return None

    closes = price_df["Close"].dropna().values
    if len(closes) < 253:
        return None

    # Use last 253 prices to get 252 log returns
    prices = closes[-253:]
    log_returns = np.log(prices[1:] / prices[:-1])
    hv = float(np.std(log_returns) * np.sqrt(252))
    return hv


def compute_vrp(atm_put_iv: float, hv_252d: float) -> float:
    """Compute Volatility Risk Premium.

    VRP = atm_put_iv - hv_252d

    Positive VRP = puts are expensive relative to realized vol.
    Negative VRP = puts are cheap (premium discount).
    """
    return atm_put_iv - hv_252d


def classify_vrp(vrp: float) -> str:
    """Classify VRP into action buckets.

    - VRP >= VRP_REJECT_THRESHOLD (0.15): REJECT
    - 0 <= VRP < VRP_REJECT_THRESHOLD: FAIR_VALUE
    - VRP < 0: PREMIUM_DISCOUNT
    """
    if vrp >= VRP_REJECT_THRESHOLD:
        return "REJECT"
    elif vrp >= 0:
        return "FAIR_VALUE"
    else:
        return "PREMIUM_DISCOUNT"


def _get_atm_put_iv(
    adapter: DataAdapter, ticker: str, spot: float, min_dte: int = 180
) -> tuple[float | None, float | None, float | None]:
    """Find the ATM put IV and premium from the options chain.

    Returns (atm_put_iv, est_premium_ask, put_call_ratio).
    """
    try:
        chain = adapter.get_options_chain(ticker, min_dte=min_dte)
    except Exception as exc:
        logger.warning("Cannot fetch options chain for %s: %s", ticker, exc)
        return None, None, None

    if chain is None or chain.empty:
        logger.warning("Empty options chain for %s", ticker)
        return None, None, None

    # Find strike nearest to spot
    chain = chain.copy()
    chain["dist"] = (chain["strike"] - spot).abs()
    atm_row = chain.loc[chain["dist"].idxmin()]

    iv = float(atm_row.get("impliedVolatility", 0))
    bid = float(atm_row.get("bid", 0))
    ask = float(atm_row.get("ask", 0))
    premium = (bid + ask) / 2.0 if (bid + ask) > 0 else ask

    # Put/call ratio (approximate from volume if available)
    total_vol = chain["volume"].sum() if "volume" in chain.columns else 0
    put_call_ratio = 1.0  # placeholder; full chain would need calls too

    return iv, premium, put_call_ratio


def filter_targets(
    predictions: list[Prediction],
    adapter: DataAdapter,
    db_path: str | None = None,
) -> list[tuple[Prediction, FrictionData]]:
    """Filter a list of predictions by VRP.

    Returns predictions that pass the VRP gate, sorted by VRP ascending
    (cheapest puts first).

    Parameters
    ----------
    predictions : list[Prediction]
        Predictions that have passed the compression gate.
    adapter : DataAdapter
        Financial data source.
    db_path : str, optional
        Override for the SQLite database path.

    Returns
    -------
    list of (Prediction, FrictionData) tuples, sorted by VRP ascending.
    """
    path = db_path or DB_PATH
    results: list[tuple[Prediction, FrictionData, float]] = []

    for pred in predictions:
        ticker = pred.ticker
        spot = pred.current_spot

        # Compute HV
        try:
            hist = adapter.get_historical_prices(ticker, period="2y")
            hv = compute_hv_252d(hist)
        except Exception as exc:
            logger.warning("Cannot compute HV for %s: %s", ticker, exc)
            hv = None

        if hv is None:
            logger.warning(
                "Skipping %s from VRP filter -- insufficient historical data", ticker
            )
            continue

        # Get ATM put IV
        atm_iv, premium, pcr = _get_atm_put_iv(adapter, ticker, spot)
        if atm_iv is None:
            logger.warning(
                "Skipping %s from VRP filter -- no options chain data", ticker
            )
            continue

        vrp = compute_vrp(atm_iv, hv)
        classification = classify_vrp(vrp)

        friction = FrictionData(
            target_id=pred.target_id,
            ticker=ticker,
            live_spot=spot,
            atm_put_iv=atm_iv,
            put_call_ratio=pcr or 1.0,
            est_premium_ask=premium or 0.0,
            hv_252d=hv,
            vrp_spread=vrp,
        )

        # Persist to market_friction_log
        with get_connection(path) as conn:
            conn.execute(
                """
                INSERT INTO market_friction_log (
                    target_id, live_spot, atm_put_iv, put_call_ratio,
                    est_premium_ask, hv_252d, vrp_spread
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pred.target_id,
                    spot,
                    atm_iv,
                    pcr or 1.0,
                    premium or 0.0,
                    hv,
                    vrp,
                ),
            )

        logger.info(
            "Ticker %s: VRP=%.4f (%s), IV=%.4f, HV=%.4f",
            ticker,
            vrp,
            classification,
            atm_iv,
            hv,
        )

        if classification == "REJECT":
            logger.info("Ticker %s REJECTED -- VRP too high (%.4f)", ticker, vrp)
            continue

        results.append((pred, friction, vrp))

    # Sort by VRP ascending (cheapest puts first)
    results.sort(key=lambda x: x[2])

    return [(pred, friction) for pred, friction, _ in results]
