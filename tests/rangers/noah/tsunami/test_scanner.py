# tests/rangers/noah/tsunami/test_scanner.py
"""Tests for the Scanner pipeline stage."""

import sys
import os
import sqlite3

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from rangers.noah.tsunami.pipeline.scanner import scan_ticker, compute_vulnerability_score
from rangers.noah.tsunami.db import init_db, get_connection
from rangers.noah.tsunami import config


class FakeAdapter:
    """Stub adapter returning controlled data for testing."""

    def __init__(
        self,
        financials: dict | None = None,
        price: float = 50.0,
        valuation: dict | None = None,
    ):
        self.financials_data = financials or {
            "sga_pct": 0.45,
            "gross_margin_pct": 0.55,
            "debt_to_equity": 1.8,
            "fcf_yield_pct": -0.02,
            "roic_pct": 0.03,
        }
        self.price_val = price
        self.valuation_data = valuation or {"eps": 1.50, "pe": 25.0}

    def get_financials(self, ticker: str) -> dict:
        return self.financials_data

    def get_price(self, ticker: str) -> float:
        return self.price_val

    def get_valuation(self, ticker: str) -> dict:
        return self.valuation_data

    def get_historical_prices(self, ticker, period="2y"):
        import pandas as pd
        return pd.DataFrame()

    def get_options_chain(self, ticker, min_dte=180):
        import pandas as pd
        return pd.DataFrame()


@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO target_companies (target_id, ticker, company, sector) VALUES (?, ?, ?, ?)",
            ("TGT_001", "CHGG", "Chegg", "EdTech"),
        )
    return db_path


class TestComputeVulnerabilityScore:
    """Unit tests for the scoring function."""

    def test_equal_weights_high_vulnerability(self):
        """High SGA, low margin, high debt, negative FCF, low ROIC => high score."""
        weights = config.DEFAULT_FEATURE_WEIGHTS
        financials = {
            "sga_pct": 0.50,
            "gross_margin_pct": 0.40,
            "debt_to_equity": 2.0,
            "fcf_yield_pct": -0.05,
            "roic_pct": 0.02,
        }
        score = compute_vulnerability_score(financials, weights)
        assert 0.0 <= score <= 1.0
        assert score > 0.6, f"Expected vulnerable company score > 0.6, got {score}"

    def test_equal_weights_low_vulnerability(self):
        """Low SGA, high margin, low debt, high FCF, high ROIC => low score."""
        weights = config.DEFAULT_FEATURE_WEIGHTS
        financials = {
            "sga_pct": 0.10,
            "gross_margin_pct": 0.80,
            "debt_to_equity": 0.3,
            "fcf_yield_pct": 0.08,
            "roic_pct": 0.20,
        }
        score = compute_vulnerability_score(financials, weights)
        assert 0.0 <= score <= 1.0
        assert score < 0.4, f"Expected strong company score < 0.4, got {score}"

    def test_score_bounded_zero_one(self):
        """Score must always be clamped between 0 and 1."""
        weights = config.DEFAULT_FEATURE_WEIGHTS
        extreme = {
            "sga_pct": 1.0,
            "gross_margin_pct": 0.0,
            "debt_to_equity": 10.0,
            "fcf_yield_pct": -1.0,
            "roic_pct": -0.5,
        }
        score = compute_vulnerability_score(extreme, weights)
        assert 0.0 <= score <= 1.0

    def test_missing_metric_uses_neutral(self):
        """None values should default to neutral (0.5 contribution)."""
        weights = config.DEFAULT_FEATURE_WEIGHTS
        partial = {
            "sga_pct": None,
            "gross_margin_pct": 0.55,
            "debt_to_equity": None,
            "fcf_yield_pct": -0.02,
            "roic_pct": 0.03,
        }
        score = compute_vulnerability_score(partial, weights)
        assert 0.0 <= score <= 1.0


class TestScanTicker:
    """Integration tests for scan_ticker."""

    def test_scan_returns_prediction_above_gate(self, test_db):
        """A vulnerable ticker should produce a prediction above the gate."""
        adapter = FakeAdapter()
        result = scan_ticker("CHGG", adapter, db_path=test_db)
        assert result is not None
        assert result.vulnerability_score > config.VULNERABILITY_GATE

    def test_scan_persists_to_db(self, test_db):
        """Scan results should be written to fundamental_predictions."""
        adapter = FakeAdapter()
        scan_ticker("CHGG", adapter, db_path=test_db)
        with get_connection(test_db) as conn:
            row = conn.execute(
                "SELECT * FROM fundamental_predictions WHERE target_id = 'TGT_001'"
            ).fetchone()
        assert row is not None
        assert row["vulnerability_score"] > 0

    def test_scan_below_gate_returns_none(self, test_db):
        """A strong company should not pass the vulnerability gate."""
        adapter = FakeAdapter(
            financials={
                "sga_pct": 0.10,
                "gross_margin_pct": 0.80,
                "debt_to_equity": 0.3,
                "fcf_yield_pct": 0.08,
                "roic_pct": 0.20,
            }
        )
        result = scan_ticker("CHGG", adapter, db_path=test_db)
        assert result is None
