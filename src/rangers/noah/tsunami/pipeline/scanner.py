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

# Compression risk scoring: optimized weights from grid search
# against known casualties (should score low) vs elevated-multiple targets (high).
# P/E premium is the anchor: no elevated multiple = no compression opportunity.
COMPRESSION_WEIGHTS = {
    "pe_premium": 0.45,
    "margin_fragility": 0.30,
    "capital_inefficiency": 0.10,
    "cash_vulnerability": 0.05,
    "leverage_amplifier": 0.10,
}


def _compute_pe_premium(pe: float, eps: float) -> float:
    """How far above utility-level (12x) is the P/E? 0-1 scale."""
    if pe <= 0 or eps <= 0:
        return 0.0  # negative earnings = already dead, no compression left
    return min(1.0, max(0.0, (pe - 12.0) / 38.0))


def _compute_margin_fragility(sga_pct: float, gross_margin_pct: float) -> float:
    """High SGA × high margin = expensive human-delivered service. 0-1 scale."""
    sga = sga_pct or 0
    gm = gross_margin_pct or 0
    return min(1.0, (sga * gm) / 0.35)


def _compute_capital_inefficiency(roic_pct: float | None) -> float:
    """Low ROIC = capital deployed poorly. 0-1 scale (1 = worst)."""
    if roic_pct is None:
        return 0.5
    return 1.0 - max(0.0, min(1.0, (roic_pct + 0.2) / 0.45))


def _compute_cash_vulnerability(fcf_yield_pct: float | None) -> float:
    """Low/negative FCF = no buffer during compression. 0-1 scale."""
    if fcf_yield_pct is None:
        return 0.5
    return 1.0 - max(0.0, min(1.0, (fcf_yield_pct + 0.15) / 0.35))


def _compute_leverage_amplifier(debt_to_equity: float | None) -> float:
    """High debt amplifies compression via covenant risk. 0-1 scale."""
    if debt_to_equity is None:
        return 0.0
    return min(1.0, debt_to_equity / 3.0)


def compute_vulnerability_score(
    financials: dict, weights: dict[str, float],
    pe: float = 0.0, eps: float = 0.0,
) -> float:
    """Compute compression risk score (0-1).

    Parameters
    ----------
    financials : dict
        Raw metrics from the data adapter.
    weights : dict
        Legacy parameter (ignored -- uses COMPRESSION_WEIGHTS).
    pe : float
        Current P/E ratio.
    eps : float
        Current EPS.

    Returns
    -------
    float
        Clamped compression risk score between 0 and 1.
    """
    pe_prem = _compute_pe_premium(pe, eps)
    marg_frag = _compute_margin_fragility(
        financials.get("sga_pct"), financials.get("gross_margin_pct")
    )
    cap_ineff = _compute_capital_inefficiency(financials.get("roic_pct"))
    cash_vuln = _compute_cash_vulnerability(financials.get("fcf_yield_pct"))
    lev_amp = _compute_leverage_amplifier(financials.get("debt_to_equity"))

    w = COMPRESSION_WEIGHTS
    score = (
        pe_prem * w["pe_premium"]
        + marg_frag * w["margin_fragility"]
        + cap_ineff * w["capital_inefficiency"]
        + cash_vuln * w["cash_vulnerability"]
        + lev_amp * w["leverage_amplifier"]
    )
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

    # Pull valuation first -- needed for compression scoring
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

    # Load weights (legacy param, ignored by new scoring)
    weights = _load_weights_from_db(path) or DEFAULT_FEATURE_WEIGHTS

    # Score using compression model (P/E premium is the anchor)
    vulnerability_score = compute_vulnerability_score(
        financials, weights, pe=current_pe, eps=current_eps
    )
    logger.info(
        "Ticker %s compression_score=%.4f (gate=%.2f) P/E=%.1f",
        ticker,
        vulnerability_score,
        VULNERABILITY_GATE,
        current_pe,
    )

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
