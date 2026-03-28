# tests/rangers/noah/tsunami/test_backtester.py
"""Tests for the Backtester pipeline stage."""

import sys
import os

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from rangers.noah.tsunami.pipeline.backtester import (
    FEATURE_NAMES,
    SEED_TICKERS,
    build_training_set,
    train_model,
    persist_weights,
    run_backtest,
    _compute_abnormal_return,
)
from rangers.noah.tsunami.db import init_db, get_connection


# ---------------------------------------------------------------------------
# Fake adapter
# ---------------------------------------------------------------------------

class FakeAdapter:
    """Stub DataAdapter that returns deterministic data for testing."""

    def __init__(self, financials_override: dict | None = None, n_prices: int = 300):
        self._financials_override = financials_override or {}
        self._n_prices = n_prices

    def _make_prices(self, seed: int = 0) -> pd.DataFrame:
        np.random.seed(seed)
        returns = np.random.normal(0.001, 0.02, self._n_prices)
        prices = [100.0]
        for r in returns:
            prices.append(prices[-1] * (1 + r))
        return pd.DataFrame({"Close": prices})

    def get_financials(self, ticker: str) -> dict:
        # Vary financials per ticker so the RF has feature variance to split on
        seed = abs(hash(ticker)) % 100
        np.random.seed(seed)
        base = {
            "sga_pct": float(np.random.uniform(0.20, 0.60)),
            "gross_margin_pct": float(np.random.uniform(0.30, 0.70)),
            "debt_to_equity": float(np.random.uniform(0.5, 3.0)),
            "fcf_yield_pct": float(np.random.uniform(-0.05, 0.05)),
            "roic_pct": float(np.random.uniform(0.01, 0.15)),
        }
        base.update(self._financials_override)
        return base

    def get_price(self, ticker: str) -> float:
        return 50.0

    def get_valuation(self, ticker: str) -> dict:
        return {"eps": 1.5, "pe": 20.0}

    def get_historical_prices(self, ticker: str, period: str = "2y") -> pd.DataFrame:
        seed = abs(hash(ticker)) % 1000
        return self._make_prices(seed)

    def get_options_chain(self, ticker: str, min_dte: int = 180) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "strike": [45.0, 50.0, 55.0],
                "bid": [3.0, 5.0, 8.0],
                "ask": [3.5, 5.5, 8.5],
                "volume": [100, 200, 150],
                "openInterest": [500, 800, 600],
                "impliedVolatility": [0.30, 0.30, 0.30],
                "expiry": ["2027-01-15", "2027-01-15", "2027-01-15"],
            }
        )


class ShortHistoryAdapter(FakeAdapter):
    """Returns fewer than 252 prices so abnormal return cannot be computed."""

    def get_historical_prices(self, ticker: str, period: str = "2y") -> pd.DataFrame:
        return pd.DataFrame({"Close": [100.0, 101.0, 99.0]})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return db_path


# ---------------------------------------------------------------------------
# Tests: constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_feature_names_length(self):
        assert len(FEATURE_NAMES) == 5

    def test_feature_names_content(self):
        expected = {"sga_pct", "gross_margin_pct", "debt_to_equity", "fcf_yield_pct", "roic_pct"}
        assert set(FEATURE_NAMES) == expected

    def test_seed_tickers_length(self):
        assert len(SEED_TICKERS) == 10


# ---------------------------------------------------------------------------
# Tests: _compute_abnormal_return
# ---------------------------------------------------------------------------

class TestComputeAbnormalReturn:
    def test_returns_float_with_sufficient_history(self):
        adapter = FakeAdapter(n_prices=300)
        result = _compute_abnormal_return(adapter, "CHGG")
        assert result is not None
        assert isinstance(result, float)

    def test_returns_none_with_insufficient_history(self):
        adapter = ShortHistoryAdapter()
        result = _compute_abnormal_return(adapter, "CHGG")
        assert result is None

    def test_returns_none_on_adapter_exception(self):
        class ErrorAdapter(FakeAdapter):
            def get_historical_prices(self, ticker: str, period: str = "2y") -> pd.DataFrame:
                raise RuntimeError("network error")

        adapter = ErrorAdapter()
        result = _compute_abnormal_return(adapter, "CHGG")
        assert result is None


# ---------------------------------------------------------------------------
# Tests: build_training_set
# ---------------------------------------------------------------------------

class TestBuildTrainingSet:
    def test_returns_dataframe_and_series(self):
        adapter = FakeAdapter()
        tickers = ["CHGG", "FVRR", "UPWK"]
        X, y = build_training_set(adapter, tickers)
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)

    def test_X_has_correct_columns(self):
        adapter = FakeAdapter()
        tickers = ["CHGG", "FVRR"]
        X, y = build_training_set(adapter, tickers)
        assert list(X.columns) == FEATURE_NAMES

    def test_X_and_y_same_length(self):
        adapter = FakeAdapter()
        tickers = ["CHGG", "FVRR", "UPWK"]
        X, y = build_training_set(adapter, tickers)
        assert len(X) == len(y)

    def test_raises_when_no_valid_data(self):
        adapter = ShortHistoryAdapter()
        with pytest.raises(ValueError, match="No valid training data"):
            build_training_set(adapter, ["CHGG"])

    def test_fills_missing_feature_values(self):
        adapter = FakeAdapter(financials_override={"sga_pct": None})
        tickers = ["CHGG", "FVRR", "UPWK"]
        X, y = build_training_set(adapter, tickers)
        assert not X["sga_pct"].isna().any()


