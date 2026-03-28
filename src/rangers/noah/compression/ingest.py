"""
Phase 1: Data Ingestion
Loads all data from agent_drops/data/ into unified structures.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path


def _find_data_dir():
    """Locate agent_drops/data/ relative to project root."""
    candidates = [
        Path(__file__).resolve().parents[4] / "agent_drops" / "data",
        Path.cwd() / "agent_drops" / "data",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Cannot find agent_drops/data/. Run collect_all_market_data.py first.")


def load_stock_prices(data_dir: Path) -> pd.DataFrame:
    """Load combined 5yr daily OHLCV for all tickers."""
    path = data_dir / "stocks" / "all_tickers_5y_daily.csv"
    if not path.exists():
        # Fall back to individual files
        stocks_dir = data_dir / "stocks"
        frames = []
        for f in stocks_dir.glob("*_5y.csv"):
            ticker = f.stem.replace("_5y", "").replace("IDX_", "^").replace("_", "-")
            df = pd.read_csv(f, parse_dates=["Date"], index_col="Date")
            df["ticker"] = ticker
            frames.append(df)
        if not frames:
            raise FileNotFoundError("No stock data found")
        return pd.concat(frames)

    df = pd.read_csv(path, header=[0, 1], index_col=0, parse_dates=True)
    return df


def load_fundamentals(data_dir: Path) -> pd.DataFrame:
    """Load current fundamentals for top 50 stocks."""
    path = data_dir / "stocks" / "fundamentals_top50.json"
    if not path.exists():
        return pd.DataFrame()
    with open(path) as f:
        data = json.load(f)
    return pd.DataFrame(data)


def load_fred_series(data_dir: Path) -> dict[str, pd.Series]:
    """Load all FRED economic series as {name: Series}."""
    econ_dir = data_dir / "economic"
    series = {}
    if not econ_dir.exists():
        return series
    for f in econ_dir.glob("*.csv"):
        name = f.stem
        try:
            df = pd.read_csv(f, parse_dates=["DATE"])
            df = df.rename(columns={df.columns[-1]: "value"})
            df = df.dropna(subset=["value"])
            # FRED sometimes has "." for missing
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna(subset=["value"])
            df = df.set_index("DATE").sort_index()
            series[name] = df["value"]
        except Exception:
            continue
    return series


def load_kalshi(data_dir: Path) -> dict:
    """Load Kalshi markets (settled + open)."""
    kalshi_dir = data_dir / "kalshi"
    result = {"settled": [], "open": [], "events": []}
    if not kalshi_dir.exists():
        return result
    for f in kalshi_dir.glob("markets_settled_*.json"):
        with open(f) as fh:
            data = json.load(fh)
            result["settled"].extend(data.get("markets", []))
    for f in kalshi_dir.glob("markets_open_*.json"):
        with open(f) as fh:
            data = json.load(fh)
            result["open"].extend(data.get("markets", []))
    events_path = kalshi_dir / "events_open.json"
    if events_path.exists():
        with open(events_path) as fh:
            data = json.load(fh)
            result["events"] = data.get("events", [])
    return result


def load_crypto(data_dir: Path) -> dict[str, pd.DataFrame]:
    """Load crypto daily prices."""
    crypto_dir = data_dir / "crypto"
    coins = {}
    if not crypto_dir.exists():
        return coins
    for f in crypto_dir.glob("*.json"):
        name = f.stem.replace("_1y", "")
        with open(f) as fh:
            data = json.load(fh)
        prices = data.get("prices", [])
        if prices:
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.set_index("date")[["price"]]
            coins[name] = df
    return coins


def load_all_data(data_path: str = None) -> dict:
    """Load everything into a unified dict."""
    data_dir = Path(data_path) if data_path else _find_data_dir()
    print(f"  Loading from {data_dir}")

    data = {}
    try:
        data["stock_prices"] = load_stock_prices(data_dir)
        print(f"  ✓ Stock prices: {data['stock_prices'].shape}")
    except Exception as e:
        print(f"  ✗ Stock prices: {e}")
        data["stock_prices"] = pd.DataFrame()

    data["fundamentals"] = load_fundamentals(data_dir)
    print(f"  ✓ Fundamentals: {len(data['fundamentals'])} companies")

    data["fred"] = load_fred_series(data_dir)
    print(f"  ✓ FRED series: {len(data['fred'])} series")

    data["kalshi"] = load_kalshi(data_dir)
    print(f"  ✓ Kalshi: {len(data['kalshi']['settled'])} settled, {len(data['kalshi']['open'])} open")

    data["crypto"] = load_crypto(data_dir)
    print(f"  ✓ Crypto: {list(data['crypto'].keys())}")

    return data
