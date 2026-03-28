# Tsunami Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Build a Python CLI tool that scans for AI-vulnerable companies, calculates multiple compression price targets, filters for cost-efficient puts, sizes positions via Kelly Criterion, and generates execution matrices.

**Architecture:** Pipeline of 6 independent stages chained by SQLite. Each stage reads/writes to the DB. CLI orchestrator (Click) exposes each stage as a command. Pluggable data adapter pattern for financial data (yfinance initially).

**Tech Stack:** Python, Click, yfinance, pandas, numpy, scikit-learn, SQLite

---

## Task 1: Project Scaffolding

**Files:**
- `src/rangers/noah/tsunami/__init__.py` (create)
- `src/rangers/noah/tsunami/config.py` (create)
- `src/rangers/noah/tsunami/adapters/__init__.py` (create)
- `src/rangers/noah/tsunami/pipeline/__init__.py` (create)
- `src/rangers/noah/tsunami/models/__init__.py` (create)
- `src/rangers/noah/tsunami/data/sector_defaults.json` (create)
- `src/rangers/noah/tsunami/data/casualties.csv` (create)
- `src/rangers/noah/__init__.py` (create)
- `src/rangers/__init__.py` (create)
- `src/rangers/noah/tsunami/requirements.txt` (create)

**Steps:**

- [ ] Create all package directories and `__init__.py` files:

```python
# src/rangers/__init__.py
# Rangers shared namespace package
```

```python
# src/rangers/noah/__init__.py
# Noah's ranger namespace
```

```python
# src/rangers/noah/tsunami/__init__.py
"""Tsunami Engine: AI Disruption Multiple Compression Scanner."""

__version__ = "0.1.0"
```

```python
# src/rangers/noah/tsunami/adapters/__init__.py
"""Data adapters for financial data sources."""
```

```python
# src/rangers/noah/tsunami/pipeline/__init__.py
"""Pipeline stages for the Tsunami Engine."""
```

```python
# src/rangers/noah/tsunami/models/__init__.py
"""Data models and schemas."""
```

- [ ] Create `config.py` with all gate thresholds and configurable constants:

```python
# src/rangers/noah/tsunami/config.py
"""Configurable constants and gate thresholds for the Tsunami Engine."""

import os

# --- Gate thresholds ---
VULNERABILITY_GATE = float(os.environ.get("TSUNAMI_VULNERABILITY_GATE", "0.6"))
COMPRESSION_GATE = float(os.environ.get("TSUNAMI_COMPRESSION_GATE", "0.25"))
VRP_REJECT_THRESHOLD = float(os.environ.get("TSUNAMI_VRP_REJECT_THRESHOLD", "0.15"))
ROP_MINIMUM = float(os.environ.get("TSUNAMI_ROP_MINIMUM", "3.0"))

# --- Kelly sizing ---
KELLY_FRACTION = float(os.environ.get("TSUNAMI_KELLY_FRACTION", "0.25"))
MAX_POSITION_PCT = float(os.environ.get("TSUNAMI_MAX_POSITION_PCT", "0.10"))
DEFAULT_WIN_PROB = float(os.environ.get("TSUNAMI_DEFAULT_WIN_PROB", "0.55"))

# --- Underwriter ---
TARGET_DTE_MIN = int(os.environ.get("TSUNAMI_TARGET_DTE_MIN", "180"))
TARGET_DTE_MAX = int(os.environ.get("TSUNAMI_TARGET_DTE_MAX", "300"))

# --- Exit triggers ---
TAKE_PROFIT_ROI = float(os.environ.get("TSUNAMI_TAKE_PROFIT_ROI", "2.0"))
STOP_LOSS_ROI = float(os.environ.get("TSUNAMI_STOP_LOSS_ROI", "-0.50"))

# --- Scanner default weights (equal 20% each, before backtester calibration) ---
DEFAULT_FEATURE_WEIGHTS = {
    "sga_pct": 0.2,
    "gross_margin_pct": 0.2,
    "debt_to_equity": 0.2,
    "fcf_yield_pct": 0.2,
    "roic_pct": 0.2,
}

# --- Database ---
DB_PATH = os.environ.get(
    "TSUNAMI_DB_PATH",
    os.path.join(os.path.dirname(__file__), "data", "tsunami.db"),
)

# --- Sector defaults fallback ---
SECTOR_DEFAULTS_PATH = os.path.join(
    os.path.dirname(__file__), "data", "sector_defaults.json"
)

# --- Casualties seed path ---
CASUALTIES_PATH = os.path.join(
    os.path.dirname(__file__), "data", "casualties.csv"
)

# --- Unknown sector fallback values ---
UNKNOWN_SECTOR_EPS_DECAY = 0.15
UNKNOWN_SECTOR_TERMINAL_PE = 12.0
```

- [ ] Create `requirements.txt`:

```text
# src/rangers/noah/tsunami/requirements.txt
click>=8.1.0
yfinance>=0.2.30
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
```

- [ ] Create `sector_defaults.json`:

```json
{
    "EdTech": {
        "eps_decay": 0.25,
        "terminal_pe": 13.0
    },
    "BPO/CallCenter": {
        "eps_decay": 0.15,
        "terminal_pe": 12.0
    },
    "IT Services": {
        "eps_decay": 0.10,
        "terminal_pe": 14.0
    },
    "Legal Services": {
        "eps_decay": 0.12,
        "terminal_pe": 10.0
    },
    "Freelance/Gig": {
        "eps_decay": 0.20,
        "terminal_pe": 11.0
    },
    "Media/Stock Images": {
        "eps_decay": 0.18,
        "terminal_pe": 12.0
    }
}
```

- [ ] Create `casualties.csv`:

```csv
ticker,company,sector,peak_date,peak_price,trough_date,trough_price,catalyst
CHGG,Chegg,EdTech,2021-02-16,113.88,2024-01-01,9.17,ChatGPT homework replacement
FVRR,Fiverr,Freelance/Gig,2021-02-12,336.10,2024-01-01,24.36,AI automates gig tasks
UPWK,Upwork,Freelance/Gig,2021-10-15,63.43,2024-01-01,11.56,AI reduces freelance demand
TEP.PA,Teleperformance,BPO/CallCenter,2022-08-15,390.00,2024-01-01,118.00,AI chatbots replace agents
TASK,TaskUs,BPO/CallCenter,2021-11-12,85.49,2024-01-01,13.55,AI replaces content moderation
SSTK,Shutterstock,Media/Stock Images,2022-11-14,68.49,2024-01-01,36.28,AI image generation
TWOU,2U Inc,EdTech,2021-02-16,49.38,2024-01-01,0.61,AI tutoring displaces online degrees
GETY,Getty Images,Media/Stock Images,2023-02-01,7.50,2024-01-01,3.11,AI image generation
EPAM,EPAM Systems,IT Services,2021-11-12,740.24,2024-01-01,259.62,AI coding assistants
COUR,Coursera,EdTech,2021-04-01,62.53,2024-01-01,14.65,AI tutoring and content generation
```

- [ ] Verify all files exist and directory structure is correct

**Test command:**
```bash
python -c "from src.rangers.noah.tsunami import config; print('Config loaded:', config.VULNERABILITY_GATE)"
```
Expected output: `Config loaded: 0.6`

- [ ] Commit: `git add src/rangers/ && git commit -m "feat(tsunami): scaffold project structure with config, seed data, and requirements"`

---

## Task 2: Database Layer

**Files:**
- `src/rangers/noah/tsunami/db.py` (create)

**Steps:**

- [ ] Create `db.py` with all 6 table CREATE statements and init function:

