"""Smoke test: end-to-end pipeline against CHGG with fake adapter."""

import sys
import os
import json

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from rangers.noah.tsunami.db import init_db, get_connection
from rangers.noah.tsunami.pipeline.scanner import scan_ticker
from rangers.noah.tsunami.pipeline.compressor import compress
from rangers.noah.tsunami.pipeline.filter import filter_targets
from rangers.noah.tsunami.pipeline.sizer import size_all
from rangers.noah.tsunami.pipeline.underwriter import underwrite_all
from rangers.noah.tsunami import config


class FakeCHGGAdapter:
    """Fake adapter returning realistic CHGG-like data."""

    def get_financials(self, ticker: str) -> dict:
        return {
            "sga_pct": 0.48,
            "gross_margin_pct": 0.50,
            "debt_to_equity": 2.1,
            "fcf_yield_pct": -0.03,
            "roic_pct": 0.02,
        }

    def get_price(self, ticker: str) -> float:
        return 9.50

    def get_valuation(self, ticker: str) -> dict:
        return {"eps": -0.80, "pe": 0.0}

    def get_historical_prices(self, ticker: str, period: str = "2y") -> pd.DataFrame:
        np.random.seed(42)
        n = 300
        returns = np.random.normal(-0.001, 0.03, n)
        prices = [50.0]
        for r in returns:
            prices.append(max(0.5, prices[-1] * (1 + r)))
        return pd.DataFrame({"Close": prices})

    def get_options_chain(self, ticker: str, min_dte: int = 180) -> pd.DataFrame:
        future_date = (datetime.utcnow() + timedelta(days=240)).strftime("%Y-%m-%d")
        return pd.DataFrame({
            "strike": [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "bid": [5.5, 4.5, 3.5, 2.5, 1.8, 1.0, 0.5, 0.2],
            "ask": [6.0, 5.0, 4.0, 3.0, 2.2, 1.5, 0.8, 0.4],
            "volume": [50, 100, 200, 300, 400, 300, 200, 100],
            "openInterest": [200, 400, 800, 1200, 1500, 1000, 600, 300],
            "impliedVolatility": [0.55, 0.50, 0.48, 0.45, 0.42, 0.40, 0.38, 0.35],
            "expiry": [future_date] * 8,
        })


@pytest.fixture
def smoke_env(tmp_path):
    db_path = str(tmp_path / "smoke.db")
    init_db(db_path)

    # Seed CHGG
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO target_companies (target_id, ticker, company, sector) VALUES (?, ?, ?, ?)",
            ("TGT_001", "CHGG", "Chegg", "EdTech"),
        )

    # Write sector defaults
    defaults_path = str(tmp_path / "sector_defaults.json")
    with open(defaults_path, "w") as f:
        json.dump({
            "EdTech": {"eps_decay": 0.30, "terminal_pe": 13.0},
        }, f)

    return db_path, defaults_path


class TestCHGGSmoke:
    """End-to-end smoke test against CHGG."""

    def test_full_pipeline(self, smoke_env):
        db_path, defaults_path = smoke_env
        adapter = FakeCHGGAdapter()

        # Stage 1: Scan
        prediction = scan_ticker("CHGG", adapter, db_path=db_path)
        assert prediction is not None, "CHGG should pass vulnerability gate"
        assert prediction.vulnerability_score > config.VULNERABILITY_GATE

        # Stage 2: Compress (CHGG has negative EPS => percentage haircut)
        compressed = compress(prediction, db_path=db_path, sector_defaults_path=defaults_path)
        assert compressed is not None, "CHGG should pass compression gate"
        assert compressed.predicted_drop_pct > config.COMPRESSION_GATE
        # Negative EPS: projected = 9.50 * (1 - 0.30) = 6.65
        # drop = (9.50 - 6.65) / 9.50 = 0.30
        assert compressed.predicted_drop_pct >= 0.25

        # Stage 4: Filter
        filtered = filter_targets([compressed], adapter, db_path=db_path)
        assert len(filtered) > 0, "CHGG should pass VRP filter with fake IV"

        # Stage 5: Size
        signals = size_all(filtered, portfolio_value=100000.0)
        assert len(signals) > 0, "CHGG should have positive Kelly allocation"
        assert signals[0].kelly_pct > 0
        assert signals[0].kelly_pct <= config.MAX_POSITION_PCT

        # Stage 6: Underwrite
        execution_matrix = underwrite_all(signals, adapter, db_path=db_path)
        assert len(execution_matrix) > 0, "Should produce at least one execution row"

        row = execution_matrix[0]
        assert row.ticker == "CHGG"
        assert row.contracts > 0
        assert row.strike > 0
        assert row.decision in ("EXECUTE", "REJECT")

        # Verify DB persistence
        with get_connection(db_path) as conn:
            pred_row = conn.execute(
                "SELECT * FROM fundamental_predictions WHERE target_id = 'TGT_001'"
            ).fetchone()
            assert pred_row is not None
            assert pred_row["vulnerability_score"] > 0

            friction_row = conn.execute(
                "SELECT * FROM market_friction_log WHERE target_id = 'TGT_001'"
            ).fetchone()
            assert friction_row is not None
            assert friction_row["vrp_spread"] is not None
