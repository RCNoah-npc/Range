# src/rangers/noah/tsunami/pipeline/compressor.py
"""Stage 2: Multiple Compression Calculator.

Projects a target share price after AI-driven earnings decay and
P/E multiple compression.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, Tuple

from ..config import (
    COMPRESSION_GATE,
    DB_PATH,
    SECTOR_DEFAULTS_PATH,
    UNKNOWN_SECTOR_EPS_DECAY,
    UNKNOWN_SECTOR_TERMINAL_PE,
)
from ..db import get_connection
from ..models.schemas import Prediction

logger = logging.getLogger(__name__)


def load_sector_defaults(
    sector: str, sector_defaults_path: str | None = None
) -> Tuple[float, float]:
    """Load eps_decay and terminal_pe for a sector.

    Falls back to UNKNOWN_SECTOR_* values if sector is not found.

    Returns
    -------
    tuple of (eps_decay, terminal_pe)
    """
    path = sector_defaults_path or SECTOR_DEFAULTS_PATH
    try:
        with open(path, "r") as f:
            defaults = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Cannot load sector defaults from %s: %s", path, exc)
        return UNKNOWN_SECTOR_EPS_DECAY, UNKNOWN_SECTOR_TERMINAL_PE

    if sector in defaults:
        entry = defaults[sector]
        return entry["eps_decay"], entry["terminal_pe"]

    logger.warning(
        "Unknown sector '%s' -- using fallback eps_decay=%.2f, terminal_pe=%.1f",
        sector,
        UNKNOWN_SECTOR_EPS_DECAY,
        UNKNOWN_SECTOR_TERMINAL_PE,
    )
    return UNKNOWN_SECTOR_EPS_DECAY, UNKNOWN_SECTOR_TERMINAL_PE


def compute_projected_price(
    current_eps: float,
    current_spot: float,
    eps_decay: float,
    terminal_pe: float,
) -> float:
    """Compute the projected share price after multiple compression.

    If current_eps <= 0, falls back to a revenue-based percentage haircut:
        projected_price = current_spot * (1 - eps_decay)

    Otherwise:
        projected_price = (current_eps * (1 - eps_decay)) * terminal_pe
    """
    if current_eps <= 0:
        return current_spot * (1.0 - eps_decay)

    return (current_eps * (1.0 - eps_decay)) * terminal_pe


def compress(
    prediction: Prediction,
    db_path: str | None = None,
    sector_defaults_path: str | None = None,
) -> Optional[Prediction]:
    """Run compression on a scanned prediction.

    Fills in eps_decay_pct, terminal_pe, projected_price, and
    predicted_drop_pct on the prediction.

    Parameters
    ----------
    prediction : Prediction
        Output from the scanner with vulnerability_score filled in.
    db_path : str, optional
        Override for the SQLite database path.
    sector_defaults_path : str, optional
        Override path for sector_defaults.json.

    Returns
    -------
    Prediction or None
        Updated prediction if predicted_drop exceeds COMPRESSION_GATE,
        otherwise None.
    """
    path = db_path or DB_PATH

    # Look up sector from target_companies
    with get_connection(path) as conn:
        row = conn.execute(
            "SELECT sector FROM target_companies WHERE target_id = ?",
            (prediction.target_id,),
        ).fetchone()
    sector = row["sector"] if row else "Unknown"

    eps_decay, terminal_pe = load_sector_defaults(sector, sector_defaults_path)

    projected_price = compute_projected_price(
        current_eps=prediction.current_eps,
        current_spot=prediction.current_spot,
        eps_decay=eps_decay,
        terminal_pe=terminal_pe,
    )

    if prediction.current_spot <= 0:
        logger.warning("Current spot is zero for %s -- cannot compute drop", prediction.ticker)
        return None

    predicted_drop = (prediction.current_spot - projected_price) / prediction.current_spot

    logger.info(
        "Ticker %s: projected_price=%.2f, predicted_drop=%.2f%% (gate=%.0f%%)",
        prediction.ticker,
        projected_price,
        predicted_drop * 100,
        COMPRESSION_GATE * 100,
    )

    # Update the prediction object
    prediction.eps_decay_pct = eps_decay
    prediction.terminal_pe = terminal_pe
    prediction.projected_price = projected_price
    prediction.predicted_drop_pct = predicted_drop

    # Persist to DB
    with get_connection(path) as conn:
        conn.execute(
            """
            UPDATE fundamental_predictions
            SET eps_decay_pct = ?, terminal_pe = ?,
                projected_price = ?, predicted_drop_pct = ?
            WHERE target_id = ?
            AND model_id = (
                SELECT MAX(model_id) FROM fundamental_predictions WHERE target_id = ?
            )
            """,
            (
                eps_decay,
                terminal_pe,
                projected_price,
                predicted_drop,
                prediction.target_id,
                prediction.target_id,
            ),
        )

    # Gate
    if predicted_drop <= COMPRESSION_GATE:
        logger.info(
            "Ticker %s predicted_drop %.2f%% below gate %.0f%% -- skipping",
            prediction.ticker,
            predicted_drop * 100,
            COMPRESSION_GATE * 100,
        )
        return None

    return prediction