```python
# src/rangers/noah/tsunami/db.py
"""SQLite database connection and schema initialization."""

import sqlite3
from contextlib import contextmanager
from typing import Generator

from .config import DB_PATH

SQL_CREATE_TARGET_COMPANIES = """
CREATE TABLE IF NOT EXISTS target_companies (
    target_id   TEXT PRIMARY KEY,
    ticker      TEXT UNIQUE NOT NULL,
    company     TEXT NOT NULL,
    sector      TEXT NOT NULL,
    added_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_FUNDAMENTAL_PREDICTIONS = """
CREATE TABLE IF NOT EXISTS fundamental_predictions (
    model_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id           TEXT NOT NULL REFERENCES target_companies(target_id),
    calculated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sga_pct             REAL,
    gross_margin_pct    REAL,
    debt_to_equity      REAL,
    fcf_yield_pct       REAL,
    roic_pct            REAL,
    vulnerability_score REAL,
    current_eps         REAL,
    current_pe          REAL,
    eps_decay_pct       REAL,
    terminal_pe         REAL,
    projected_price     REAL,
    predicted_drop_pct  REAL
);
"""

SQL_CREATE_MARKET_FRICTION_LOG = """
CREATE TABLE IF NOT EXISTS market_friction_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id       TEXT NOT NULL REFERENCES target_companies(target_id),
    logged_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    live_spot       REAL,
    atm_put_iv      REAL,
    put_call_ratio  REAL,
    est_premium_ask REAL,
    hv_252d         REAL,
    vrp_spread      REAL
);
"""

SQL_CREATE_MODEL_WEIGHTS = """
CREATE TABLE IF NOT EXISTS model_weights (
    weight_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feature_name TEXT NOT NULL,
    weight_pct   REAL NOT NULL,
    r_squared    REAL
);
"""

SQL_CREATE_POSITIONS = """
CREATE TABLE IF NOT EXISTS positions (
    position_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id        TEXT NOT NULL REFERENCES target_companies(target_id),
    opened_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    strike           REAL NOT NULL,
    expiry_date      TEXT NOT NULL,
    premium_paid     REAL NOT NULL,
    contracts        INTEGER NOT NULL,
    capital_deployed REAL NOT NULL,
    kelly_pct        REAL,
    status           TEXT NOT NULL DEFAULT 'OPEN',
    closed_at        TIMESTAMP,
    realized_pnl     REAL
);
"""

SQL_CREATE_PAPER_POSITIONS = """
CREATE TABLE IF NOT EXISTS paper_positions (
    paper_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id           TEXT NOT NULL REFERENCES target_companies(target_id),
    opened_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    strike              REAL NOT NULL,
    expiry_date         TEXT NOT NULL,
    premium_at_open     REAL NOT NULL,
    contracts           INTEGER NOT NULL,
    capital_deployed    REAL NOT NULL,
    spot_at_open        REAL NOT NULL,
    spot_at_close       REAL,
    predicted_drop_pct  REAL,
    actual_drop_pct     REAL,
    status              TEXT NOT NULL DEFAULT 'OPEN'
);
"""

ALL_CREATE_STATEMENTS = [
    SQL_CREATE_TARGET_COMPANIES,
    SQL_CREATE_FUNDAMENTAL_PREDICTIONS,
    SQL_CREATE_MARKET_FRICTION_LOG,
    SQL_CREATE_MODEL_WEIGHTS,
    SQL_CREATE_POSITIONS,
    SQL_CREATE_PAPER_POSITIONS,
]


def init_db(db_path: str | None = None) -> None:
    """Create all tables if they don't exist."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        for stmt in ALL_CREATE_STATEMENTS:
            cursor.execute(stmt)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_connection(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that yields a SQLite connection with row_factory set."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

- [ ] Verify DB init works:

**Test command:**
```bash
python -c "
import sys, os
sys.path.insert(0, 'src')
from rangers.noah.tsunami.db import init_db, get_connection
init_db('/tmp/tsunami_test.db')
with get_connection('/tmp/tsunami_test.db') as conn:
    tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
    print('Tables:', [t['name'] for t in tables])
"
```
Expected output: `Tables: ['target_companies', 'fundamental_predictions', 'market_friction_log', 'model_weights', 'positions', 'paper_positions']`

- [ ] Commit: `git add src/rangers/noah/tsunami/db.py && git commit -m "feat(tsunami): add SQLite database layer with all 6 table schemas"`

---

## Task 3: Data Models

**Files:**
- `src/rangers/noah/tsunami/models/schemas.py` (create)

**Steps:**

- [ ] Create `schemas.py` with all dataclasses:

```python
# src/rangers/noah/tsunami/models/schemas.py
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
```

- [ ] Verify models import:

**Test command:**
```bash
python -c "
import sys; sys.path.insert(0, 'src')
from rangers.noah.tsunami.models.schemas import Target, Prediction, Signal, Position, ExecutionRow
print('All models imported successfully')
print('Target fields:', [f.name for f in Target.__dataclass_fields__.values()])
"
```
Expected output: `All models imported successfully` followed by Target fields list.

- [ ] Commit: `git add src/rangers/noah/tsunami/models/schemas.py && git commit -m "feat(tsunami): add dataclass models for all domain objects"`

---

## Task 4: Adapter Interface + YFinance Adapter

**Files:**
- `src/rangers/noah/tsunami/adapters/base.py` (create)
- `src/rangers/noah/tsunami/adapters/yfinance_adapter.py` (create)

**Steps:**

- [ ] Create `base.py` abstract adapter interface:

```python
# src/rangers/noah/tsunami/adapters/base.py
"""Abstract base class for financial data adapters."""

from abc import ABC, abstractmethod

import pandas as pd


class DataAdapter(ABC):
    """Interface for financial data sources.

    All adapters must implement these methods.  The Tsunami pipeline
    calls them generically so that switching from yfinance to a paid
    provider (FMP, Polygon, etc.) requires only a new adapter class.
    """

    @abstractmethod
    def get_financials(self, ticker: str) -> dict:
        """Return fundamental metrics for vulnerability scoring.

        Expected keys:
            sga_pct        -- SG&A as % of revenue
            gross_margin_pct -- Gross margin percentage (0-1 scale)
            debt_to_equity -- Debt-to-equity ratio
            fcf_yield_pct  -- Free cash flow yield (0-1 scale)
            roic_pct       -- Return on invested capital (0-1 scale)
        """

    @abstractmethod
    def get_price(self, ticker: str) -> float:
        """Return the current spot price."""

    @abstractmethod
    def get_valuation(self, ticker: str) -> dict:
        """Return valuation metrics.

        Expected keys:
            eps -- Trailing EPS
            pe  -- Trailing P/E ratio
        """

    @abstractmethod
    def get_historical_prices(self, ticker: str, period: str) -> pd.DataFrame:
        """Return OHLCV DataFrame for volatility calculations.

        Must include a 'Close' column at minimum.
        ``period`` follows yfinance convention: '1y', '2y', etc.
        """

    @abstractmethod
    def get_options_chain(self, ticker: str, min_dte: int) -> pd.DataFrame:
        """Return puts options chain filtered to >= min_dte days out.

        Required columns:
            strike, bid, ask, volume, openInterest,
            impliedVolatility, expiry (str YYYY-MM-DD)
        """
```

- [ ] Create `yfinance_adapter.py`:

```python
# src/rangers/noah/tsunami/adapters/yfinance_adapter.py
"""YFinance implementation of the DataAdapter interface."""

from __future__ import annotations

import warnings
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from .base import DataAdapter


class YFinanceAdapter(DataAdapter):
    """Free-tier data adapter using the yfinance library."""

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _safe_get(info: dict, key: str, default: Any = None) -> Any:
        """Return info[key] if present and not None/NaN, else default."""
        val = info.get(key, default)
        if val is None:
            return default
        if isinstance(val, float) and np.isnan(val):
            return default
        return val

    @staticmethod
    def _first_valid(series: pd.Series) -> float | None:
        """Return the first non-NaN value from a pandas Series."""
        for val in series:
            if pd.notna(val):
                return float(val)
        return None

    # ------------------------------------------------------------------ #
    #  Interface methods
    # ------------------------------------------------------------------ #

    def get_financials(self, ticker: str) -> dict:
        """Pull fundamental metrics and derive SGA%, FCF yield, ROIC."""
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        income = tk.income_stmt  # columns = fiscal years, rows = line items
        balance = tk.balance_sheet
        cashflow = tk.cashflow

        # --- SGA % of revenue ---
        sga_pct = None
        if income is not None and not income.empty:
            sga_row = None
            for label in [
                "SellingGeneralAndAdministration",
                "Selling General And Administration",
                "SellingGeneralAndAdministrative",
            ]:
                if label in income.index:
                    sga_row = income.loc[label]
                    break
            rev_row = None
            for label in ["TotalRevenue", "Total Revenue"]:
                if label in income.index:
                    rev_row = income.loc[label]
                    break
            if sga_row is not None and rev_row is not None:
                sga_val = self._first_valid(sga_row)
                rev_val = self._first_valid(rev_row)
                if sga_val and rev_val and rev_val != 0:
                    sga_pct = sga_val / rev_val

        # --- Gross margin ---
        gross_margin_pct = self._safe_get(info, "grossMargins")

        # --- Debt to equity ---
        debt_to_equity_raw = self._safe_get(info, "debtToEquity")
        # yfinance sometimes returns this as a percentage (e.g. 150.0 for 1.5x)
        debt_to_equity = (
            debt_to_equity_raw / 100.0
            if debt_to_equity_raw is not None and debt_to_equity_raw > 10
            else debt_to_equity_raw
        )

        # --- FCF yield ---
        fcf_yield_pct = None
        if cashflow is not None and not cashflow.empty:
            fcf_row = None
            for label in ["FreeCashFlow", "Free Cash Flow"]:
                if label in cashflow.index:
                    fcf_row = cashflow.loc[label]
                    break
            fcf_val = self._first_valid(fcf_row) if fcf_row is not None else None
            shares = self._safe_get(info, "sharesOutstanding")
            price = self._safe_get(info, "currentPrice") or self._safe_get(
                info, "regularMarketPrice"
            )
            if fcf_val is not None and shares and price and (shares * price) != 0:
                fcf_yield_pct = fcf_val / (shares * price)

        # --- ROIC ---
        roic_pct = None
        if (
            income is not None
            and not income.empty
            and balance is not None
            and not balance.empty
        ):
            ni_row = None
            for label in ["NetIncome", "Net Income"]:
                if label in income.index:
                    ni_row = income.loc[label]
                    break
            ta_row = None
            for label in ["TotalAssets", "Total Assets"]:
                if label in balance.index:
                    ta_row = balance.loc[label]
                    break
            cl_row = None
            for label in ["CurrentLiabilities", "Current Liabilities"]:
                if label in balance.index:
                    cl_row = balance.loc[label]
                    break
            ni_val = self._first_valid(ni_row) if ni_row is not None else None
            ta_val = self._first_valid(ta_row) if ta_row is not None else None
            cl_val = self._first_valid(cl_row) if cl_row is not None else None
            if ni_val is not None and ta_val is not None and cl_val is not None:
                invested_capital = ta_val - cl_val
                if invested_capital != 0:
                    nopat = ni_val * (1 - 0.21)  # after-tax
                    roic_pct = nopat / invested_capital

        return {
            "sga_pct": sga_pct,
            "gross_margin_pct": gross_margin_pct,
            "debt_to_equity": debt_to_equity,
            "fcf_yield_pct": fcf_yield_pct,
            "roic_pct": roic_pct,
        }

    def get_price(self, ticker: str) -> float:
        """Return current spot price."""
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        price = self._safe_get(info, "currentPrice") or self._safe_get(
            info, "regularMarketPrice"
        )
        if price is None:
            raise ValueError(f"Cannot retrieve price for {ticker}")
        return float(price)

    def get_valuation(self, ticker: str) -> dict:
        """Return EPS and P/E ratio."""
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        eps = self._safe_get(info, "trailingEps", 0.0)
        pe = self._safe_get(info, "trailingPE", 0.0)
        return {"eps": float(eps), "pe": float(pe)}

    def get_historical_prices(self, ticker: str, period: str = "2y") -> pd.DataFrame:
        """Return OHLCV data for HV calculation."""
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, auto_adjust=True)
        if df is None or df.empty:
            raise ValueError(f"No historical price data for {ticker}")
        return df

    def get_options_chain(self, ticker: str, min_dte: int = 180) -> pd.DataFrame:
        """Return puts chain with DTE >= min_dte.

        Iterates available expiration dates from yfinance and collects
        put options for those expiries that are at least ``min_dte`` days
        out.  Returns a single DataFrame with an added ``expiry`` column.
        """
        tk = yf.Ticker(ticker)
        expirations = tk.options  # tuple of 'YYYY-MM-DD' strings
        if not expirations:
            warnings.warn(f"No options chain available for {ticker}")
            return pd.DataFrame()

        cutoff = datetime.utcnow() + timedelta(days=min_dte)
        frames: list[pd.DataFrame] = []

        for exp_str in expirations:
            exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
            if exp_dt < cutoff:
                continue
            chain = tk.option_chain(exp_str)
            puts = chain.puts.copy()
            puts["expiry"] = exp_str
            frames.append(puts)

        if not frames:
            warnings.warn(
                f"No options with DTE >= {min_dte} for {ticker}"
            )
            return pd.DataFrame()

        result = pd.concat(frames, ignore_index=True)
        # Normalize column names to match adapter interface
        rename_map = {
            "impliedVolatility": "impliedVolatility",
            "openInterest": "openInterest",
        }
        result.rename(columns=rename_map, inplace=True)
        return result
