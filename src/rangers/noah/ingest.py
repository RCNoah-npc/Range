"""
Data ingestion module — loads all market data from agent_drops/data/
"""
import os
import json
import pandas as pd
from pathlib import Path


def find_data_dir():
    """Walk up from this file to find agent_drops/data/"""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / "agent_drops" / "data"
        if candidate.exists():
            return candidate
        current = current.parent
    raise FileNotFoundError("Cannot find agent_drops/data/ — run collect_all_market_data.py first")


def load_stock_prices(data_dir):
    """Load the combined 5yr daily CSV."""
    path = data_dir / "stocks" / "all_tickers_5y_daily.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    df = pd.read_csv(path, header=[0, 1], index_col=0, parse_dates=True)
    return df


def load_individual_ticker(data_dir, ticker):
    """Load a single ticker's 5yr CSV."""
    safe = ticker.replace("^", "IDX_").replace("-", "_")
    path = data_dir / "stocks" / f"{safe}_5y.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df


def load_fundamentals(data_dir):
    """Load current fundamentals JSON."""
    path = data_dir / "stocks" / "fundamentals_top50.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_fred_series(data_dir, name):
    """Load a single FRED CSV (DATE, VALUE columns)."""
    path = data_dir / "economic" / f"{name}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["DATE"])
    df = df.rename(columns={df.columns[-1]: "VALUE"})
    df["VALUE"] = pd.to_numeric(df["VALUE"], errors="coerce")
    df = df.dropna(subset=["VALUE"])
    df = df.set_index("DATE").sort_index()
    return df


def load_all_fred(data_dir):
    """Load all FRED series into a dict."""
    econ_dir = data_dir / "economic"
    if not econ_dir.exists():
        return {}
    series = {}
    for f in econ_dir.glob("*.csv"):
        name = f.stem
        df = load_fred_series(data_dir, name)
        if df is not None and len(df) > 0:
            series[name] = df
    return series


def load_kalshi_markets(data_dir, status="settled"):
    """Load Kalshi markets JSON files."""
    kalshi_dir = data_dir / "kalshi"
    if not kalshi_dir.exists():
        return []
    markets = []
    for f in sorted(kalshi_dir.glob(f"markets_{status}_*.json")):
        with open(f) as fh:
            data = json.load(fh)
            markets.extend(data.get("markets", []))
    return markets


def load_all_data():
    """Master loader — returns everything in a dict."""
    data_dir = find_data_dir()
    print(f"  Data directory: {data_dir}")

    data = {
        "data_dir": data_dir,
        "fundamentals": load_fundamentals(data_dir),
        "fred": load_all_fred(data_dir),
        "kalshi_settled": load_kalshi_markets(data_dir, "settled"),
        "kalshi_open": load_kalshi_markets(data_dir, "open"),
    }

    # Load individual tickers for the ones we have fundamentals for
    tickers = [f["ticker"] for f in data["fundamentals"]]
    ticker_data = {}
    for t in tickers:
        df = load_individual_ticker(data_dir, t)
        if df is not None:
            ticker_data[t] = df
    data["tickers"] = ticker_data

    # Load key indices
    for idx in ["^GSPC", "^VIX", "^TNX"]:
        df = load_individual_ticker(data_dir, idx)
        if df is not None:
            ticker_data[idx] = df
    # Load key ETFs
    for etf in ["SPY", "XLK", "XLF", "XLE", "XLV", "TLT", "HYG"]:
        df = load_individual_ticker(data_dir, etf)
        if df is not None:
            ticker_data[etf] = df

    print(f"  Loaded: {len(ticker_data)} tickers, {len(data['fred'])} FRED series, "
          f"{len(data['fundamentals'])} fundamentals, "
          f"{len(data['kalshi_settled'])} settled Kalshi markets")
    return data
