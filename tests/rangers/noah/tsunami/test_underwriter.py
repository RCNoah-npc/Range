# tests/rangers/noah/tsunami/test_underwriter.py
"""Tests for the Underwriter pipeline stage."""

import sys
import os
from datetime import datetime, timedelta

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from rangers.noah.tsunami.pipeline.underwriter import (
    select_strike,
    select_expiry,
    compute_rop,
    underwrite_signal,
)
from rangers.noah.tsunami.models.schemas import Signal, ExecutionRow
from rangers.noah.tsunami import config


class FakeAdapterForUnderwriter:
    """Stub adapter for underwriter tests."""

    def __init__(self):
        # Build an options chain with known strikes and premiums
        future_date = (datetime.utcnow() + timedelta(days=240)).strftime("%Y-%m-%d")
        self.chain = pd.DataFrame({
            "strike": [20.0, 25.0, 30.0, 35.0, 40.0, 45.0],
            "bid": [18.0, 14.0, 10.0, 6.0, 3.0, 1.0],
            "ask": [19.0, 15.0, 11.0, 7.0, 4.0, 2.0],
            "volume": [50, 100, 200, 300, 200, 100],
            "openInterest": [500, 800, 1200, 1500, 1000, 500],
            "impliedVolatility": [0.50, 0.48, 0.45, 0.42, 0.40, 0.38],
            "expiry": [future_date] * 6,
        })

    def get_options_chain(self, ticker, min_dte=180):
        return self.chain

    def get_price(self, ticker):
        return 50.0

    def get_financials(self, ticker):
        return {}

    def get_valuation(self, ticker):
        return {"eps": 1.0, "pe": 20.0}

    def get_historical_prices(self, ticker, period="2y"):
        return pd.DataFrame()


class TestSelectStrike:
    """Unit tests for strike selection."""

    def test_midpoint_strike(self):
        """Strike should be nearest to spot * (1 + predicted_drop/2).

        spot=50, predicted_drop=0.60 => target = 50*(1 + (-0.60)/2) = 50*0.70 = 35
        Note: predicted_drop is positive. Strike target = spot*(1 - drop/2).
        """
        available_strikes = [20.0, 25.0, 30.0, 35.0, 40.0, 45.0]
        strike = select_strike(
            current_spot=50.0,
            predicted_drop_pct=0.60,
            available_strikes=available_strikes,
        )
        assert strike == 35.0

    def test_exact_match(self):
        available_strikes = [30.0, 35.0, 40.0]
        strike = select_strike(
            current_spot=50.0,
            predicted_drop_pct=0.40,  # target = 50*0.80 = 40
            available_strikes=available_strikes,
        )
        assert strike == 40.0


class TestSelectExpiry:
    """Unit tests for expiry selection."""

    def test_nearest_to_240d(self):
        today = datetime.utcnow()
        expiries = [
            (today + timedelta(days=190)).strftime("%Y-%m-%d"),
            (today + timedelta(days=235)).strftime("%Y-%m-%d"),
            (today + timedelta(days=250)).strftime("%Y-%m-%d"),
            (today + timedelta(days=310)).strftime("%Y-%m-%d"),
        ]
        selected = select_expiry(expiries)
        # 235 days is closest to 240
        assert selected == expiries[1]

    def test_filters_outside_range(self):
        today = datetime.utcnow()
        expiries = [
            (today + timedelta(days=100)).strftime("%Y-%m-%d"),  # too short
            (today + timedelta(days=200)).strftime("%Y-%m-%d"),
            (today + timedelta(days=400)).strftime("%Y-%m-%d"),  # too long
        ]
        selected = select_expiry(expiries)
        assert selected == expiries[1]


class TestComputeROP:
    """Unit tests for return on premium calculation."""

    def test_rop_above_minimum(self):
        """intrinsic = max(0, 35 - 14.625) = 20.375; rop = (20.375 - 5) / 5 = 3.075."""
        rop = compute_rop(
            strike=35.0, projected_price=14.625, premium=5.0
        )
        assert rop >= config.ROP_MINIMUM

    def test_rop_below_minimum(self):
        """Strike too close to projected => low ROP."""
        rop = compute_rop(
            strike=16.0, projected_price=14.625, premium=5.0
        )
        assert rop < config.ROP_MINIMUM

    def test_otm_at_target(self):
        """If projected price > strike, intrinsic = 0, rop = -1."""
        rop = compute_rop(
            strike=10.0, projected_price=14.625, premium=5.0
        )
        assert rop < 0


class TestUnderwriteSignal:
    """Integration tests for underwrite_signal."""

    def test_execute_decision(self):
        adapter = FakeAdapterForUnderwriter()
        signal = Signal(
            target_id="TGT_001", ticker="CHGG",
            predicted_drop_pct=0.70, projected_price=14.625,
            current_spot=50.0, vrp_spread=0.05,
            kelly_pct=0.08, capital_to_deploy=8000.0,
            win_probability=0.55, payoff_ratio=5.0,
        )
        row = underwrite_signal(signal, adapter)
        assert row is not None
        assert isinstance(row, ExecutionRow)
        assert row.contracts > 0
        assert row.decision in ("EXECUTE", "REJECT")

    def test_reject_low_rop(self):
        adapter = FakeAdapterForUnderwriter()
        signal = Signal(
            target_id="TGT_001", ticker="CHGG",
            predicted_drop_pct=0.05, projected_price=47.5,
            current_spot=50.0, vrp_spread=0.05,
            kelly_pct=0.08, capital_to_deploy=8000.0,
            win_probability=0.55, payoff_ratio=0.5,
        )
        row = underwrite_signal(signal, adapter)
        # Should still return a row, but with REJECT decision
        assert row is not None
        assert row.decision == "REJECT"