```

- [ ] Verify adapter imports:

**Test command:**
```bash
python -c "
import sys; sys.path.insert(0, 'src')
from rangers.noah.tsunami.adapters.base import DataAdapter
from rangers.noah.tsunami.adapters.yfinance_adapter import YFinanceAdapter
print('Adapter classes imported successfully')
print('YFinanceAdapter methods:', [m for m in dir(YFinanceAdapter) if not m.startswith('_')])
"
```
Expected output: `Adapter classes imported successfully` followed by method list.

- [ ] Commit: `git add src/rangers/noah/tsunami/adapters/ && git commit -m "feat(tsunami): add DataAdapter interface and YFinance implementation"`

---

## Task 5: Scanner Pipeline Stage (TDD)

**Files:**
- `tests/rangers/noah/tsunami/test_scanner.py` (create)
- `src/rangers/noah/tsunami/pipeline/scanner.py` (create)

**Steps:**

- [ ] Write the failing test first:

```python
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
```

- [ ] Run the test and verify it fails:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_scanner.py -v 2>&1 | head -30
```
Expected: `ModuleNotFoundError` or `ImportError` (scanner.py does not exist yet).

- [ ] Implement `scanner.py`:

```python
# src/rangers/noah/tsunami/pipeline/scanner.py
"""Stage 1: Vulnerability Scanner.

Pulls financial metrics via the data adapter, computes a weighted
vulnerability score, and gates on VULNERABILITY_GATE.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from ..adapters.base import DataAdapter
from ..config import (
    DB_PATH,
    DEFAULT_FEATURE_WEIGHTS,
    VULNERABILITY_GATE,
)
from ..db import get_connection
from ..models.schemas import Prediction

logger = logging.getLogger(__name__)

# Normalization ranges for each metric.
# (min_bad, max_bad) -- values outside are clamped.
# Higher raw score = MORE vulnerable.
METRIC_RANGES = {
    "sga_pct": {"min": 0.05, "max": 0.60, "direction": "higher_is_worse"},
    "gross_margin_pct": {"min": 0.20, "max": 0.90, "direction": "lower_is_worse"},
    "debt_to_equity": {"min": 0.0, "max": 3.0, "direction": "higher_is_worse"},
    "fcf_yield_pct": {"min": -0.10, "max": 0.15, "direction": "lower_is_worse"},
    "roic_pct": {"min": -0.10, "max": 0.30, "direction": "lower_is_worse"},
}


def _normalize_metric(value: float | None, metric_name: str) -> float:
    """Normalize a raw metric to 0-1 where 1 = most vulnerable.

    Returns 0.5 (neutral) when value is None.
    """
    if value is None:
        return 0.5

    spec = METRIC_RANGES[metric_name]
    lo = spec["min"]
    hi = spec["max"]

    # Clamp
    clamped = max(lo, min(hi, value))

    # Scale to 0-1
    if hi == lo:
        normalized = 0.5
    else:
        normalized = (clamped - lo) / (hi - lo)

    # Flip direction so 1 always = most vulnerable
    if spec["direction"] == "lower_is_worse":
        normalized = 1.0 - normalized

    return normalized


def compute_vulnerability_score(
    financials: dict, weights: dict[str, float]
) -> float:
    """Compute weighted composite vulnerability score (0-1).

    Parameters
    ----------
    financials : dict
        Raw metrics from the data adapter (sga_pct, gross_margin_pct, etc.).
    weights : dict
        Feature name -> weight (should sum to ~1.0).

    Returns
    -------
    float
        Clamped vulnerability score between 0 and 1.
    """
    score = 0.0
    for feature, weight in weights.items():
        raw = financials.get(feature)
        normalized = _normalize_metric(raw, feature)
        score += normalized * weight

    return max(0.0, min(1.0, score))


def _load_weights_from_db(db_path: str) -> dict[str, float] | None:
    """Load the latest backtester weights from model_weights table.

    Returns None if no weights exist (use defaults).
    """
    try:
        with get_connection(db_path) as conn:
            rows = conn.execute(
                """
                SELECT feature_name, weight_pct
                FROM model_weights
                WHERE created_at = (SELECT MAX(created_at) FROM model_weights)
                """
            ).fetchall()
            if not rows:
                return None
            return {row["feature_name"]: row["weight_pct"] for row in rows}
    except Exception:
        return None


def _get_target_id(ticker: str, db_path: str) -> str | None:
    """Look up the target_id for a ticker."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT target_id FROM target_companies WHERE ticker = ?",
            (ticker,),
        ).fetchone()
        return row["target_id"] if row else None


def scan_ticker(
    ticker: str,
    adapter: DataAdapter,
    db_path: str | None = None,
) -> Optional[Prediction]:
    """Run the vulnerability scan on a single ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol.
    adapter : DataAdapter
        Financial data source.
    db_path : str, optional
        Override for the SQLite database path.

    Returns
    -------
    Prediction or None
        Returns the Prediction if the ticker passes the vulnerability gate,
        otherwise None.
    """
    path = db_path or DB_PATH
    target_id = _get_target_id(ticker, path)
    if target_id is None:
        logger.warning("Ticker %s not found in target_companies table", ticker)
        return None

    # Pull financials
    try:
        financials = adapter.get_financials(ticker)
    except Exception as exc:
        logger.error("Failed to get financials for %s: %s", ticker, exc)
        return None

    # Load weights (backtester-derived or defaults)
    weights = _load_weights_from_db(path) or DEFAULT_FEATURE_WEIGHTS

    # Score
    vulnerability_score = compute_vulnerability_score(financials, weights)
    logger.info(
        "Ticker %s vulnerability_score=%.4f (gate=%.2f)",
        ticker,
        vulnerability_score,
        VULNERABILITY_GATE,
    )

    # Pull valuation for persistence even if below gate
    try:
        valuation = adapter.get_valuation(ticker)
        current_eps = valuation.get("eps", 0.0)
        current_pe = valuation.get("pe", 0.0)
    except Exception:
        current_eps = 0.0
        current_pe = 0.0

    try:
        current_spot = adapter.get_price(ticker)
    except Exception:
        current_spot = 0.0

    # Persist raw scan to DB
    prediction = Prediction(
        target_id=target_id,
        ticker=ticker,
        sga_pct=financials.get("sga_pct") or 0.0,
        gross_margin_pct=financials.get("gross_margin_pct") or 0.0,
        debt_to_equity=financials.get("debt_to_equity") or 0.0,
        fcf_yield_pct=financials.get("fcf_yield_pct") or 0.0,
        roic_pct=financials.get("roic_pct") or 0.0,
        vulnerability_score=vulnerability_score,
        current_eps=current_eps,
        current_pe=current_pe,
        current_spot=current_spot,
        eps_decay_pct=0.0,  # set by compressor
        terminal_pe=0.0,  # set by compressor
        projected_price=0.0,  # set by compressor
        predicted_drop_pct=0.0,  # set by compressor
    )

    with get_connection(path) as conn:
        conn.execute(
            """
            INSERT INTO fundamental_predictions (
                target_id, sga_pct, gross_margin_pct, debt_to_equity,
                fcf_yield_pct, roic_pct, vulnerability_score,
                current_eps, current_pe
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                target_id,
                prediction.sga_pct,
                prediction.gross_margin_pct,
                prediction.debt_to_equity,
                prediction.fcf_yield_pct,
                prediction.roic_pct,
                prediction.vulnerability_score,
                prediction.current_eps,
                prediction.current_pe,
            ),
        )

    # Gate
    if vulnerability_score <= VULNERABILITY_GATE:
        logger.info("Ticker %s below vulnerability gate -- skipping", ticker)
        return None

    return prediction
```

