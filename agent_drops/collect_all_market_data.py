"""
Market & Economic Training Data Collector
==========================================
Drop this in: agent_drops/ within the Range project
Run it and it creates agent_drops/data/ with everything.

Sources: Kalshi (prediction markets), Yahoo Finance (stocks), FRED (macro), CoinGecko (crypto)
No API keys needed.

Usage:
    pip install yfinance pandas requests
    python collect_all_market_data.py
"""

import os
import json
import time
import requests
import pandas as pd

# ── Config ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

KALSHI_DIR = os.path.join(DATA_DIR, "kalshi")
STOCKS_DIR = os.path.join(DATA_DIR, "stocks")
ECON_DIR   = os.path.join(DATA_DIR, "economic")
CRYPTO_DIR = os.path.join(DATA_DIR, "crypto")

for d in [KALSHI_DIR, STOCKS_DIR, ECON_DIR, CRYPTO_DIR]:
    os.makedirs(d, exist_ok=True)

KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"

TICKERS_INDICES  = ["^GSPC", "^DJI", "^IXIC", "^VIX", "^RUT", "^TNX"]
TICKERS_ETFS     = ["SPY", "QQQ", "IWM", "DIA", "VTI", "GLD", "SLV", "TLT",
                    "HYG", "XLF", "XLK", "XLE", "XLV", "XLI"]
TICKERS_MEGACAP  = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "JPM", "V", "UNH", "MA", "HD", "PG", "JNJ", "XOM", "BAC", "ABBV",
    "KO", "PEP", "MRK", "COST", "AVGO", "TMO", "WMT", "CRM", "ACN",
    "LLY", "MCD", "CSCO", "ADBE", "AMD", "NFLX", "INTC", "QCOM",
    "TXN", "PM", "HON", "UPS", "GS", "CAT", "BA", "DE", "RTX",
    "SCHW", "AMAT", "NOW", "ISRG", "GE", "PLD",
]
ALL_TICKERS = TICKERS_INDICES + TICKERS_ETFS + TICKERS_MEGACAP

FRED_SERIES = {
    "GDP": "GDP", "REAL_GDP": "GDPC1",
    "CPI": "CPIAUCSL", "CORE_CPI": "CPILFESL",
    "PCE": "PCEPI", "CORE_PCE": "PCEPILFE",
    "UNEMPLOYMENT": "UNRATE", "NONFARM_PAYROLL": "PAYEMS",
    "INITIAL_CLAIMS": "ICSA",
    "FED_FUNDS_RATE": "FEDFUNDS",
    "10Y_TREASURY": "DGS10", "2Y_TREASURY": "DGS2",
    "YIELD_SPREAD_10Y2Y": "T10Y2Y",
    "SP500": "SP500", "VIX": "VIXCLS",
    "INDUSTRIAL_PROD": "INDPRO", "RETAIL_SALES": "RSXFS",
    "HOUSING_STARTS": "HOUST", "CONSUMER_SENTIMENT": "UMCSENT",
    "M2_MONEY_SUPPLY": "M2SL", "DOLLAR_INDEX": "DTWEXBGS",
    "PERSONAL_INCOME": "PI", "PERSONAL_SAVING_RATE": "PSAVERT",
    "TRADE_BALANCE": "BOPGSTB", "BREAKEVEN_INFLATION_5Y": "T5YIE",
}

CRYPTO_COINS = ["bitcoin", "ethereum", "solana"]


# ── Helpers ─────────────────────────────────────────────────────────────
def fetch_json(url, params=None):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def safe_name(ticker):
    return ticker.replace("^", "IDX_").replace("-", "_")


# ── 1. Kalshi Prediction Markets ───────────────────────────────────────
def collect_kalshi():
    print("\n[KALSHI] Prediction Markets")
    for status in ["open", "settled"]:
        print(f"  Fetching {status} markets...")
        page = 1
        cursor = None
        while True:
            params = {"limit": 1000, "status": status}
            if cursor:
                params["cursor"] = cursor
            try:
                data = fetch_json(f"{KALSHI_BASE}/markets", params)
                fname = f"markets_{status}_p{page}.json"
                save_json(data, os.path.join(KALSHI_DIR, fname))
                count = len(data.get("markets", []))
                print(f"    + {fname} ({count} markets)")
                cursor = data.get("cursor")
                if not cursor or count == 0:
                    break
                page += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"    x {status} page {page}: {e}")
                break

    print("  Fetching events...")
    try:
        data = fetch_json(f"{KALSHI_BASE}/events", {"limit": 200, "status": "open"})
        save_json(data, os.path.join(KALSHI_DIR, "events_open.json"))
        print(f"    + events_open.json ({len(data.get('events', []))} events)")
    except Exception as e:
        print(f"    x events: {e}")


