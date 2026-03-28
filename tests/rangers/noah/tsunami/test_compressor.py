# tests/rangers/noah/tsunami/test_compressor.py
"""Tests for the Compressor pipeline stage."""

import sys
import os
import json

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from rangers.noah.tsunami.pipeline.compressor import (
    compress,
    load_sector_defaults,
    compute_projected_price,
)
from rangers.noah.tsunami.models.schemas import Prediction
from rangers.noah.tsunami.db import init_db, get_connection
from rangers.noah.tsunami import config


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


@pytest.fixture
def sector_defaults_file(tmp_path):
    defaults = {
        "EdTech": {"eps_decay": 0.25, "terminal_pe": 13.0},
        "IT Services": {"eps_decay": 0.10, "terminal_pe": 14.0},
    }
    path = tmp_path / "sector_defaults.json"
    path.write_text(json.dumps(defaults))
    return str(path)


class TestComputeProjectedPrice:
    """Unit tests for the projection formula."""

    def test_positive_eps_compression(self):
        """Standard case: positive EPS with multiple compression."""
        # EPS=5.0, decay=25%, terminal_PE=13 => projected = 5.0*0.75*13 = 48.75
        proj = compute_projected_price(
            current_eps=5.0,
            current_spot=100.0,
            eps_decay=0.25,
            terminal_pe=13.0,
        )
        assert abs(proj - 48.75) < 0.01

    def test_negative_eps_fallback(self):
        """Negative EPS: fall back to revenue-based percentage haircut."""
        # current_spot=20.0, decay=25% => projected = 20.0 * (1 - 0.25) = 15.0
        proj = compute_projected_price(
            current_eps=-1.5,
            current_spot=20.0,
            eps_decay=0.25,
            terminal_pe=13.0,
        )
        assert abs(proj - 15.0) < 0.01

    def test_zero_eps_fallback(self):
        """Zero EPS: same fallback as negative."""
        proj = compute_projected_price(
            current_eps=0.0,
            current_spot=40.0,
            eps_decay=0.20,
            terminal_pe=11.0,
        )
        assert abs(proj - 32.0) < 0.01

    def test_predicted_drop_calculation(self):
        """Predicted drop should be correct percentage."""
        proj = compute_projected_price(
            current_eps=5.0,
            current_spot=100.0,
            eps_decay=0.25,
            terminal_pe=13.0,
        )
        drop = (100.0 - proj) / 100.0
        assert abs(drop - 0.5125) < 0.01


class TestLoadSectorDefaults:
    """Test sector defaults loading and fallback."""

    def test_known_sector(self, sector_defaults_file):
        eps_decay, terminal_pe = load_sector_defaults("EdTech", sector_defaults_file)
        assert eps_decay == 0.25
        assert terminal_pe == 13.0

    def test_unknown_sector_fallback(self, sector_defaults_file):
        eps_decay, terminal_pe = load_sector_defaults("Aerospace", sector_defaults_file)
        assert eps_decay == config.UNKNOWN_SECTOR_EPS_DECAY
        assert terminal_pe == config.UNKNOWN_SECTOR_TERMINAL_PE


class TestCompress:
    """Integration tests for the compress function."""

    def test_compress_updates_prediction(self, test_db, sector_defaults_file):
        """Compress should fill in projection fields on the prediction."""
        pred = Prediction(
            target_id="TGT_001",
            ticker="CHGG",
            sga_pct=0.45,
            gross_margin_pct=0.55,
            debt_to_equity=1.8,
            fcf_yield_pct=-0.02,
            roic_pct=0.03,
            vulnerability_score=0.75,
            current_eps=1.50,
            current_pe=25.0,
            current_spot=50.0,
            eps_decay_pct=0.0,
            terminal_pe=0.0,
            projected_price=0.0,
            predicted_drop_pct=0.0,
        )
        result = compress(pred, db_path=test_db, sector_defaults_path=sector_defaults_file)
        assert result is not None
        assert result.eps_decay_pct == 0.25
        assert result.terminal_pe == 13.0
        assert result.projected_price > 0
        assert result.predicted_drop_pct > 0

    def test_compress_below_gate_returns_none(self, test_db, sector_defaults_file):
        """If predicted drop is below COMPRESSION_GATE, returns None."""
        # With high EPS relative to spot, drop will be small
        pred = Prediction(
            target_id="TGT_001",
            ticker="CHGG",
            sga_pct=0.45,
            gross_margin_pct=0.55,
            debt_to_equity=1.8,
            fcf_yield_pct=-0.02,
            roic_pct=0.03,
            vulnerability_score=0.75,
            current_eps=10.0,
            current_pe=5.0,
            current_spot=50.0,
            eps_decay_pct=0.0,
            terminal_pe=0.0,
            projected_price=0.0,
            predicted_drop_pct=0.0,
        )
        result = compress(pred, db_path=test_db, sector_defaults_path=sector_defaults_file)
        # projected = 10*0.75*13 = 97.5; drop = (50-97.5)/50 = -0.95 (negative = price goes UP)
        assert result is None
