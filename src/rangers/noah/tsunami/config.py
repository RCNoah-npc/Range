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
