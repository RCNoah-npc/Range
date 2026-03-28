# src/rangers/noah/tsunami/pipeline/backtester.py
"""Stage 3: Backtester -- trains on historical casualties to derive feature weights.

Uses Random Forest only (n=1000, max_depth=5).  OLS is omitted because
10 training samples with 5 features leaves only 4 degrees of freedom,
making p-values unreliable.
"""

from __future__ import annotations

import csv
import logging
from datetime import datetime
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score

from ..adapters.base import DataAdapter
from ..config import CASUALTIES_PATH, DB_PATH
from ..db import get_connection, init_db

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "sga_pct",
    "gross_margin_pct",
    "debt_to_equity",
    "fcf_yield_pct",
    "roic_pct",
]

SEED_TICKERS = [
    "CHGG", "FVRR", "UPWK", "TEP.PA", "TASK",
    "SSTK", "TWOU", "GETY", "EPAM", "COUR",
]


def _compute_abnormal_return(
    adapter: DataAdapter, ticker: str, period: str = "2y"
) -> float | None:
    """Compute 12-month abnormal return relative to S&P 500.

    Returns the difference between the ticker's 12-month return and
    SPY's 12-month return over the same period.
    """
    try:
        hist = adapter.get_historical_prices(ticker, period)
        spy_hist = adapter.get_historical_prices("SPY", period)
    except Exception as exc:
        logger.warning("Cannot fetch history for %s: %s", ticker, exc)
        return None

    if hist.empty or spy_hist.empty or len(hist) < 252 or len(spy_hist) < 252:
        logger.warning("Insufficient history for %s", ticker)
        return None

    # Use the last 252 trading days
    ticker_return = (hist["Close"].iloc[-1] / hist["Close"].iloc[-252]) - 1.0
    spy_return = (spy_hist["Close"].iloc[-1] / spy_hist["Close"].iloc[-252]) - 1.0

    return ticker_return - spy_return


def build_training_set(
    adapter: DataAdapter,
    tickers: list[str] | None = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Build the feature matrix X and target vector y from casualties.

    Parameters
    ----------
    adapter : DataAdapter
        Financial data source.
    tickers : list[str], optional
        Override the seed tickers list.

    Returns
    -------
    X : pd.DataFrame with columns = FEATURE_NAMES
    y : pd.Series of Abnormal_Return_12M
    """
    tickers = tickers or SEED_TICKERS
    rows = []

    for ticker in tickers:
        try:
            financials = adapter.get_financials(ticker)
        except Exception as exc:
            logger.warning("Skipping %s (financials): %s", ticker, exc)
            continue

        abnormal_return = _compute_abnormal_return(adapter, ticker)
        if abnormal_return is None:
            logger.warning("Skipping %s (no abnormal return)", ticker)
            continue

        row = {feat: financials.get(feat) for feat in FEATURE_NAMES}
        row["abnormal_return"] = abnormal_return
        row["ticker"] = ticker
        rows.append(row)

    if not rows:
        raise ValueError("No valid training data collected")

    df = pd.DataFrame(rows)
    logger.info("Training set: %d samples from %d tickers", len(df), len(tickers))

    # Fill missing values with column medians
    for feat in FEATURE_NAMES:
        if df[feat].isna().any():
            median_val = df[feat].median()
            fill_val = median_val if pd.notna(median_val) else 0.0
            df[feat] = df[feat].fillna(fill_val)

    X = df[FEATURE_NAMES]
    y = df["abnormal_return"]
    return X, y


def train_model(
    X: pd.DataFrame, y: pd.Series
) -> Tuple[RandomForestRegressor, dict[str, float], float]:
    """Train Random Forest and extract feature importances.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    y : pd.Series
        Target variable (abnormal return).

    Returns
    -------
    model : RandomForestRegressor
    weights : dict[str, float]
        Feature name -> importance (sums to 1.0).
    r_squared : float
        Mean R-squared from leave-one-out or 3-fold CV (whichever is
        appropriate for sample size).
    """
    model = RandomForestRegressor(
        n_estimators=1000,
        max_depth=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    # Feature importances (already normalized to sum=1 by sklearn)
    importances = model.feature_importances_
    weights = {name: float(imp) for name, imp in zip(FEATURE_NAMES, importances)}

    # Cross-validation R-squared
    n_splits = min(3, len(X))
    if n_splits < 2:
        r_squared = 0.0
    else:
        cv_scores = cross_val_score(model, X, y, cv=n_splits, scoring="r2")
        r_squared = float(np.mean(cv_scores))

    logger.info("Random Forest R-squared: %.4f", r_squared)
    if r_squared < 0.60:
        logger.warning(
            "R-squared %.4f is below 0.60 -- consider adding/pruning features",
            r_squared,
        )
    elif r_squared >= 0.75:
        logger.info("Model quality gate PASSED (R^2 >= 0.75)")
    else:
        logger.info(
            "R-squared %.4f is acceptable but below 0.75 quality gate", r_squared
        )

    return model, weights, r_squared


def persist_weights(
    weights: dict[str, float], r_squared: float, db_path: str | None = None
) -> None:
    """Save feature weights to the model_weights table.

    Inserts a new row for each feature with the current timestamp,
    so historical weight evolution is preserved.
    """
    path = db_path or DB_PATH
    now = datetime.utcnow().isoformat()

    with get_connection(path) as conn:
        for feature_name, weight_pct in weights.items():
            conn.execute(
                """
                INSERT INTO model_weights (created_at, feature_name, weight_pct, r_squared)
                VALUES (?, ?, ?, ?)
                """,
                (now, feature_name, weight_pct, r_squared),
            )

    logger.info("Persisted %d feature weights to model_weights table", len(weights))


def run_backtest(
    adapter: DataAdapter,
    tickers: list[str] | None = None,
    db_path: str | None = None,
) -> Tuple[dict[str, float], float]:
    """Full backtest pipeline: build training set, train, persist.

    Parameters
    ----------
    adapter : DataAdapter
        Financial data source.
    tickers : list[str], optional
        Override the seed tickers.
    db_path : str, optional
        Override database path.

    Returns
    -------
    weights : dict[str, float]
    r_squared : float
    """
    X, y = build_training_set(adapter, tickers)
    model, weights, r_squared = train_model(X, y)
    persist_weights(weights, r_squared, db_path)

    logger.info("Backtest complete. Weights: %s", weights)
    return weights, r_squared
