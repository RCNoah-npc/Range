"""Dataclasses for Tsunami Engine domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Target:
    """A company being evaluated for AI disruption vulnerability."""

    target_id: str
    ticker: str
    company: str
    sector: str
    added_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Financials:
    """Raw financial metrics pulled from data adapter."""

    ticker: str
    sga_pct: float
    gross_margin_pct: float
    debt_to_equity: float
    fcf_yield_pct: float
    roic_pct: float


@dataclass
class Prediction:
    """Vulnerability score and compression projection for a target."""

    target_id: str
    ticker: str
    sga_pct: float
    gross_margin_pct: float
    debt_to_equity: float
    fcf_yield_pct: float
    roic_pct: float
    vulnerability_score: float
    current_eps: float
    current_pe: float
    current_spot: float
    eps_decay_pct: float
    terminal_pe: float
    projected_price: float
    predicted_drop_pct: float
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FrictionData:
    """Market friction metrics for VRP filtering."""

    target_id: str
    ticker: str
    live_spot: float
    atm_put_iv: float
    put_call_ratio: float
    est_premium_ask: float
    hv_252d: float
    vrp_spread: float
    logged_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Signal:
    """A filtered, sized trading signal ready for underwriting."""

    target_id: str
    ticker: str
    predicted_drop_pct: float
    projected_price: float
    current_spot: float
    vrp_spread: float
    kelly_pct: float
    capital_to_deploy: float
    win_probability: float
    payoff_ratio: float


@dataclass
class Position:
    """An underwritten put option position."""

    target_id: str
    ticker: str
    strike: float
    expiry_date: str
    premium_paid: float
    contracts: int
    capital_deployed: float
    kelly_pct: float
    status: str = "OPEN"
    rop: float = 0.0
    decision: str = "REJECT"
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    realized_pnl: Optional[float] = None


@dataclass
class PaperPosition:
    """A paper-traded position for validation."""

    target_id: str
    ticker: str
    strike: float
    expiry_date: str
    premium_at_open: float
    contracts: int
    capital_deployed: float
    spot_at_open: float
    predicted_drop_pct: float
    spot_at_close: Optional[float] = None
    actual_drop_pct: Optional[float] = None
    status: str = "OPEN"
    opened_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ModelWeight:
    """A single feature weight from the backtester."""

    feature_name: str
    weight_pct: float
    r_squared: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionRow:
    """A single row in the execution matrix output."""

    ticker: str
    strike: float
    expiry_date: str
    contracts: int
    premium_per_share: float
    capital_deployed: float
    projected_price: float
    intrinsic_at_target: float
    rop: float
    kelly_pct: float
    decision: str  # EXECUTE or REJECT