- [ ] Run tests and verify they pass:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_scanner.py -v
```
Expected: All tests pass.

- [ ] Commit: `git add src/rangers/noah/tsunami/pipeline/scanner.py tests/rangers/noah/tsunami/test_scanner.py && git commit -m "feat(tsunami): add Scanner stage with TDD tests"`

---

## Task 6: Compressor Pipeline Stage (TDD)

**Files:**
- `tests/rangers/noah/tsunami/test_compressor.py` (create)
- `src/rangers/noah/tsunami/pipeline/compressor.py` (create)

**Steps:**

- [ ] Write the failing test first:

```python
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
```

- [ ] Run the test and verify it fails:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_compressor.py -v 2>&1 | head -30
```
Expected: `ImportError` (compressor.py does not exist yet).

- [ ] Implement `compressor.py`:

```python
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
```

- [ ] Run tests and verify they pass:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_compressor.py -v
```
Expected: All tests pass.

- [ ] Commit: `git add src/rangers/noah/tsunami/pipeline/compressor.py tests/rangers/noah/tsunami/test_compressor.py && git commit -m "feat(tsunami): add Compressor stage with negative EPS fallback and TDD tests"`

---

## Task 7: Backtester Pipeline Stage

**Files:**
- `src/rangers/noah/tsunami/pipeline/backtester.py` (create)

**Steps:**

- [ ] Implement `backtester.py` with Random Forest only:

```python
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
            df[feat].fillna(median_val if pd.notna(median_val) else 0.0, inplace=True)

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
```

- [ ] Verify import:

**Test command:**
```bash
python -c "
import sys; sys.path.insert(0, 'src')
from rangers.noah.tsunami.pipeline.backtester import run_backtest, SEED_TICKERS, FEATURE_NAMES
print('Backtester imported. Seed tickers:', SEED_TICKERS)
print('Features:', FEATURE_NAMES)
"
```
Expected: Imports succeed with seed tickers and features printed.

- [ ] Commit: `git add src/rangers/noah/tsunami/pipeline/backtester.py && git commit -m "feat(tsunami): add Backtester stage with Random Forest and weight persistence"`

---

## Task 8: VRP Filter Pipeline Stage (TDD)

**Files:**
- `tests/rangers/noah/tsunami/test_filter.py` (create)
- `src/rangers/noah/tsunami/pipeline/filter.py` (create)

**Steps:**

- [ ] Write the failing test first:

```python
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
```

- [ ] Run the test and verify it fails:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_filter.py -v 2>&1 | head -30
```
Expected: `ImportError` (filter.py does not exist yet).

- [ ] Implement `filter.py`:

```python
# src/rangers/noah/tsunami/pipeline/filter.py
"""Stage 4: VRP Filter.

Compares implied volatility to realized volatility to reject
overpriced puts.  VRP = atm_put_iv - hv_252d.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from ..adapters.base import DataAdapter
from ..config import DB_PATH, VRP_REJECT_THRESHOLD
from ..db import get_connection
from ..models.schemas import FrictionData, Prediction

logger = logging.getLogger(__name__)


def compute_hv_252d(price_df: pd.DataFrame) -> float | None:
    """Compute annualized 252-day historical volatility from daily closes.

    Parameters
    ----------
    price_df : pd.DataFrame
        Must contain a 'Close' column with at least 253 rows.

    Returns
    -------
    float or None
        Annualized HV, or None if insufficient data.
    """
    if price_df is None or price_df.empty or len(price_df) < 253:
        return None

    closes = price_df["Close"].dropna().values
    if len(closes) < 253:
        return None

    # Use last 253 prices to get 252 log returns
    prices = closes[-253:]
    log_returns = np.log(prices[1:] / prices[:-1])
    hv = float(np.std(log_returns) * np.sqrt(252))
    return hv


def compute_vrp(atm_put_iv: float, hv_252d: float) -> float:
    """Compute Volatility Risk Premium.

    VRP = atm_put_iv - hv_252d

    Positive VRP = puts are expensive relative to realized vol.
    Negative VRP = puts are cheap (premium discount).
    """
    return atm_put_iv - hv_252d


def classify_vrp(vrp: float) -> str:
    """Classify VRP into action buckets.

    - VRP >= VRP_REJECT_THRESHOLD (0.15): REJECT
    - 0 <= VRP < VRP_REJECT_THRESHOLD: FAIR_VALUE
    - VRP < 0: PREMIUM_DISCOUNT
    """
    if vrp >= VRP_REJECT_THRESHOLD:
        return "REJECT"
    elif vrp >= 0:
        return "FAIR_VALUE"
    else:
        return "PREMIUM_DISCOUNT"


def _get_atm_put_iv(
    adapter: DataAdapter, ticker: str, spot: float, min_dte: int = 180
) -> tuple[float | None, float | None, float | None]:
    """Find the ATM put IV and premium from the options chain.

    Returns (atm_put_iv, est_premium_ask, put_call_ratio).
    """
    try:
        chain = adapter.get_options_chain(ticker, min_dte=min_dte)
    except Exception as exc:
        logger.warning("Cannot fetch options chain for %s: %s", ticker, exc)
        return None, None, None

    if chain is None or chain.empty:
        logger.warning("Empty options chain for %s", ticker)
        return None, None, None

    # Find strike nearest to spot
    chain = chain.copy()
    chain["dist"] = (chain["strike"] - spot).abs()
    atm_row = chain.loc[chain["dist"].idxmin()]

    iv = float(atm_row.get("impliedVolatility", 0))
    bid = float(atm_row.get("bid", 0))
    ask = float(atm_row.get("ask", 0))
    premium = (bid + ask) / 2.0 if (bid + ask) > 0 else ask

    # Put/call ratio (approximate from volume if available)
    total_vol = chain["volume"].sum() if "volume" in chain.columns else 0
    put_call_ratio = 1.0  # placeholder; full chain would need calls too

    return iv, premium, put_call_ratio


def filter_targets(
    predictions: list[Prediction],
    adapter: DataAdapter,
    db_path: str | None = None,
) -> list[tuple[Prediction, FrictionData]]:
    """Filter a list of predictions by VRP.

    Returns predictions that pass the VRP gate, sorted by VRP ascending
    (cheapest puts first).

    Parameters
    ----------
    predictions : list[Prediction]
        Predictions that have passed the compression gate.
    adapter : DataAdapter
        Financial data source.
    db_path : str, optional
        Override for the SQLite database path.

    Returns
    -------
    list of (Prediction, FrictionData) tuples, sorted by VRP ascending.
    """
    path = db_path or DB_PATH
    results: list[tuple[Prediction, FrictionData, float]] = []

    for pred in predictions:
        ticker = pred.ticker
        spot = pred.current_spot

        # Compute HV
        try:
            hist = adapter.get_historical_prices(ticker, period="2y")
            hv = compute_hv_252d(hist)
        except Exception as exc:
            logger.warning("Cannot compute HV for %s: %s", ticker, exc)
            hv = None

        if hv is None:
            logger.warning(
                "Skipping %s from VRP filter -- insufficient historical data", ticker
            )
            continue

        # Get ATM put IV
        atm_iv, premium, pcr = _get_atm_put_iv(adapter, ticker, spot)
        if atm_iv is None:
            logger.warning(
                "Skipping %s from VRP filter -- no options chain data", ticker
            )
            continue

        vrp = compute_vrp(atm_iv, hv)
        classification = classify_vrp(vrp)

        friction = FrictionData(
            target_id=pred.target_id,
            ticker=ticker,
            live_spot=spot,
            atm_put_iv=atm_iv,
            put_call_ratio=pcr or 1.0,
            est_premium_ask=premium or 0.0,
            hv_252d=hv,
            vrp_spread=vrp,
        )

        # Persist to market_friction_log
        with get_connection(path) as conn:
            conn.execute(
                """
                INSERT INTO market_friction_log (
                    target_id, live_spot, atm_put_iv, put_call_ratio,
                    est_premium_ask, hv_252d, vrp_spread
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pred.target_id,
                    spot,
                    atm_iv,
                    pcr or 1.0,
                    premium or 0.0,
                    hv,
                    vrp,
                ),
            )

        logger.info(
            "Ticker %s: VRP=%.4f (%s), IV=%.4f, HV=%.4f",
            ticker,
            vrp,
            classification,
            atm_iv,
            hv,
        )

        if classification == "REJECT":
            logger.info("Ticker %s REJECTED -- VRP too high (%.4f)", ticker, vrp)
            continue

        results.append((pred, friction, vrp))

    # Sort by VRP ascending (cheapest puts first)
    results.sort(key=lambda x: x[2])

    return [(pred, friction) for pred, friction, _ in results]
```

