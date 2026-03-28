"""Step 1: Calculate 12-month abnormal returns for all companies in the database.

AR_12M = stock_return_12M - SP500_return_12M

This is the target variable Y for the regression.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# COMPRESSION DATABASE WITH T-ZERO DATES
# T-Zero = the approximate date the compression started
# We measure 12-month return from T-Zero
# ============================================================

companies = [
    # ticker, t_zero, pre_pe, sga, gm, de, fcf, roic, industry, recovered
    # DOTCOM (T-Zero = March 2000)
    ("CSCO", "2000-03-01", 127, 0.25, 0.65, 0.10, 0.005, 0.12, "Networking", False),
    ("MSFT", "2000-03-01", 59, 0.22, 0.86, 0.0, 0.015, 0.30, "Enterprise Software", True),
    ("INTC", "2000-03-01", 50, 0.15, 0.62, 0.05, 0.02, 0.22, "Semiconductors", True),
    ("ORCL", "2000-03-01", 103, 0.28, 0.78, 0.20, 0.008, 0.15, "Enterprise Software", True),
    ("QCOM", "2000-03-01", 200, 0.12, 0.60, 0.05, 0.003, 0.08, "Semiconductors", True),
    # GFC (T-Zero = Oct 2007)
    ("C", "2007-10-01", 11, 0.40, 0.55, 8.0, 0.02, 0.04, "Banking", False),
    ("BAC", "2007-10-01", 11.5, 0.35, 0.50, 7.5, 0.03, 0.05, "Banking", False),
    ("JPM", "2007-10-01", 10, 0.35, 0.55, 6.0, 0.03, 0.06, "Banking", True),
    ("WFC", "2007-10-01", 13, 0.38, 0.58, 5.0, 0.04, 0.08, "Banking", True),
    ("GS", "2007-10-01", 8, 0.50, 0.60, 12.0, 0.02, 0.08, "Investment Banking", True),
    ("GE", "2007-10-01", 15, 0.20, 0.35, 4.0, 0.04, 0.06, "Conglomerate", False),
    # GROWTH 2022 (T-Zero = Nov 2021)
    ("ZM", "2021-11-01", 130, 0.35, 0.75, 0.05, 0.015, 0.12, "Video Comms", False),
    ("DOCU", "2021-11-01", 195, 0.50, 0.78, 1.5, 0.005, 0.05, "E-Signature", False),
    ("SHOP", "2021-11-01", 350, 0.30, 0.55, 0.5, 0.002, 0.03, "E-Commerce Platform", True),
    ("CRM", "2021-11-01", 130, 0.45, 0.73, 0.20, 0.04, 0.06, "Enterprise CRM", True),
    ("SNAP", "2021-09-01", 0, 0.55, 0.55, 0.50, -0.05, -0.08, "Social Media", False),
    ("ABNB", "2021-11-01", 0, 0.30, 0.80, 0.50, 0.02, 0.05, "Travel Platform", True),
    ("DASH", "2021-11-01", 0, 0.45, 0.45, 1.0, -0.05, -0.08, "Food Delivery", True),
    # AI 2023 (T-Zero = Nov 2022)
    ("CHGG", "2022-11-01", 28, 0.48, 0.74, 0.91, 0.085, 0.04, "EdTech", False),
    ("UPWK", "2022-11-01", 0, 0.61, 0.75, 0.85, 0.012, -0.05, "Freelance", False),
    # Additional tickers with good yfinance data
    ("META", "2022-02-01", 24, 0.25, 0.80, 0.10, 0.06, 0.18, "Social Media", True),
    ("NVDA", "2021-11-01", 90, 0.10, 0.65, 0.40, 0.02, 0.20, "Semiconductors", True),
    ("TSLA", "2021-11-01", 350, 0.10, 0.25, 0.30, -0.01, 0.05, "Electric Vehicles", True),
    ("COIN", "2021-11-01", 0, 0.40, 0.80, 2.0, -0.05, -0.10, "Crypto Exchange", True),
]

# ============================================================
# PULL S&P 500 DATA FOR BENCHMARK
# ============================================================
print("Pulling S&P 500 benchmark data...")
spy = yf.Ticker("SPY")
spy_hist = spy.history(start="1999-01-01", end="2026-03-27", auto_adjust=True)
spy_hist.index = spy_hist.index.tz_localize(None)
print(f"SPY data: {len(spy_hist)} days")

def get_return(ticker_hist, start_date, months=12):
    """Calculate return over N months from start_date."""
    start = pd.Timestamp(start_date)
    end = start + pd.DateOffset(months=months)

    # Find nearest trading days
    after_start = ticker_hist[ticker_hist.index >= start]
    before_end = ticker_hist[ticker_hist.index <= end]

    if after_start.empty or before_end.empty:
        return None

    start_price = float(after_start.iloc[0]["Close"])
    end_price = float(before_end.iloc[-1]["Close"])

    return (end_price - start_price) / start_price

# ============================================================
# CALCULATE ABNORMAL RETURNS
# ============================================================
print("\nCalculating abnormal returns...")
print(f"{'Ticker':8s} {'T-Zero':12s} {'Stock_12M':>10s} {'SPY_12M':>10s} {'AR_12M':>10s} {'Industry':20s} {'Recov':>6s}")
print("-" * 85)

results = []
for ticker, t_zero, pe, sga, gm, de, fcf, roic, industry, recovered in companies:
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(start="1999-01-01", end="2026-03-27", auto_adjust=True)
        hist.index = hist.index.tz_localize(None)

        stock_ret = get_return(hist, t_zero, 12)
        spy_ret = get_return(spy_hist, t_zero, 12)

        if stock_ret is not None and spy_ret is not None:
            ar_12m = stock_ret - spy_ret

            recov_str = "YES" if recovered else "no"
            print(f"{ticker:8s} {t_zero:12s} {stock_ret:+9.1%} {spy_ret:+9.1%} {ar_12m:+9.1%} {industry:20s} {recov_str:>6s}")

            results.append({
                "ticker": ticker,
                "t_zero": t_zero,
                "pe": pe,
                "sga": sga,
                "gm": gm,
                "de": de,
                "fcf": fcf,
                "roic": roic,
                "industry": industry,
                "recovered": recovered,
                "stock_return_12m": stock_ret,
                "spy_return_12m": spy_ret,
                "abnormal_return_12m": ar_12m,
            })
        else:
            print(f"{ticker:8s} {t_zero:12s} -- NO DATA (ticker may not have history that far back)")
    except Exception as e:
        print(f"{ticker:8s} {t_zero:12s} -- ERROR: {e}")

# ============================================================
# SAVE THE TRAINING SET
# ============================================================
df = pd.DataFrame(results)
output_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'rangers', 'noah', 'tsunami', 'data', 'training_set.csv')
df.to_csv(output_path, index=False)
print(f"\nSaved {len(results)} companies to {output_path}")

# ============================================================
# SUMMARY STATISTICS
# ============================================================
print(f"\n{'='*60}")
print("TRAINING SET SUMMARY")
print(f"{'='*60}")
print(f"Total companies with data: {len(results)}")
print(f"Recovered: {sum(1 for r in results if r['recovered'])}")
print(f"Stayed dead: {sum(1 for r in results if not r['recovered'])}")
print(f"\nAbnormal Return Distribution:")
ars = [r["abnormal_return_12m"] for r in results]
print(f"  Mean:   {np.mean(ars):+.1%}")
print(f"  Median: {np.median(ars):+.1%}")
print(f"  Min:    {min(ars):+.1%}")
print(f"  Max:    {max(ars):+.1%}")
print(f"  Std:    {np.std(ars):.1%}")

dead = [r["abnormal_return_12m"] for r in results if not r["recovered"]]
alive = [r["abnormal_return_12m"] for r in results if r["recovered"]]
print(f"\nDead companies AR:    mean={np.mean(dead):+.1%}")
print(f"Recovered companies AR: mean={np.mean(alive):+.1%}")
print(f"Separation:             {np.mean(dead) - np.mean(alive):+.1%}")
