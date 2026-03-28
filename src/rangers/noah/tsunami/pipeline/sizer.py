# src/rangers/noah/tsunami/pipeline/sizer.py
"""Stage 5: Kelly Criterion Position Sizer.

Calculates optimal position size using fractional (quarter) Kelly.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..config import (
    DEFAULT_WIN_PROB,
    KELLY_FRACTION,
    MAX_POSITION_PCT,
)
from ..models.schemas import FrictionData, Prediction, Signal

logger = logging.getLogger(__name__)


def compute_payoff_ratio(
    projected_price: float, strike: float, premium: float
) -> float:
    """Compute the payoff ratio b for the Kelly formula.

    b = (intrinsic_at_target - premium) / premium

    where intrinsic_at_target = max(0, strike - projected_price).

    Returns 0.0 if premium is zero (avoid division by zero).
    """
    if premium <= 0:
        return 0.0

    intrinsic = max(0.0, strike - projected_price)
    return (intrinsic - premium) / premium


def compute_kelly(p: float, b: float) -> float:
    """Compute the full Kelly fraction.

    f* = p - (q / b)  where q = 1 - p

    Returns the raw (full) Kelly value.  May be negative if the trade
    has negative expected value.
    """
    if b <= 0:
        return -1.0  # signal that trade is not viable

    q = 1.0 - p
    return p - (q / b)


def size_position(
    prediction: Prediction,
    friction: FrictionData,
    portfolio_value: float,
    win_prob: float | None = None,
) -> Optional[Signal]:
    """Size a single position using quarter-Kelly with a 10% hard cap.

    Parameters
    ----------
    prediction : Prediction
        Must have projected_price and current_spot filled in.
    friction : FrictionData
        Must have est_premium_ask and live_spot.
    portfolio_value : float
        Total portfolio value in dollars.
    win_prob : float, optional
        Override win probability (default: DEFAULT_WIN_PROB from config).

    Returns
    -------
    Signal or None
        Returns None if Kelly fraction is <= 0 (negative expected value).
    """
    p = win_prob if win_prob is not None else DEFAULT_WIN_PROB
    premium = friction.est_premium_ask
    spot = friction.live_spot

    # Use a midpoint strike for sizing estimation
    # (actual strike selected by underwriter later)
    estimated_strike = spot * (1.0 + prediction.predicted_drop_pct / 2.0)
    # The strike should be BELOW spot for a put
    # predicted_drop_pct is positive (e.g. 0.70 means 70% drop)
    # midpoint strike = spot * (1 - predicted_drop/2) = halfway to target
    estimated_strike = spot * (1.0 - prediction.predicted_drop_pct / 2.0)

    b = compute_payoff_ratio(
        projected_price=prediction.projected_price,
        strike=estimated_strike,
        premium=premium,
    )

    f_full = compute_kelly(p, b)

    if f_full <= 0:
        logger.info(
            "Ticker %s REJECTED by Kelly -- f*=%.4f (negative EV). p=%.2f, b=%.2f",
            prediction.ticker,
            f_full,
            p,
            b,
        )
        return None

    f_applied = min(f_full * KELLY_FRACTION, MAX_POSITION_PCT)
    capital_to_deploy = portfolio_value * f_applied

    logger.info(
        "Ticker %s: f_full=%.4f, quarter_kelly=%.4f, capped=%.4f, capital=$%.2f",
        prediction.ticker,
        f_full,
        f_full * KELLY_FRACTION,
        f_applied,
        capital_to_deploy,
    )

    return Signal(
        target_id=prediction.target_id,
        ticker=prediction.ticker,
        predicted_drop_pct=prediction.predicted_drop_pct,
        projected_price=prediction.projected_price,
        current_spot=spot,
        vrp_spread=friction.vrp_spread,
        kelly_pct=f_applied,
        capital_to_deploy=capital_to_deploy,
        win_probability=p,
        payoff_ratio=b,
    )


def size_all(
    filtered: list[tuple[Prediction, FrictionData]],
    portfolio_value: float,
    win_prob: float | None = None,
) -> list[Signal]:
    """Size all filtered targets.

    Parameters
    ----------
    filtered : list of (Prediction, FrictionData) tuples
        Output from the VRP filter stage.
    portfolio_value : float
        Total portfolio value.
    win_prob : float, optional
        Override win probability.

    Returns
    -------
    list[Signal]
        Only signals with positive Kelly allocation.
    """
    signals = []
    for pred, friction in filtered:
        signal = size_position(pred, friction, portfolio_value, win_prob)
        if signal is not None:
            signals.append(signal)

    logger.info(
        "Sized %d positions from %d filtered targets", len(signals), len(filtered)
    )
    return signals