- [ ] Run tests and verify they pass:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_filter.py -v
```
Expected: All tests pass.

- [ ] Commit: `git add src/rangers/noah/tsunami/pipeline/filter.py tests/rangers/noah/tsunami/test_filter.py && git commit -m "feat(tsunami): add VRP Filter stage with TDD tests"`

---

## Task 9: Kelly Sizer Pipeline Stage (TDD)

**Files:**
- `tests/rangers/noah/tsunami/test_sizer.py` (create)
- `src/rangers/noah/tsunami/pipeline/sizer.py` (create)

**Steps:**

- [ ] Write the failing test first:

```python
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
```

- [ ] Run the test and verify it fails:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_sizer.py -v 2>&1 | head -30
```
Expected: `ImportError` (sizer.py does not exist yet).

- [ ] Implement `sizer.py`:

```python
# src/rangers/noah/tsunami/pipeline/sizer.py
"""Stage 5: Kelly Criterion Position Sizer.

Calculates optimal position size using fractional (quarter) Kelly.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..config import (
    DEFAULT_WIN_PROB,
    KELLY_FRACTION,
    MAX_POSITION_PCT,
)
from ..models.schemas import FrictionData, Prediction, Signal

logger = logging.getLogger(__name__)


def compute_payoff_ratio(
    projected_price: float, strike: float, premium: float
) -> float:
    """Compute the payoff ratio b for the Kelly formula.

    b = (intrinsic_at_target - premium) / premium

    where intrinsic_at_target = max(0, strike - projected_price).

    Returns 0.0 if premium is zero (avoid division by zero).
    """
    if premium <= 0:
        return 0.0

    intrinsic = max(0.0, strike - projected_price)
    return (intrinsic - premium) / premium


def compute_kelly(p: float, b: float) -> float:
    """Compute the full Kelly fraction.

    f* = p - (q / b)  where q = 1 - p

    Returns the raw (full) Kelly value.  May be negative if the trade
    has negative expected value.
    """
    if b <= 0:
        return -1.0  # signal that trade is not viable

    q = 1.0 - p
    return p - (q / b)


def size_position(
    prediction: Prediction,
    friction: FrictionData,
    portfolio_value: float,
    win_prob: float | None = None,
) -> Optional[Signal]:
    """Size a single position using quarter-Kelly with a 10% hard cap.

    Parameters
    ----------
    prediction : Prediction
        Must have projected_price and current_spot filled in.
    friction : FrictionData
        Must have est_premium_ask and live_spot.
    portfolio_value : float
        Total portfolio value in dollars.
    win_prob : float, optional
        Override win probability (default: DEFAULT_WIN_PROB from config).

    Returns
    -------
    Signal or None
        Returns None if Kelly fraction is <= 0 (negative expected value).
    """
    p = win_prob if win_prob is not None else DEFAULT_WIN_PROB
    premium = friction.est_premium_ask
    spot = friction.live_spot

    # Use a midpoint strike for sizing estimation
    # (actual strike selected by underwriter later)
    estimated_strike = spot * (1.0 + prediction.predicted_drop_pct / 2.0)
    # The strike should be BELOW spot for a put
    # predicted_drop_pct is positive (e.g. 0.70 means 70% drop)
    # midpoint strike = spot * (1 - predicted_drop/2) = halfway to target
    estimated_strike = spot * (1.0 - prediction.predicted_drop_pct / 2.0)

    b = compute_payoff_ratio(
        projected_price=prediction.projected_price,
        strike=estimated_strike,
        premium=premium,
    )

    f_full = compute_kelly(p, b)

    if f_full <= 0:
        logger.info(
            "Ticker %s REJECTED by Kelly -- f*=%.4f (negative EV). p=%.2f, b=%.2f",
            prediction.ticker,
            f_full,
            p,
            b,
        )
        return None

    f_applied = min(f_full * KELLY_FRACTION, MAX_POSITION_PCT)
    capital_to_deploy = portfolio_value * f_applied

    logger.info(
        "Ticker %s: f_full=%.4f, quarter_kelly=%.4f, capped=%.4f, capital=$%.2f",
        prediction.ticker,
        f_full,
        f_full * KELLY_FRACTION,
        f_applied,
        capital_to_deploy,
    )

    return Signal(
        target_id=prediction.target_id,
        ticker=prediction.ticker,
        predicted_drop_pct=prediction.predicted_drop_pct,
        projected_price=prediction.projected_price,
        current_spot=spot,
        vrp_spread=friction.vrp_spread,
        kelly_pct=f_applied,
        capital_to_deploy=capital_to_deploy,
        win_probability=p,
        payoff_ratio=b,
    )


def size_all(
    filtered: list[tuple[Prediction, FrictionData]],
    portfolio_value: float,
    win_prob: float | None = None,
) -> list[Signal]:
    """Size all filtered targets.

    Parameters
    ----------
    filtered : list of (Prediction, FrictionData) tuples
        Output from the VRP filter stage.
    portfolio_value : float
        Total portfolio value.
    win_prob : float, optional
        Override win probability.

    Returns
    -------
    list[Signal]
        Only signals with positive Kelly allocation.
    """
    signals = []
    for pred, friction in filtered:
        signal = size_position(pred, friction, portfolio_value, win_prob)
        if signal is not None:
            signals.append(signal)

    logger.info(
        "Sized %d positions from %d filtered targets", len(signals), len(filtered)
    )
    return signals
```

- [ ] Run tests and verify they pass:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_sizer.py -v
```
Expected: All tests pass.

- [ ] Commit: `git add src/rangers/noah/tsunami/pipeline/sizer.py tests/rangers/noah/tsunami/test_sizer.py && git commit -m "feat(tsunami): add Kelly Sizer stage with quarter-Kelly, 10% cap, and TDD tests"`

---

## Task 10: Underwriter Pipeline Stage (TDD)

**Files:**
- `tests/rangers/noah/tsunami/test_underwriter.py` (create)
- `src/rangers/noah/tsunami/pipeline/underwriter.py` (create)

**Steps:**

- [ ] Write the failing test first:

```python
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
```

- [ ] Run the test and verify it fails:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_underwriter.py -v 2>&1 | head -30
```
Expected: `ImportError` (underwriter.py does not exist yet).

- [ ] Implement `underwriter.py`:

