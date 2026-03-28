"""Full time-series simulation: replay ZM with known quarterly data + daily price/volume."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import yfinance as yf
import numpy as np
import pandas as pd

# ============================================================
# ZM KNOWN QUARTERLY FUNDAMENTALS (from SEC filings)
# We hardcode what we KNOW from the 10-Qs
# ============================================================
zm_quarters = [
    # date, EPS_TTM, SGA%, GM%, revenue_growth_yoy
    ("2020-07-01", 1.92, 0.25, 0.72, 3.55),   # COVID peak growth
    ("2020-10-01", 2.60, 0.22, 0.73, 3.67),   # Still rocketing
    ("2021-01-01", 3.34, 0.24, 0.74, 3.69),   # Peak euphoria
    ("2021-04-01", 3.70, 0.28, 0.73, 1.91),   # Growth DECELERATING
    ("2021-07-01", 3.90, 0.30, 0.72, 0.54),   # Growth collapsing
    ("2021-10-01", 3.85, 0.32, 0.70, 0.35),   # Growth stalling
    ("2022-01-01", 3.50, 0.33, 0.68, 0.21),   # Earnings declining
    ("2022-04-01", 3.00, 0.35, 0.66, 0.12),   # Margin compression
    ("2022-07-01", 2.80, 0.36, 0.65, 0.05),   # Near flat growth
    ("2022-10-01", 2.60, 0.35, 0.65, 0.05),   # Stagnant
    ("2023-01-01", 2.50, 0.34, 0.66, 0.04),   # Stabilizing low
    ("2023-04-01", 2.40, 0.33, 0.67, 0.03),
    ("2023-07-01", 2.50, 0.32, 0.68, 0.03),
    ("2023-10-01", 2.80, 0.30, 0.69, 0.03),   # Slight recovery
    ("2024-01-01", 3.00, 0.28, 0.70, 0.03),
    ("2024-04-01", 3.10, 0.27, 0.71, 0.02),
    ("2024-07-01", 3.20, 0.28, 0.72, 0.02),
]

# Load daily price + volume from yfinance
print("Loading ZM daily price data...")
zm = yf.Ticker("ZM")
hist = zm.history(start="2020-06-01", end="2026-03-27", auto_adjust=True)
hist.index = hist.index.tz_localize(None)
print(f"Loaded {len(hist)} trading days\n")

# ============================================================
# SIMULATION ENGINE
# ============================================================

def get_quarter_data(date):
    """Get the most recent quarterly snapshot before this date."""
    result = None
    for q_date_str, eps, sga, gm, rev_growth in zm_quarters:
        q_date = pd.Timestamp(q_date_str)
        if q_date <= date:
            result = {"eps_ttm": eps, "sga": sga, "gm": gm, "rev_growth": rev_growth}
    return result or {"eps_ttm": 0, "sga": 0.30, "gm": 0.70, "rev_growth": 0}

def compute_signals(date, price, volume, q_data, hist_slice):
    """Compute all signals for a given date."""
    eps = q_data["eps_ttm"]
    sga = q_data["sga"]
    gm = q_data["gm"]
    pe = price / eps if eps > 0 else 0

    # 1. Growth compression path
    pe_prem = min(1, max(0, (pe - 12) / 38)) if pe > 0 else 0
    mf = min(1, (sga * gm) / 0.35)
    growth_signal = pe_prem * 0.55 + mf * 0.45

    # 2. ZM moat = WEAK (video call is a feature)
    moat = 0.35

    # 3. Net score
    net = growth_signal - moat

    # 4. Volume Z-score (20-day)
    if len(hist_slice) >= 20:
        vol_20 = hist_slice["Volume"].tail(20)
        vol_mean = vol_20.mean()
        vol_std = vol_20.std()
        vol_z = (volume - vol_mean) / vol_std if vol_std > 0 else 0
    else:
        vol_z = 0

    # 5. Price momentum (20-day)
    if len(hist_slice) >= 20:
        price_20d_ago = hist_slice["Close"].iloc[-20]
        momentum = (price - price_20d_ago) / price_20d_ago
    else:
        momentum = 0

    # 6. Revenue deceleration signal
    rev_decel = max(0, 1 - q_data["rev_growth"])  # higher when growth slows

    return {
        "pe": pe, "pe_prem": pe_prem, "mf": mf,
        "growth": growth_signal, "moat": moat, "net": net,
        "vol_z": vol_z, "momentum": momentum, "rev_decel": rev_decel,
    }

# ============================================================
# RUN DAILY SIMULATION
# ============================================================

# Sample weekly (every Friday)
weekly = hist.resample("W-FRI").last().dropna()

results = []
for date, row in weekly.iterrows():
    price = row["Close"]
    volume = row["Volume"]
    q_data = get_quarter_data(date)
    hist_slice = hist[:date]
    sigs = compute_signals(date, price, volume, q_data, hist_slice)
    results.append({"date": date, "price": price, "volume": volume, **sigs, **q_data})

# ============================================================
# TRADE SIMULATION WITH INTRADAY-ISH SIGNALS
# ============================================================

print("=" * 90)
print("WEEKLY SIMULATION: ZM compression trade")
print("=" * 90)
print(f"{'Date':12s} {'Price':>8s} {'P/E':>6s} {'Net':>6s} {'VolZ':>6s} {'Mom':>7s} {'RevD':>5s} {'Signal':>20s}")
print("-" * 80)

in_trade = False
entry_price = 0
entry_date = None
trades = []

for r in results:
    signal = ""

    # ENHANCED BUY: net_score > 0.40 AND (volume spike OR negative momentum OR revenue deceleration)
    buy_conditions = r["net"] > 0.40
    buy_catalyst = r["vol_z"] > 1.5 or r["momentum"] < -0.10 or r["rev_decel"] > 0.50

    if not in_trade:
        if buy_conditions and buy_catalyst:
            signal = ">>> BUY (catalyst)"
            in_trade = True
            entry_price = r["price"]
            entry_date = r["date"]
        elif buy_conditions:
            signal = "... READY (no catalyst)"
    else:
        drop = (entry_price - r["price"]) / entry_price

        # SELL conditions
        if drop > 0.50:
            roi = drop / 0.04
            signal = f"<<< SELL +{roi:.0f}x ({drop:.0%} drop)"
            trades.append({"entry": entry_date, "exit": r["date"],
                          "entry_p": entry_price, "exit_p": r["price"],
                          "drop": drop, "roi": roi, "days": (r["date"] - entry_date).days})
            in_trade = False
        elif r["net"] < 0.10:
            roi = drop / 0.04 if drop > 0 else -1
            signal = f"<<< EXIT (score={r['net']:.2f})"
            trades.append({"entry": entry_date, "exit": r["date"],
                          "entry_p": entry_price, "exit_p": r["price"],
                          "drop": drop, "roi": roi, "days": (r["date"] - entry_date).days})
            in_trade = False
        elif r["price"] > entry_price * 1.20:
            signal = f"<<< STOP (up {r['price']/entry_price-1:.0%})"
            trades.append({"entry": entry_date, "exit": r["date"],
                          "entry_p": entry_price, "exit_p": r["price"],
                          "drop": 0, "roi": -1, "days": (r["date"] - entry_date).days})
            in_trade = False

    # Print signal rows + monthly checkpoints
    if signal or r["date"].day <= 7:
        pe_str = f"{r['pe']:.0f}x" if r["pe"] > 0 else "N/E"
        marker = " ***" if "BUY" in signal or "SELL" in signal else ""
        print(f"{r['date'].strftime('%Y-%m-%d'):12s} ${r['price']:7.2f} {pe_str:>6s} {r['net']:+.3f} {r['vol_z']:+5.1f} {r['momentum']:+6.1%} {r['rev_decel']:.2f} {signal}{marker}")

# ============================================================
# RESULTS
# ============================================================
print()
print("=" * 70)
print("TRADE LOG")
print("=" * 70)

for i, t in enumerate(trades, 1):
    print(f"\nTrade #{i}:")
    print(f"  Entry: {t['entry'].strftime('%Y-%m-%d')} @ ${t['entry_p']:.2f}")
    print(f"  Exit:  {t['exit'].strftime('%Y-%m-%d')} @ ${t['exit_p']:.2f}")
    print(f"  Drop:  {t['drop']:.1%} over {t['days']} days")
    print(f"  Put ROI: {t['roi']:+.1f}x on premium")

print()
print("=" * 70)
print("TIMING ANALYSIS")
print("=" * 70)

# Find actual peak and bottom
peak = max(results, key=lambda x: x["price"])
bottom = min(results, key=lambda x: x["price"])
print(f"ZM Peak:   {peak['date'].strftime('%Y-%m-%d')} @ ${peak['price']:.2f} (P/E={peak['pe']:.0f}x)")
print(f"ZM Bottom: {bottom['date'].strftime('%Y-%m-%d')} @ ${bottom['price']:.2f} (P/E={bottom['pe']:.0f}x)")
print(f"Total compression: {(peak['price']-bottom['price'])/peak['price']:.0%}")

if trades:
    first = trades[0]
    days_after_peak = (first["entry"] - peak["date"]).days
    print(f"\nFirst trade entry: {first['entry'].strftime('%Y-%m-%d')} @ ${first['entry_p']:.2f}")
    if days_after_peak > 0:
        print(f"  {days_after_peak} days AFTER peak (caught the turn)")
    else:
        print(f"  {abs(days_after_peak)} days BEFORE peak (early)")
    print(f"  P/E at entry: {results[[r['date'] for r in results].index(first['entry'])]['pe'] if False else 'see above'}x")

    # How much of the total drop did we capture?
    total_drop = peak["price"] - bottom["price"]
    captured = first["entry_p"] - trades[-1]["exit_p"]
    capture_pct = captured / total_drop if total_drop > 0 else 0
    print(f"\nTotal drop: ${total_drop:.2f}")
    print(f"Captured:   ${captured:.2f} ({capture_pct:.0%} of total move)")