# ── 2. Stock Market Data ───────────────────────────────────────────────
def collect_stocks():
    import yfinance as yf

    print("\n[STOCKS] 5yr Daily (70 tickers)")

    # Bulk download
    print("  Bulk downloading all tickers...")
    try:
        data = yf.download(ALL_TICKERS, period="5y", interval="1d",
                          group_by="ticker", threads=True)
        data.to_csv(os.path.join(STOCKS_DIR, "all_tickers_5y_daily.csv"))
        print(f"    + all_tickers_5y_daily.csv ({data.shape[0]} rows x {data.shape[1]} cols)")
    except Exception as e:
        print(f"    x bulk download: {e}")

    # Individual tickers
    print("  Downloading individual histories...")
    for ticker in ALL_TICKERS:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5y")
            hist.to_csv(os.path.join(STOCKS_DIR, f"{safe_name(ticker)}_5y.csv"))
            print(f"    + {ticker} ({len(hist)} rows)")
        except Exception as e:
            print(f"    x {ticker}: {e}")

    # Fundamentals
    print("  Fetching fundamentals...")
    fundamentals = []
    for ticker in TICKERS_MEGACAP:
        try:
            info = yf.Ticker(ticker).info
            fundamentals.append({
                "ticker": ticker,
                "name": info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "marketCap": info.get("marketCap"),
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "dividendYield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52wHigh": info.get("fiftyTwoWeekHigh"),
                "52wLow": info.get("fiftyTwoWeekLow"),
                "avgVolume": info.get("averageVolume"),
                "revenue": info.get("totalRevenue"),
                "grossMargins": info.get("grossMargins"),
                "ebitdaMargins": info.get("ebitdaMargins"),
                "profitMargins": info.get("profitMargins"),
                "evToEbitda": info.get("enterpriseToEbitda"),
                "priceToBook": info.get("priceToBook"),
                "priceToSales": info.get("priceToSalesTrailing12Months"),
                "debtToEquity": info.get("debtToEquity"),
                "returnOnEquity": info.get("returnOnEquity"),
                "earningsGrowth": info.get("earningsGrowth"),
                "revenueGrowth": info.get("revenueGrowth"),
            })
            print(f"    + {ticker} fundamentals")
        except Exception as e:
            print(f"    x {ticker}: {e}")
    save_json(fundamentals, os.path.join(STOCKS_DIR, "fundamentals_top50.json"))


# ── 3. FRED Economic Data ─────────────────────────────────────────────
def collect_fred():
    print("\n[FRED] 25 Macroeconomic Series")
    for name, series_id in FRED_SERIES.items():
        try:
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            path = os.path.join(ECON_DIR, f"{name}.csv")
            with open(path, "wb") as f:
                f.write(r.content)
            rows = r.text.count("\n") - 1
            print(f"  + {name} ({rows} rows)")
            time.sleep(0.4)
        except Exception as e:
            print(f"  x {name}: {e}")


# ── 4. Crypto ──────────────────────────────────────────────────────────
def collect_crypto():
    print("\n[CRYPTO] Daily prices (1yr)")
    for coin in CRYPTO_COINS:
        try:
            data = fetch_json(
                f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart",
                {"vs_currency": "usd", "days": 365, "interval": "daily"},
            )
            save_json(data, os.path.join(CRYPTO_DIR, f"{coin}_1y.json"))
            days = len(data.get("prices", []))
            print(f"  + {coin} ({days} days)")
            time.sleep(2)
        except Exception as e:
            print(f"  x {coin}: {e}")


# ── 5. Write README ───────────────────────────────────────────────────
def write_readme():
    readme = """# Market & Economic Training Data
## For: Multiple Compression Signal Detection

## Structure
- `kalshi/` — Prediction market data (open + settled markets with known outcomes)
- `stocks/` — 5yr daily OHLCV for 70 tickers + fundamentals (P/E, EV/EBITDA, margins, growth)
- `economic/` — 25 FRED macro series (GDP, CPI, rates, employment, sentiment, etc.)
- `crypto/` — BTC, ETH, SOL daily prices (1yr)

## Key Files for Multiple Compression Analysis
- `stocks/fundamentals_top50.json` — Current valuation multiples (trailingPE, forwardPE, evToEbitda, priceToBook, priceToSales)
- `stocks/all_tickers_5y_daily.csv` — Price history to compute historical P/E trajectories
- `economic/FED_FUNDS_RATE.csv` — Rate hiking cycles that trigger compression
- `economic/YIELD_SPREAD_10Y2Y.csv` — Yield curve inversions preceding slowdowns
- `economic/CONSUMER_SENTIMENT.csv` — Sentiment shifts
- `economic/VIX.csv` — Volatility regime changes
- `kalshi/markets_settled_*.json` — Resolved prediction markets (outcomes known)

## Multiple Compression Triggers to Model
1. Rising interest rates (FED_FUNDS_RATE, 10Y/2Y TREASURY)
2. Yield curve inversion (YIELD_SPREAD_10Y2Y going negative)
3. Slowing earnings growth vs price appreciation
4. Macro deterioration (GDP decel, rising unemployment, falling sentiment)
5. Sector rotation (defensive vs growth ETF relative performance)
6. Volatility regime shift (VIX breakouts)

## Sources
- Kalshi public API (no auth)
- Yahoo Finance via yfinance
- FRED (Federal Reserve Bank of St. Louis)
- CoinGecko API
"""
    with open(os.path.join(DATA_DIR, "README.md"), "w") as f:
        f.write(readme)


# ── Main ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Market & Economic Data Collector")
    print("  Target: Multiple Compression Signal Detection")
    print("=" * 60)

    collect_kalshi()
    collect_stocks()
    collect_fred()
    collect_crypto()
    write_readme()

    # Summary
    total = 0
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for name, path in [("Kalshi", KALSHI_DIR), ("Stocks", STOCKS_DIR),
                        ("Economic", ECON_DIR), ("Crypto", CRYPTO_DIR)]:
        size = sum(os.path.getsize(os.path.join(path, f))
                   for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        total += size
        files = len(os.listdir(path))
        print(f"  {name:12s}  {files:3d} files  {size/1024/1024:.1f} MB")
    print(f"  {'TOTAL':12s}  {total/1024/1024:.1f} MB")
    print(f"\n  Data saved to: {DATA_DIR}")
    print("=" * 60)