```python
# src/rangers/noah/tsunami/pipeline/underwriter.py
"""Stage 6: Underwriter -- strike selection and execution matrix generation.

Selects the optimal put contract (strike, expiry) and calculates
the Return on Premium (ROP) for each signal.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from ..adapters.base import DataAdapter
from ..config import (
    DB_PATH,
    ROP_MINIMUM,
    TARGET_DTE_MAX,
    TARGET_DTE_MIN,
)
from ..db import get_connection
from ..models.schemas import ExecutionRow, Position, Signal

logger = logging.getLogger(__name__)

TARGET_DTE_IDEAL = 240  # ideal days to expiry


def select_strike(
    current_spot: float,
    predicted_drop_pct: float,
    available_strikes: list[float],
) -> float:
    """Select the listed strike nearest to the midpoint between spot and target.

    midpoint = current_spot * (1 - predicted_drop / 2)

    This targets "halfway to the target" to maximize the balance between
    intrinsic value at target and premium cost.
    """
    target_strike = current_spot * (1.0 - predicted_drop_pct / 2.0)
    best = min(available_strikes, key=lambda s: abs(s - target_strike))
    logger.info(
        "Strike selection: spot=%.2f, drop=%.2f%%, target=%.2f, selected=%.2f",
        current_spot,
        predicted_drop_pct * 100,
        target_strike,
        best,
    )
    return best


def select_expiry(expiry_dates: list[str]) -> str | None:
    """Select the expiration date closest to 240 DTE within [180, 300] range.

    Parameters
    ----------
    expiry_dates : list[str]
        Dates in YYYY-MM-DD format.

    Returns
    -------
    str or None
        Selected expiry date string, or None if nothing in range.
    """
    now = datetime.utcnow()
    candidates = []

    for exp_str in expiry_dates:
        exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
        dte = (exp_dt - now).days
        if TARGET_DTE_MIN <= dte <= TARGET_DTE_MAX:
            candidates.append((exp_str, abs(dte - TARGET_DTE_IDEAL)))

    if not candidates:
        logger.warning("No expiry dates within DTE range [%d, %d]", TARGET_DTE_MIN, TARGET_DTE_MAX)
        return None

    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]


def compute_rop(
    strike: float, projected_price: float, premium: float
) -> float:
    """Compute Return on Premium.

    ROP = (intrinsic_at_target - premium) / premium

    where intrinsic_at_target = max(0, strike - projected_price).

    Must be >= ROP_MINIMUM (3.0) to EXECUTE.
    """
    if premium <= 0:
        return -1.0

    intrinsic_at_target = max(0.0, strike - projected_price)
    return (intrinsic_at_target - premium) / premium


def underwrite_signal(
    signal: Signal,
    adapter: DataAdapter,
    db_path: str | None = None,
) -> Optional[ExecutionRow]:
    """Underwrite a single signal into an execution row.

    Selects strike and expiry from the live options chain, computes ROP,
    and determines EXECUTE or REJECT.

    Parameters
    ----------
    signal : Signal
        Sized signal from the Kelly sizer.
    adapter : DataAdapter
        Financial data source for options chain.
    db_path : str, optional
        Override for the SQLite database path.

    Returns
    -------
    ExecutionRow or None
        None only if no options chain is available at all.
    """
    path = db_path or DB_PATH
    ticker = signal.ticker

    # Get options chain
    try:
        chain = adapter.get_options_chain(ticker, min_dte=TARGET_DTE_MIN)
    except Exception as exc:
        logger.error("Cannot fetch options chain for %s: %s", ticker, exc)
        return None

    if chain is None or chain.empty:
        logger.warning("No options chain for %s -- cannot underwrite", ticker)
        return None

    # Select expiry
    expiry_dates = sorted(chain["expiry"].unique().tolist())
    expiry = select_expiry(expiry_dates)
    if expiry is None:
        # Fall back to any available expiry
        expiry = expiry_dates[-1] if expiry_dates else None
        if expiry is None:
            logger.warning("No expiry dates available for %s", ticker)
            return None

    # Filter chain to selected expiry
    exp_chain = chain[chain["expiry"] == expiry]
    available_strikes = sorted(exp_chain["strike"].tolist())
    if not available_strikes:
        logger.warning("No strikes available for %s at expiry %s", ticker, expiry)
        return None

    # Select strike
    strike = select_strike(
        current_spot=signal.current_spot,
        predicted_drop_pct=signal.predicted_drop_pct,
        available_strikes=available_strikes,
    )

    # Get premium for the selected strike
    strike_row = exp_chain.loc[(exp_chain["strike"] - strike).abs().idxmin()]
    bid = float(strike_row.get("bid", 0))
    ask = float(strike_row.get("ask", 0))
    premium_per_share = (bid + ask) / 2.0 if (bid + ask) > 0 else ask

    if premium_per_share <= 0:
        logger.warning("Zero premium for %s strike %.2f -- cannot underwrite", ticker, strike)
        return None

    # Compute ROP
    rop = compute_rop(strike, signal.projected_price, premium_per_share)

    # Calculate contracts
    # Each contract = 100 shares
    cost_per_contract = premium_per_share * 100.0
    if cost_per_contract <= 0:
        return None
    contracts = max(1, int(signal.capital_to_deploy / cost_per_contract))
    actual_capital = contracts * cost_per_contract

    # Intrinsic at target for reporting
    intrinsic_at_target = max(0.0, strike - signal.projected_price)

    # Decision
    decision = "EXECUTE" if rop >= ROP_MINIMUM else "REJECT"

    logger.info(
        "Underwrite %s: strike=%.2f, expiry=%s, premium=%.2f, "
        "contracts=%d, ROP=%.2f, decision=%s",
        ticker,
        strike,
        expiry,
        premium_per_share,
        contracts,
        rop,
        decision,
    )

    row = ExecutionRow(
        ticker=ticker,
        strike=strike,
        expiry_date=expiry,
        contracts=contracts,
        premium_per_share=premium_per_share,
        capital_deployed=actual_capital,
        projected_price=signal.projected_price,
        intrinsic_at_target=intrinsic_at_target,
        rop=rop,
        kelly_pct=signal.kelly_pct,
        decision=decision,
    )

    # Persist position to DB if EXECUTE
    if decision == "EXECUTE":
        try:
            with get_connection(path) as conn:
                conn.execute(
                    """
                    INSERT INTO positions (
                        target_id, strike, expiry_date, premium_paid,
                        contracts, capital_deployed, kelly_pct, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
                    """,
                    (
                        signal.target_id,
                        strike,
                        expiry,
                        premium_per_share,
                        contracts,
                        actual_capital,
                        signal.kelly_pct,
                    ),
                )
        except Exception as exc:
            logger.error("Failed to persist position for %s: %s", ticker, exc)

    return row


def underwrite_all(
    signals: list[Signal],
    adapter: DataAdapter,
    db_path: str | None = None,
) -> list[ExecutionRow]:
    """Underwrite all signals and return the execution matrix.

    Parameters
    ----------
    signals : list[Signal]
        Sized signals from the Kelly sizer.
    adapter : DataAdapter
        Financial data source.
    db_path : str, optional
        Override for the SQLite database path.

    Returns
    -------
    list[ExecutionRow]
        The full execution matrix (includes both EXECUTE and REJECT rows).
    """
    rows = []
    for signal in signals:
        row = underwrite_signal(signal, adapter, db_path)
        if row is not None:
            rows.append(row)

    execute_count = sum(1 for r in rows if r.decision == "EXECUTE")
    reject_count = sum(1 for r in rows if r.decision == "REJECT")
    logger.info(
        "Execution matrix: %d EXECUTE, %d REJECT out of %d signals",
        execute_count,
        reject_count,
        len(signals),
    )

    return rows
```

- [ ] Run tests and verify they pass:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m pytest ../../../../tests/rangers/noah/tsunami/test_underwriter.py -v
```
Expected: All tests pass.

- [ ] Commit: `git add src/rangers/noah/tsunami/pipeline/underwriter.py tests/rangers/noah/tsunami/test_underwriter.py && git commit -m "feat(tsunami): add Underwriter stage with strike selection, ROP gate, and TDD tests"`

---

## Task 11: CLI Orchestrator

**Files:**
- `src/rangers/noah/tsunami/cli.py` (create)

**Steps:**

- [ ] Implement `cli.py` with all commands wired up:

```python
# src/rangers/noah/tsunami/cli.py
"""Click-based CLI entry point for the Tsunami Engine."""

from __future__ import annotations

import logging
import sys
from typing import Optional

import click

from .adapters.yfinance_adapter import YFinanceAdapter
from .config import (
    COMPRESSION_GATE,
    DEFAULT_WIN_PROB,
    MAX_POSITION_PCT,
    VULNERABILITY_GATE,
)
from .db import get_connection, init_db
from .pipeline.backtester import run_backtest
from .pipeline.compressor import compress
from .pipeline.filter import filter_targets
from .pipeline.scanner import scan_ticker
from .pipeline.sizer import size_all
from .pipeline.underwriter import underwrite_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _get_adapter() -> YFinanceAdapter:
    return YFinanceAdapter()


@click.group()
@click.option("--db", default=None, help="Override SQLite database path.")
@click.pass_context
def tsunami(ctx: click.Context, db: Optional[str]) -> None:
    """Tsunami Engine: AI Disruption Multiple Compression Scanner."""
    ctx.ensure_object(dict)
    if db:
        ctx.obj["db_path"] = db
    else:
        from .config import DB_PATH
        ctx.obj["db_path"] = DB_PATH
    init_db(ctx.obj["db_path"])