# ---------------------------------------------------------------------------
# Tests: train_model
# ---------------------------------------------------------------------------

class TestTrainModel:
    def _make_data(self, n: int = 15):
        np.random.seed(42)
        X = pd.DataFrame(
            np.random.rand(n, len(FEATURE_NAMES)),
            columns=FEATURE_NAMES,
        )
        y = pd.Series(np.random.uniform(-0.5, 0.2, n))
        return X, y

    def test_returns_three_items(self):
        X, y = self._make_data()
        result = train_model(X, y)
        assert len(result) == 3

    def test_weights_sum_to_one(self):
        X, y = self._make_data()
        _, weights, _ = train_model(X, y)
        assert abs(sum(weights.values()) - 1.0) < 1e-6

    def test_weights_keys_match_feature_names(self):
        X, y = self._make_data()
        _, weights, _ = train_model(X, y)
        assert set(weights.keys()) == set(FEATURE_NAMES)

    def test_r_squared_is_float(self):
        X, y = self._make_data()
        _, _, r_squared = train_model(X, y)
        assert isinstance(r_squared, float)

    def test_single_sample_r_squared_is_zero(self):
        X = pd.DataFrame([[0.3, 0.5, 1.2, -0.01, 0.05]], columns=FEATURE_NAMES)
        y = pd.Series([-0.3])
        _, _, r_squared = train_model(X, y)
        assert r_squared == 0.0


# ---------------------------------------------------------------------------
# Tests: persist_weights
# ---------------------------------------------------------------------------

class TestPersistWeights:
    def test_rows_inserted(self, test_db):
        weights = {feat: 0.2 for feat in FEATURE_NAMES}
        persist_weights(weights, r_squared=0.72, db_path=test_db)
        with get_connection(test_db) as conn:
            rows = conn.execute("SELECT * FROM model_weights").fetchall()
        assert len(rows) == len(FEATURE_NAMES)

    def test_correct_feature_names_stored(self, test_db):
        weights = {feat: 0.2 for feat in FEATURE_NAMES}
        persist_weights(weights, r_squared=0.72, db_path=test_db)
        with get_connection(test_db) as conn:
            rows = conn.execute("SELECT feature_name FROM model_weights").fetchall()
        stored = {row["feature_name"] for row in rows}
        assert stored == set(FEATURE_NAMES)

    def test_r_squared_stored(self, test_db):
        weights = {feat: 0.2 for feat in FEATURE_NAMES}
        persist_weights(weights, r_squared=0.80, db_path=test_db)
        with get_connection(test_db) as conn:
            rows = conn.execute("SELECT r_squared FROM model_weights").fetchall()
        for row in rows:
            assert abs(row["r_squared"] - 0.80) < 1e-6

    def test_multiple_calls_append_rows(self, test_db):
        weights = {feat: 0.2 for feat in FEATURE_NAMES}
        persist_weights(weights, r_squared=0.70, db_path=test_db)
        persist_weights(weights, r_squared=0.75, db_path=test_db)
        with get_connection(test_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM model_weights").fetchone()[0]
        assert count == len(FEATURE_NAMES) * 2


# ---------------------------------------------------------------------------
# Tests: run_backtest (integration)
# ---------------------------------------------------------------------------

class TestRunBacktest:
    def test_returns_weights_and_r_squared(self, test_db):
        adapter = FakeAdapter()
        tickers = ["CHGG", "FVRR", "UPWK", "TASK", "TWOU"]
        weights, r_squared = run_backtest(adapter, tickers=tickers, db_path=test_db)
        assert isinstance(weights, dict)
        assert isinstance(r_squared, float)

    def test_weights_persisted_after_run(self, test_db):
        adapter = FakeAdapter()
        tickers = ["CHGG", "FVRR", "UPWK"]
        run_backtest(adapter, tickers=tickers, db_path=test_db)
        with get_connection(test_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM model_weights").fetchone()[0]
        assert count == len(FEATURE_NAMES)

    def test_weights_sum_to_one(self, test_db):
        adapter = FakeAdapter()
        # Use enough tickers so RF importances are non-trivial
        tickers = ["CHGG", "FVRR", "UPWK", "TASK", "TWOU", "SSTK", "EPAM"]
        weights, _ = run_backtest(adapter, tickers=tickers, db_path=test_db)
        total = sum(weights.values())
        # sklearn RF importances sum to 1.0 when there is variance to split on;
        # allow 0.0 only if every importance is 0 (degenerate constant-target case)
        assert abs(total - 1.0) < 1e-6 or total == 0.0
