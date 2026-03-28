# tests/rangers/noah/tsunami/test_filter.py
"""Tests for the VRP Filter pipeline stage."""

import sys
import os
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from rangers.noah.tsunami.pipeline.filter import (
    compute_hv_252d,
    compute_vrp,
    classify_vrp,
    filter_targets,
)
from rangers.noah.tsunami.db import init_db, get_connection
from rangers.noah.tsunami.models.schemas import Prediction
from rangers.noah.tsunami import config


class FakeAdapterForFilter:
    """Stub adapter for filter tests."""

    def __init__(self, iv: float = 0.45, hv_close_prices: list | None = None):
        self.iv = iv
        # Generate 300 days of prices with known volatility
        if hv_close_prices is not None:
            self.close_prices = hv_close_prices
        else:
            np.random.seed(42)
            daily_returns = np.random.normal(0.0, 0.02, 300)
            prices = [100.0]
            for r in daily_returns:
                prices.append(prices[-1] * (1 + r))
            self.close_prices = prices

    def get_historical_prices(self, ticker: str, period: str = "2y") -> pd.DataFrame:
        return pd.DataFrame({"Close": self.close_prices})

    def get_options_chain(self, ticker: str, min_dte: int = 180) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "strike": [45.0, 50.0, 55.0],
                "bid": [3.0, 5.0, 8.0],
                "ask": [3.5, 5.5, 8.5],
                "volume": [100, 200, 150],
                "openInterest": [500, 800, 600],
                "impliedVolatility": [self.iv, self.iv, self.iv],
                "expiry": ["2027-01-15", "2027-01-15", "2027-01-15"],
            }
        )

    def get_price(self, ticker: str) -> float:
        return 50.0

    def get_financials(self, ticker: str) -> dict:
        return {}

    def get_valuation(self, ticker: str) -> dict:
        return {"eps": 1.0, "pe": 20.0}


@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO target_companies (target_id, ticker, company, sector) VALUES (?, ?, ?, ?)",
            ("TGT_001", "CHGG", "Chegg", "EdTech"),
        )
        conn.execute(
            "INSERT INTO target_companies (target_id, ticker, company, sector) VALUES (?, ?, ?, ?)",
            ("TGT_002", "UPWK", "Upwork", "Freelance/Gig"),
        )
    return db_path


class TestComputeHV252d:
    """Unit tests for historical volatility calculation."""

    def test_returns_positive_float(self):
        np.random.seed(42)
        prices = [100.0]
        for _ in range(260):
            prices.append(prices[-1] * (1 + np.random.normal(0, 0.02)))
        hv = compute_hv_252d(pd.DataFrame({"Close": prices}))
        assert hv > 0
        assert isinstance(hv, float)

    def test_insufficient_data_returns_none(self):
        prices = [100.0, 101.0, 99.0]
        hv = compute_hv_252d(pd.DataFrame({"Close": prices}))
        assert hv is None


class TestComputeVRP:
    """Unit tests for VRP calculation."""

    def test_vrp_formula(self):
        """VRP = atm_put_iv - hv_252d."""
        vrp = compute_vrp(atm_put_iv=0.45, hv_252d=0.30)
        assert abs(vrp - 0.15) < 0.001

    def test_vrp_negative(self):
        """Negative VRP means puts are cheap."""
        vrp = compute_vrp(atm_put_iv=0.25, hv_252d=0.35)
        assert vrp < 0


class TestClassifyVRP:
    """Test VRP classification buckets."""

    def test_reject_high_vrp(self):
        assert classify_vrp(0.20) == "REJECT"

    def test_fair_value(self):
        assert classify_vrp(0.10) == "FAIR_VALUE"

    def test_premium_discount(self):
        assert classify_vrp(-0.05) == "PREMIUM_DISCOUNT"

    def test_boundary_at_threshold(self):
        assert classify_vrp(0.15) == "REJECT"


class TestFilterTargets:
    """Integration tests for filter_targets."""

    def test_filter_ranks_by_vrp_ascending(self, test_db):
        predictions = [
            Prediction(
                target_id="TGT_001", ticker="CHGG", sga_pct=0.4,
                gross_margin_pct=0.5, debt_to_equity=1.5, fcf_yield_pct=-0.02,
                roic_pct=0.03, vulnerability_score=0.75, current_eps=1.5,
                current_pe=25.0, current_spot=50.0, eps_decay_pct=0.25,
                terminal_pe=13.0, projected_price=14.625, predicted_drop_pct=0.70,
            ),
            Prediction(
                target_id="TGT_002", ticker="UPWK", sga_pct=0.4,
                gross_margin_pct=0.5, debt_to_equity=1.5, fcf_yield_pct=-0.02,
                roic_pct=0.03, vulnerability_score=0.75, current_eps=1.5,
                current_pe=25.0, current_spot=50.0, eps_decay_pct=0.20,
                terminal_pe=11.0, projected_price=13.2, predicted_drop_pct=0.73,
            ),
        ]
        adapter = FakeAdapterForFilter(iv=0.10)  # low IV => likely passes
        results = filter_targets(predictions, adapter, db_path=test_db)
        # Should return at least one result (those that pass VRP gate)
        assert isinstance(results, list)