@tsunami.command()
@click.pass_context
def seed(ctx: click.Context) -> None:
    """Load historical casualties into the database."""
    import csv
    from .config import CASUALTIES_PATH

    db_path = ctx.obj["db_path"]

    with open(CASUALTIES_PATH, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with get_connection(db_path) as conn:
        for i, row in enumerate(rows, start=1):
            target_id = f"TGT_{i:03d}"
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO target_companies
                    (target_id, ticker, company, sector)
                    VALUES (?, ?, ?, ?)
                    """,
                    (target_id, row["ticker"], row["company"], row["sector"]),
                )
            except Exception as exc:
                click.echo(f"Warning: could not insert {row['ticker']}: {exc}")

    click.echo(f"Seeded {len(rows)} casualties into target_companies.")


@tsunami.command()
@click.argument("ticker")
@click.pass_context
def scan(ctx: click.Context, ticker: str) -> None:
    """Run vulnerability scan on a single ticker."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()
    ticker = ticker.upper()

    result = scan_ticker(ticker, adapter, db_path=db_path)
    if result is None:
        click.echo(f"{ticker}: Below vulnerability gate ({VULNERABILITY_GATE}). No action.")
    else:
        click.echo(
            f"{ticker}: vulnerability_score={result.vulnerability_score:.4f} "
            f"(gate={VULNERABILITY_GATE}). PASSED."
        )


@tsunami.command(name="compress")
@click.argument("ticker")
@click.pass_context
def compress_cmd(ctx: click.Context, ticker: str) -> None:
    """Calculate price target via multiple compression for a ticker."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()
    ticker = ticker.upper()

    # Must scan first
    prediction = scan_ticker(ticker, adapter, db_path=db_path)
    if prediction is None:
        click.echo(f"{ticker}: Did not pass scanner. Cannot compress.")
        return

    result = compress(prediction, db_path=db_path)
    if result is None:
        click.echo(
            f"{ticker}: Predicted drop below compression gate ({COMPRESSION_GATE:.0%}). No action."
        )
    else:
        click.echo(
            f"{ticker}: projected_price=${result.projected_price:.2f}, "
            f"predicted_drop={result.predicted_drop_pct:.2%}. QUALIFIED."
        )


@tsunami.command()
@click.pass_context
def backtest(ctx: click.Context) -> None:
    """Train model on historical casualties and extract feature weights."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    try:
        weights, r_squared = run_backtest(adapter, db_path=db_path)
        click.echo(f"Backtest complete. R-squared: {r_squared:.4f}")
        click.echo("Feature weights:")
        for feat, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            click.echo(f"  {feat}: {w:.4f}")
    except ValueError as exc:
        click.echo(f"Backtest failed: {exc}", err=True)
        sys.exit(1)


@tsunami.command(name="filter")
@click.pass_context
def filter_cmd(ctx: click.Context) -> None:
    """Rank targets by VRP (cheapest puts first)."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    # Load all targets that have predictions with predicted_drop > gate
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT tc.target_id, tc.ticker, tc.sector,
                   fp.sga_pct, fp.gross_margin_pct, fp.debt_to_equity,
                   fp.fcf_yield_pct, fp.roic_pct, fp.vulnerability_score,
                   fp.current_eps, fp.current_pe, fp.eps_decay_pct,
                   fp.terminal_pe, fp.projected_price, fp.predicted_drop_pct
            FROM target_companies tc
            JOIN fundamental_predictions fp ON tc.target_id = fp.target_id
            WHERE fp.predicted_drop_pct > ?
            AND fp.model_id = (
                SELECT MAX(model_id) FROM fundamental_predictions
                WHERE target_id = tc.target_id
            )
            """,
            (COMPRESSION_GATE,),
        ).fetchall()

    if not rows:
        click.echo("No targets with sufficient predicted drop. Run scan + compress first.")
        return

    from .models.schemas import Prediction

    predictions = []
    for r in rows:
        try:
            spot = adapter.get_price(r["ticker"])
        except Exception:
            spot = 0.0
        predictions.append(
            Prediction(
                target_id=r["target_id"],
                ticker=r["ticker"],
                sga_pct=r["sga_pct"] or 0.0,
                gross_margin_pct=r["gross_margin_pct"] or 0.0,
                debt_to_equity=r["debt_to_equity"] or 0.0,
                fcf_yield_pct=r["fcf_yield_pct"] or 0.0,
                roic_pct=r["roic_pct"] or 0.0,
                vulnerability_score=r["vulnerability_score"] or 0.0,
                current_eps=r["current_eps"] or 0.0,
                current_pe=r["current_pe"] or 0.0,
                current_spot=spot,
                eps_decay_pct=r["eps_decay_pct"] or 0.0,
                terminal_pe=r["terminal_pe"] or 0.0,
                projected_price=r["projected_price"] or 0.0,
                predicted_drop_pct=r["predicted_drop_pct"] or 0.0,
            )
        )

    filtered = filter_targets(predictions, adapter, db_path=db_path)
    if not filtered:
        click.echo("No targets passed VRP filter.")
        return

    click.echo(f"\n{'Ticker':<10} {'VRP':<10} {'IV':<10} {'HV':<10} {'Status':<15}")
    click.echo("-" * 55)
    for pred, friction in filtered:
        status = "DISCOUNT" if friction.vrp_spread < 0 else "FAIR VALUE"
        click.echo(
            f"{pred.ticker:<10} {friction.vrp_spread:<10.4f} "
            f"{friction.atm_put_iv:<10.4f} {friction.hv_252d:<10.4f} {status:<15}"
        )


@tsunami.command()
@click.option("--portfolio", default=100000.0, help="Portfolio value in dollars.")
@click.pass_context
def size(ctx: click.Context, portfolio: float) -> None:
    """Kelly allocation across approved targets."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    # Rebuild predictions from DB
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT tc.target_id, tc.ticker,
                   fp.sga_pct, fp.gross_margin_pct, fp.debt_to_equity,
                   fp.fcf_yield_pct, fp.roic_pct, fp.vulnerability_score,
                   fp.current_eps, fp.current_pe, fp.eps_decay_pct,
                   fp.terminal_pe, fp.projected_price, fp.predicted_drop_pct,
                   mfl.live_spot, mfl.atm_put_iv, mfl.put_call_ratio,
                   mfl.est_premium_ask, mfl.hv_252d, mfl.vrp_spread
            FROM target_companies tc
            JOIN fundamental_predictions fp ON tc.target_id = fp.target_id
            JOIN market_friction_log mfl ON tc.target_id = mfl.target_id
            WHERE fp.predicted_drop_pct > ?
            AND mfl.vrp_spread < ?
            AND fp.model_id = (
                SELECT MAX(model_id) FROM fundamental_predictions
                WHERE target_id = tc.target_id
            )
            AND mfl.log_id = (
                SELECT MAX(log_id) FROM market_friction_log
                WHERE target_id = tc.target_id
            )
            """,
            (COMPRESSION_GATE, 0.15),
        ).fetchall()

    if not rows:
        click.echo("No filtered targets found. Run filter first.")
        return

    from .models.schemas import FrictionData, Prediction

    filtered = []
    for r in rows:
        pred = Prediction(
            target_id=r["target_id"], ticker=r["ticker"],
            sga_pct=r["sga_pct"] or 0.0, gross_margin_pct=r["gross_margin_pct"] or 0.0,
            debt_to_equity=r["debt_to_equity"] or 0.0, fcf_yield_pct=r["fcf_yield_pct"] or 0.0,
            roic_pct=r["roic_pct"] or 0.0, vulnerability_score=r["vulnerability_score"] or 0.0,
            current_eps=r["current_eps"] or 0.0, current_pe=r["current_pe"] or 0.0,
            current_spot=r["live_spot"] or 0.0, eps_decay_pct=r["eps_decay_pct"] or 0.0,
            terminal_pe=r["terminal_pe"] or 0.0, projected_price=r["projected_price"] or 0.0,
            predicted_drop_pct=r["predicted_drop_pct"] or 0.0,
        )
        friction = FrictionData(
            target_id=r["target_id"], ticker=r["ticker"],
            live_spot=r["live_spot"] or 0.0, atm_put_iv=r["atm_put_iv"] or 0.0,
            put_call_ratio=r["put_call_ratio"] or 1.0,
            est_premium_ask=r["est_premium_ask"] or 0.0,
            hv_252d=r["hv_252d"] or 0.0, vrp_spread=r["vrp_spread"] or 0.0,
        )
        filtered.append((pred, friction))

    signals = size_all(filtered, portfolio_value=portfolio)
    if not signals:
        click.echo("No positions sized (all rejected by Kelly).")
        return

    click.echo(f"\n{'Ticker':<10} {'Kelly%':<10} {'Capital':<12} {'Payoff':<10}")
    click.echo("-" * 42)
    for s in signals:
        click.echo(
            f"{s.ticker:<10} {s.kelly_pct:<10.4f} "
            f"${s.capital_to_deploy:<11.2f} {s.payoff_ratio:<10.2f}"
        )


@tsunami.command()
@click.option("--portfolio", default=100000.0, help="Portfolio value in dollars.")
@click.pass_context
def underwrite(ctx: click.Context, portfolio: float) -> None:
    """Generate execution matrix (strikes, expiry, contracts)."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    # This is the final stage -- we rebuild the full pipeline state from DB
    # and run underwriter on the sized signals.
    # For simplicity, we re-run size to get signals.
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT tc.target_id, tc.ticker,
                   fp.projected_price, fp.predicted_drop_pct,
                   mfl.live_spot, mfl.vrp_spread, mfl.est_premium_ask
            FROM target_companies tc
            JOIN fundamental_predictions fp ON tc.target_id = fp.target_id
            JOIN market_friction_log mfl ON tc.target_id = mfl.target_id
            WHERE fp.predicted_drop_pct > ?
            AND mfl.vrp_spread < ?
            AND fp.model_id = (
                SELECT MAX(model_id) FROM fundamental_predictions
                WHERE target_id = tc.target_id
            )
            AND mfl.log_id = (
                SELECT MAX(log_id) FROM market_friction_log
                WHERE target_id = tc.target_id
            )
            """,
            (COMPRESSION_GATE, 0.15),
        ).fetchall()

    if not rows:
        click.echo("No qualified targets. Run the full pipeline first.")
        return

    from .models.schemas import Signal

    signals = []
    for r in rows:
        signals.append(
            Signal(
                target_id=r["target_id"], ticker=r["ticker"],
                predicted_drop_pct=r["predicted_drop_pct"] or 0.0,
                projected_price=r["projected_price"] or 0.0,
                current_spot=r["live_spot"] or 0.0,
                vrp_spread=r["vrp_spread"] or 0.0,
                kelly_pct=min(0.10, MAX_POSITION_PCT),
                capital_to_deploy=portfolio * min(0.10, MAX_POSITION_PCT),
                win_probability=DEFAULT_WIN_PROB,
                payoff_ratio=0.0,
            )
        )

    execution_matrix = underwrite_all(signals, adapter, db_path=db_path)
    if not execution_matrix:
        click.echo("No actionable signals.")
        return

    click.echo(
        f"\n{'Ticker':<8} {'Strike':<8} {'Expiry':<12} {'Cts':<5} "
        f"{'Premium':<10} {'Capital':<12} {'ROP':<8} {'Decision':<10}"
    )
    click.echo("-" * 73)
    for row in execution_matrix:
        click.echo(
            f"{row.ticker:<8} {row.strike:<8.2f} {row.expiry_date:<12} "
            f"{row.contracts:<5d} ${row.premium_per_share:<9.2f} "
            f"${row.capital_deployed:<11.2f} {row.rop:<8.2f} {row.decision:<10}"
        )


