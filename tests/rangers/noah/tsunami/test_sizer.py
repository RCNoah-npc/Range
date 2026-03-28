# tests/rangers/noah/tsunami/test_sizer.py
"""Tests for the Kelly Sizer pipeline stage."""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from rangers.noah.tsunami.pipeline.sizer import (
    compute_kelly,
    compute_payoff_ratio,
    size_position,
)
from rangers.noah.tsunami.models.schemas import Prediction, FrictionData, Signal
from rangers.noah.tsunami import config


class TestComputePayoffRatio:
    """Unit tests for payoff ratio calculation."""

    def test_positive_payoff(self):
        """Intrinsic exceeds premium => positive payoff ratio."""
        # strike 40, projected 10, premium 5 => intrinsic=30, b=(30-5)/5=5.0
        b = compute_payoff_ratio(
            projected_price=10.0, strike=40.0, premium=5.0
        )
        assert abs(b - 5.0) < 0.01

    def test_zero_premium_returns_zero(self):
        b = compute_payoff_ratio(projected_price=10.0, strike=40.0, premium=0.0)
        assert b == 0.0

    def test_otm_at_target(self):
        """If projected_price > strike, intrinsic is 0."""
        b = compute_payoff_ratio(projected_price=50.0, strike=40.0, premium=5.0)
        assert b == -1.0  # (0 - 5) / 5 = -1


class TestComputeKelly:
    """Unit tests for the Kelly fraction calculation."""

    def test_standard_kelly(self):
        """p=0.55, b=5.0 => f=0.55 - 0.45/5.0 = 0.55-0.09 = 0.46."""
        f_full = compute_kelly(p=0.55, b=5.0)
        assert abs(f_full - 0.46) < 0.01

    def test_negative_ev_returns_zero(self):
        """If f_full <= 0, the trade has negative expected value."""
        f_full = compute_kelly(p=0.30, b=1.0)
        # f = 0.30 - 0.70/1.0 = -0.40
        assert f_full <= 0

    def test_even_odds(self):
        """p=0.5, b=1.0 => f = 0.5 - 0.5/1.0 = 0.0."""
        f_full = compute_kelly(p=0.5, b=1.0)
        assert abs(f_full) < 0.01


class TestSizePosition:
    """Integration tests for size_position."""

    def test_size_with_quarter_kelly_and_cap(self):
        """Quarter-Kelly with 10% cap."""
        pred = Prediction(
            target_id="TGT_001", ticker="CHGG", sga_pct=0.4,
            gross_margin_pct=0.5, debt_to_equity=1.5, fcf_yield_pct=-0.02,
            roic_pct=0.03, vulnerability_score=0.75, current_eps=1.5,
            current_pe=25.0, current_spot=50.0, eps_decay_pct=0.25,
            terminal_pe=13.0, projected_price=14.625, predicted_drop_pct=0.70,
        )
        friction = FrictionData(
            target_id="TGT_001", ticker="CHGG", live_spot=50.0,
            atm_put_iv=0.40, put_call_ratio=1.0, est_premium_ask=5.0,
            hv_252d=0.30, vrp_spread=0.10,
        )
        signal = size_position(
            pred, friction, portfolio_value=100000.0, win_prob=0.55
        )
        assert signal is not None
        assert signal.kelly_pct > 0
        assert signal.kelly_pct <= config.MAX_POSITION_PCT
        assert signal.capital_to_deploy > 0
        assert signal.capital_to_deploy <= 100000.0 * config.MAX_POSITION_PCT

    def test_reject_negative_ev(self):
        """If payoff ratio is too low, Kelly is negative => reject."""
        pred = Prediction(
            target_id="TGT_001", ticker="CHGG", sga_pct=0.4,
            gross_margin_pct=0.5, debt_to_equity=1.5, fcf_yield_pct=-0.02,
            roic_pct=0.03, vulnerability_score=0.75, current_eps=1.5,
            current_pe=25.0, current_spot=50.0, eps_decay_pct=0.05,
            terminal_pe=30.0, projected_price=42.75, predicted_drop_pct=0.145,
        )
        friction = FrictionData(
            target_id="TGT_001", ticker="CHGG", live_spot=50.0,
            atm_put_iv=0.40, put_call_ratio=1.0, est_premium_ask=15.0,
            hv_252d=0.30, vrp_spread=0.10,
        )
        signal = size_position(
            pred, friction, portfolio_value=100000.0, win_prob=0.30
        )
        assert signal is None
