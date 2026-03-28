# src/rangers/noah/tsunami/pipeline/scanner.py
"""Stage 1: Vulnerability Scanner.

Pulls financial metrics via the data adapter, computes a weighted
vulnerability score, and gates on VULNERABILITY_GATE.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from ..adapters.base import DataAdapter
from ..config import (
    DB_PATH,
    DEFAULT_FEATURE_WEIGHTS,
    VULNERABILITY_GATE,
)
from ..db import get_connection
from ..models.schemas import Prediction

logger = logging.getLogger(__name__)

# Normalization ranges for each metric.
# (min_bad, max_bad) -- values outside are clamped.
# Higher raw score = MORE vulnerable.
METRIC_RANGES = {
    "sga_pct": {"min": 0.05, "max": 0.60, "direction": "higher_is_worse"},
    "gross_margin_pct": {"min": 0.20, "max": 0.90, "direction": "lower_is_worse"},
    "debt_to_equity": {"min": 0.0, "max": 3.0, "direction": "higher_is_worse"},
    "fcf_yield_pct": {"min": -0.10, "max": 0.15, "direction": "lower_is_worse"},
    "roic_pct": {"min": -0.10, "max": 0.30, "direction": "lower_is_worse"},
}


def _normalize_metric(value: float | None, metric_name: str) -> float:
    """Normalize a raw metric to 0-1 where 1 = most vulnerable.

    Returns 0.5 (neutral) when value is None.
    """
    if value is None:
        return 0.5

    spec = METRIC_RANGES[metric_name]
    lo = spec["min"]
    hi = spec["max"]

    # Clamp
    clamped = max(lo, min(hi, value))

    # Scale to 0-1
    if hi == lo:
        normalized = 0.5
    else:
        normalized = (clamped - lo) / (hi - lo)

    # Flip direction so 1 always = most vulnerable
    if spec["direction"] == "lower_is_worse":
        normalized = 1.0 - normalized

    return normalized


def compute_vulnerability_score(
    financials: dict, weights: dict[str, float]
) -> float:
    """Compute weighted composite vulnerability score (0-1).

    Parameters
    ----------
    financials : dict
        Raw metrics from the data adapter (sga_pct, gross_margin_pct, etc.).
    weights : dict
        Feature name -> weight (should sum to ~1.0).

    Returns
    -------
    float
        Clamped vulnerability score between 0 and 1.
    """
    score = 0.0
    for feature, weight in weights.items():
        raw = financials.get(feature)
        normalized = _normalize_metric(raw, feature)
        score += normalized * weight

    return max(0.0, min(1.0, score))


def _load_weights_from_db(db_path: str) -> dict[str, float] | None:
    """Load the latest backtester weights from model_weights table.

    Returns None if no weights exist (use defaults).
    """
    try:
        with get_connection(db_path) as conn:
            rows = conn.execute(
                """
                SELECT feature_name, weight_pct
                FROM model_weights
                WHERE created_at = (SELECT MAX(created_at) FROM model_weights)
                """
            ).fetchall()
            if not rows:
                return None
            return {row["feature_name"]: row["weight_pct"] for row in rows}
    except Exception:
        return None


def _get_target_id(ticker: str, db_path: str) -> str | None:
    """Look up the target_id for a ticker."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT target_id FROM target_companies WHERE ticker = ?",
            (ticker,),
        ).fetchone()
        return row["target_id"] if row else None


def scan_ticker(
    ticker: str,
    adapter: DataAdapter,
    db_path: str | None = None,
) -> Optional[Prediction]:
    """Run the vulnerability scan on a single ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol.
    adapter : DataAdapter
        Financial data source.
    db_path : str, optional
        Override for the SQLite database path.

    Returns
    -------
    Prediction or None
        Returns the Prediction if the ticker passes the vulnerability gate,
        otherwise None.
    """
    path = db_path or DB_PATH
    target_id = _get_target_id(ticker, path)
    if target_id is None:
        logger.warning("Ticker %s not found in target_companies table", ticker)
        return None

    # Pull financials
    try:
        financials = adapter.get_financials(ticker)
    except Exception as exc:
        logger.error("Failed to get financials for %s: %s", ticker, exc)
        return None

    # Load weights (backtester-derived or defaults)
    weights = _load_weights_from_db(path) or DEFAULT_FEATURE_WEIGHTS

    # Score
    vulnerability_score = compute_vulnerability_score(financials, weights)
    logger.info(
        "Ticker %s vulnerability_score=%.4f (gate=%.2f)",
        ticker,
        vulnerability_score,
        VULNERABILITY_GATE,
    )

    # Pull valuation for persistence even if below gate
    try:
        valuation = adapter.get_valuation(ticker)
        current_eps = valuation.get("eps", 0.0)
        current_pe = valuation.get("pe", 0.0)
    except Exception:
        current_eps = 0.0
        current_pe = 0.0

    try:
        current_spot = adapter.get_price(ticker)
    except Exception:
        current_spot = 0.0

    # Persist raw scan to DB
    prediction = Prediction(
        target_id=target_id,
        ticker=ticker,
        sga_pct=financials.get("sga_pct") or 0.0,
        gross_margin_pct=financials.get("gross_margin_pct") or 0.0,
        debt_to_equity=financials.get("debt_to_equity") or 0.0,
        fcf_yield_pct=financials.get("fcf_yield_pct") or 0.0,
        roic_pct=financials.get("roic_pct") or 0.0,
        vulnerability_score=vulnerability_score,
        current_eps=current_eps,
        current_pe=current_pe,
        current_spot=current_spot,
        eps_decay_pct=0.0,  # set by compressor
        terminal_pe=0.0,  # set by compressor
        projected_price=0.0,  # set by compressor
        predicted_drop_pct=0.0,  # set by compressor
    )

    with get_connection(path) as conn:
        conn.execute(
            """
            INSERT INTO fundamental_predictions (
                target_id, sga_pct, gross_margin_pct, debt_to_equity,
                fcf_yield_pct, roic_pct, vulnerability_score,
                current_eps, current_pe
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                target_id,
                prediction.sga_pct,
                prediction.gross_margin_pct,
                prediction.debt_to_equity,
                prediction.fcf_yield_pct,
                prediction.roic_pct,
                prediction.vulnerability_score,
                prediction.current_eps,
                prediction.current_pe,
            ),
        )

    # Gate
    if vulnerability_score <= VULNERABILITY_GATE:
        logger.info("Ticker %s below vulnerability gate -- skipping", ticker)
        return None

    return prediction
