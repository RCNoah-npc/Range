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