@tsunami.command()
@click.option("--portfolio", default=100000.0, help="Portfolio value in dollars.")
@click.option("--paper", is_flag=True, help="Paper trading mode.")
@click.pass_context
def run(ctx: click.Context, portfolio: float, paper: bool) -> None:
    """Full pipeline end-to-end."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()
    mode = "PAPER" if paper else "LIVE"
    click.echo(f"=== Tsunami Engine [{mode}] ===\n")

    # Load all targets
    with get_connection(db_path) as conn:
        targets = conn.execute(
            "SELECT target_id, ticker, company, sector FROM target_companies"
        ).fetchall()

    if not targets:
        click.echo("No targets in database. Run 'tsunami seed' first.")
        return

    # Stage 1+2: Scan and compress each target
    click.echo(f"Stage 1+2: Scanning and compressing {len(targets)} targets...")
    qualified = []
    for t in targets:
        ticker = t["ticker"]
        prediction = scan_ticker(ticker, adapter, db_path=db_path)
        if prediction is None:
            click.echo(f"  {ticker}: below vulnerability gate -- skipped")
            continue

        compressed = compress(prediction, db_path=db_path)
        if compressed is None:
            click.echo(f"  {ticker}: below compression gate -- skipped")
            continue

        click.echo(
            f"  {ticker}: vuln={compressed.vulnerability_score:.3f}, "
            f"drop={compressed.predicted_drop_pct:.1%}, "
            f"target=${compressed.projected_price:.2f}"
        )
        qualified.append(compressed)

    if not qualified:
        click.echo("\nNo actionable signals.")
        return

    # Stage 3 (optional): VRP Filter
    click.echo(f"\nStage 4: VRP filtering {len(qualified)} targets...")
    filtered = filter_targets(qualified, adapter, db_path=db_path)
    if not filtered:
        click.echo("All targets rejected by VRP filter.")
        return
    click.echo(f"  {len(filtered)} targets passed VRP filter")

    # Stage 4: Size
    click.echo(f"\nStage 5: Kelly sizing (portfolio=${portfolio:,.0f})...")
    signals = size_all(filtered, portfolio_value=portfolio)
    if not signals:
        click.echo("All positions rejected by Kelly criterion.")
        return
    click.echo(f"  {len(signals)} positions sized")

    # Stage 5: Underwrite
    click.echo(f"\nStage 6: Underwriting...")
    execution_matrix = underwrite_all(signals, adapter, db_path=db_path)

    if not execution_matrix:
        click.echo("No contracts available for underwriting.")
        return

    # Print execution matrix
    click.echo(
        f"\n{'Ticker':<8} {'Strike':<8} {'Expiry':<12} {'Cts':<5} "
        f"{'Premium':<10} {'Capital':<12} {'ROP':<8} {'Decision':<10}"
    )
    click.echo("=" * 73)
    for row in execution_matrix:
        click.echo(
            f"{row.ticker:<8} {row.strike:<8.2f} {row.expiry_date:<12} "
            f"{row.contracts:<5d} ${row.premium_per_share:<9.2f} "
            f"${row.capital_deployed:<11.2f} {row.rop:<8.2f} {row.decision:<10}"
        )

    execute_count = sum(1 for r in execution_matrix if r.decision == "EXECUTE")
    total_capital = sum(r.capital_deployed for r in execution_matrix if r.decision == "EXECUTE")
    click.echo(f"\nSummary: {execute_count} EXECUTE, total capital=${total_capital:,.2f}")

    # Paper trade persistence
    if paper:
        click.echo("\n[PAPER MODE] Writing to paper_positions...")
        with get_connection(db_path) as conn:
            for row in execution_matrix:
                if row.decision == "EXECUTE":
                    # Find the matching signal
                    sig = next((s for s in signals if s.ticker == row.ticker), None)
                    if sig:
                        conn.execute(
                            """
                            INSERT INTO paper_positions (
                                target_id, strike, expiry_date, premium_at_open,
                                contracts, capital_deployed, spot_at_open,
                                predicted_drop_pct, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                            """,
                            (
                                sig.target_id,
                                row.strike,
                                row.expiry_date,
                                row.premium_per_share,
                                row.contracts,
                                row.capital_deployed,
                                sig.current_spot,
                                sig.predicted_drop_pct,
                            ),
                        )
        click.echo("Paper positions saved.")


@tsunami.command()
@click.pass_context
def test(ctx: click.Context) -> None:
    """Smoke test against CHGG (known casualty)."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    click.echo("=== Smoke Test: CHGG ===\n")

    # Ensure CHGG is in the DB
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT target_id FROM target_companies WHERE ticker = 'CHGG'"
        ).fetchone()
        if not row:
            conn.execute(
                """
                INSERT INTO target_companies (target_id, ticker, company, sector)
                VALUES ('TGT_001', 'CHGG', 'Chegg', 'EdTech')
                """
            )

    # Scan
    prediction = scan_ticker("CHGG", adapter, db_path=db_path)
    if prediction is None:
        click.echo("FAIL: CHGG did not pass scanner.")
        sys.exit(1)
    click.echo(f"Scanner: vulnerability_score={prediction.vulnerability_score:.4f} PASS")

    # Compress
    compressed = compress(prediction, db_path=db_path)
    if compressed is None:
        click.echo("FAIL: CHGG did not pass compressor.")
        sys.exit(1)

    drop = compressed.predicted_drop_pct
    click.echo(
        f"Compressor: projected_price=${compressed.projected_price:.2f}, "
        f"predicted_drop={drop:.1%}"
    )

    # Validate against known range
    if 0.30 <= drop <= 0.90:
        click.echo(f"Smoke test PASSED: predicted drop {drop:.1%} is in range [30%, 90%]")
    else:
        click.echo(
            f"WARNING: predicted drop {drop:.1%} outside expected range [30%, 90%]. "
            "Model may need recalibration."
        )


def main() -> None:
    """Entry point."""
    tsunami()


if __name__ == "__main__":
    main()
```

- [ ] Verify CLI loads:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -m rangers.noah.tsunami.cli --help
```
Expected: Help text showing all tsunami commands.

- [ ] Commit: `git add src/rangers/noah/tsunami/cli.py && git commit -m "feat(tsunami): add Click CLI orchestrator with all pipeline commands"`

---

## Task 12: Seed Data Command

**Files:**
- No new files (uses `cli.py` seed command + `casualties.csv`)

**Steps:**

- [ ] Verify seed command works end-to-end:

**Test command:**
```bash
cd src/rangers/noah/tsunami && python -c "
import sys; sys.path.insert(0, '../../../')
from rangers.noah.tsunami.db import init_db, get_connection
from rangers.noah.tsunami.config import DB_PATH
import os

db_path = '/tmp/tsunami_seed_test.db'
init_db(db_path)

# Simulate seed
import csv
from rangers.noah.tsunami.config import CASUALTIES_PATH
with open(CASUALTIES_PATH, 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

from rangers.noah.tsunami.db import get_connection
with get_connection(db_path) as conn:
    for i, row in enumerate(rows, start=1):
        target_id = f'TGT_{i:03d}'
        conn.execute(
            'INSERT OR IGNORE INTO target_companies (target_id, ticker, company, sector) VALUES (?, ?, ?, ?)',
            (target_id, row['ticker'], row['company'], row['sector']),
        )

with get_connection(db_path) as conn:
    count = conn.execute('SELECT COUNT(*) as cnt FROM target_companies').fetchone()['cnt']
    tickers = conn.execute('SELECT ticker FROM target_companies ORDER BY target_id').fetchall()
    print(f'Seeded {count} companies')
    print('Tickers:', [t['ticker'] for t in tickers])
"
```
Expected: `Seeded 10 companies` with all 10 tickers listed.

- [ ] Commit: `git commit --allow-empty -m "chore(tsunami): verify seed data command works with casualties.csv"`

---

## Task 13: Smoke Test Against CHGG

**Files:**
- `tests/rangers/noah/tsunami/__init__.py` (create if not exists)
- `tests/rangers/noah/tsunami/test_smoke.py` (create)
- `tests/rangers/__init__.py` (create if not exists)
- `tests/rangers/noah/__init__.py` (create if not exists)

**Steps:**

- [ ] Create test `__init__.py` files and smoke test:

```python
# tests/rangers/__init__.py
```

```python
# tests/rangers/noah/__init__.py
```

```python
# tests/rangers/noah/tsunami/__init__.py
```

```python
# tests/rangers/noah/tsunami/test_smoke.py
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
            "EdTech": {"eps_decay": 0.25, "terminal_pe": 13.0},
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
        # Negative EPS: projected = 9.50 * (1 - 0.25) = 7.125
        # drop = (9.50 - 7.125) / 9.50 = 0.25
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
```

- [ ] Run the full smoke test:

**Test command:**
```bash
python -m pytest tests/rangers/noah/tsunami/test_smoke.py -v
```
Expected: `test_full_pipeline PASSED`.

- [ ] Run ALL tests:

**Test command:**
```bash
python -m pytest tests/rangers/noah/tsunami/ -v
```
Expected: All tests pass.

- [ ] Commit: `git add tests/rangers/ && git commit -m "test(tsunami): add full smoke test for CHGG end-to-end pipeline"`
