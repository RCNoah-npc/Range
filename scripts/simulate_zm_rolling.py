"""ZM simulation with realistic rolling 6-month puts."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import yfinance as yf
import numpy as np
import pandas as pd

# Known quarterly fundamentals
zm_quarters = [
    ("2020-07-01", 1.92, 0.25, 0.72, 3.55),
    ("2020-10-01", 2.60, 0.22, 0.73, 3.67),
    ("2021-01-01", 3.34, 0.24, 0.74, 3.69),
    ("2021-04-01", 3.70, 0.28, 0.73, 1.91),
    ("2021-07-01", 3.90, 0.30, 0.72, 0.54),
    ("2021-10-01", 3.85, 0.32, 0.70, 0.35),
    ("2022-01-01", 3.50, 0.33, 0.68, 0.21),
    ("2022-04-01", 3.00, 0.35, 0.66, 0.12),
    ("2022-07-01", 2.80, 0.36, 0.65, 0.05),
    ("2022-10-01", 2.60, 0.35, 0.65, 0.05),
    ("2023-01-01", 2.50, 0.34, 0.66, 0.04),
    ("2023-04-01", 2.40, 0.33, 0.67, 0.03),
    ("2023-07-01", 2.50, 0.32, 0.68, 0.03),
    ("2023-10-01", 2.80, 0.30, 0.69, 0.03),
    ("2024-01-01", 3.00, 0.28, 0.70, 0.03),
]

print("Loading ZM daily data...")
zm = yf.Ticker("ZM")
hist = zm.history(start="2020-06-01", end="2026-03-27", auto_adjust=True)
hist.index = hist.index.tz_localize(None)
print(f"Loaded {len(hist)} days\n")

weekly = hist.resample("W-FRI").last().dropna()

def get_q(date):
    result = {"eps_ttm": 0, "sga": 0.30, "gm": 0.70, "rev_growth": 0}
    for q_date_str, eps, sga, gm, rg in zm_quarters:
        if pd.Timestamp(q_date_str) <= date:
            result = {"eps_ttm": eps, "sga": sga, "gm": gm, "rev_growth": rg}
    return result

def net_score(date, price):
    q = get_q(date)
    eps = q["eps_ttm"]
    pe = price / eps if eps > 0 else 0
    pe_prem = min(1, max(0, (pe - 12) / 38)) if pe > 0 else 0
    mf = min(1, (q["sga"] * q["gm"]) / 0.35)
    growth = pe_prem * 0.55 + mf * 0.45
    moat = 0.35
    return growth - moat, pe

# ============================================================
# ROLLING PUT SIMULATION
# ============================================================
# Rules:
# - Each put = 6 months (26 weeks), ATM strike, 4% premium
# - At expiry: if intrinsic > 0, cash out. If worthless, premium lost.
# - If thesis still active (net > 0.20), immediately roll into new put.
# - Capital: $10,000 per put round (10% of $100k portfolio)

CAPITAL_PER_ROUND = 100000  # 10% of $1M portfolio per position
PREMIUM_PCT = 0.04  # 4% of strike = ATM 6-month put cost
PUT_LIFE_WEEKS = 26

print("=" * 85)
print("ROLLING PUT SIMULATION: ZM ($10k per round, 6-month puts, 4% premium)")
print("=" * 85)
print(f"{'Date':12s} {'Price':>8s} {'P/E':>6s} {'Net':>6s} {'Event':>28s} {'P&L':>10s} {'Cumul':>10s}")
print("-" * 85)

active_put = None  # {"entry_date", "strike", "premium_cost", "contracts", "expiry_week"}
in_strategy = False
total_pnl = 0
rounds = []
week_idx = 0

for date, row in weekly.iterrows():
    price = float(row["Close"])
    ns, pe = net_score(date, price)
    event = ""
    round_pnl = 0

    # Check for momentum catalyst
    hist_slice = hist[:date]
    if len(hist_slice) >= 20:
        p20 = float(hist_slice["Close"].iloc[-20])
        mom = (price - p20) / p20
    else:
        mom = 0

    buy_ready = ns > 0.40
    catalyst = mom < -0.10

    # === CHECK EXPIRY ===
    if active_put and week_idx >= active_put["expiry_week"]:
        strike = active_put["strike"]
        intrinsic = max(0, strike - price)
        value = intrinsic * active_put["contracts"] * 100
        cost = active_put["premium_cost"]
        round_pnl = value - cost
        total_pnl += round_pnl

        if intrinsic > 0:
            roi = round_pnl / cost
            event = f"EXPIRY +${value:.0f} (ROI {roi:+.0%})"
        else:
            event = f"EXPIRY worthless (-${cost:.0f})"

        rounds.append({
            "entry": active_put["entry_date"],
            "expiry": date,
            "strike": strike,
            "entry_price": active_put["entry_price"],
            "exit_price": price,
            "cost": cost,
            "value": value,
            "pnl": round_pnl,
        })
        active_put = None

        # Roll if thesis still active
        if ns > 0.20:
            premium_per_share = price * PREMIUM_PCT
            contracts = max(1, int(CAPITAL_PER_ROUND / (premium_per_share * 100)))
            cost = premium_per_share * contracts * 100
            active_put = {
                "entry_date": date,
                "entry_price": price,
                "strike": round(price, 2),
                "premium_cost": cost,
                "contracts": contracts,
                "expiry_week": week_idx + PUT_LIFE_WEEKS,
            }
            event += f" -> ROLL {contracts}x ${price:.0f}P"
        else:
            event += " -> EXIT (score low)"
            in_strategy = False

    # === CHECK ENTRY ===
    if not active_put and not in_strategy and buy_ready and catalyst:
        premium_per_share = price * PREMIUM_PCT
        contracts = max(1, int(CAPITAL_PER_ROUND / (premium_per_share * 100)))
        cost = premium_per_share * contracts * 100
        active_put = {
            "entry_date": date,
            "entry_price": price,
            "strike": round(price, 2),
            "premium_cost": cost,
            "contracts": contracts,
            "expiry_week": week_idx + PUT_LIFE_WEEKS,
        }
        in_strategy = True
        event = f"BUY {contracts}x ${price:.0f}P @${premium_per_share:.2f}"

    # === CHECK EARLY EXIT (take profit at 200% ROI mid-contract) ===
    if active_put and not event:
        strike = active_put["strike"]
        intrinsic = max(0, strike - price)
        # Rough mid-contract value = intrinsic + some time value
        mid_value = intrinsic * active_put["contracts"] * 100
        mid_roi = (mid_value - active_put["premium_cost"]) / active_put["premium_cost"]
        if mid_roi > 2.0:  # 200% ROI = take profit early
            round_pnl = mid_value - active_put["premium_cost"]
            total_pnl += round_pnl
            event = f"TAKE PROFIT {mid_roi:+.0%} ROI (+${round_pnl:.0f})"
            rounds.append({
                "entry": active_put["entry_date"],
                "expiry": date,
                "strike": strike,
                "entry_price": active_put["entry_price"],
                "exit_price": price,
                "cost": active_put["premium_cost"],
                "value": mid_value,
                "pnl": round_pnl,
            })
            active_put = None
            # Don't immediately re-enter, wait for next catalyst

    # Print
    if event or date.month in [1, 4, 7, 10] and date.day <= 7:
        pe_str = f"{pe:.0f}x" if pe > 0 else "N/E"
        pnl_str = f"${round_pnl:+,.0f}" if round_pnl else ""
        cum_str = f"${total_pnl:+,.0f}"
        marker = " ***" if "BUY" in event or "PROFIT" in event or "ROLL" in event else ""
        print(f"{date.strftime('%Y-%m-%d'):12s} ${price:7.2f} {pe_str:>6s} {ns:+.3f} {event:>28s} {pnl_str:>10s} {cum_str:>10s}{marker}")

    week_idx += 1

# ============================================================
# RESULTS
# ============================================================
print()
print("=" * 70)
print("ROUND-BY-ROUND RESULTS")
print("=" * 70)

total_cost = 0
total_value = 0
for i, r in enumerate(rounds, 1):
    days = (r["expiry"] - r["entry"]).days
    roi = r["pnl"] / r["cost"] if r["cost"] else 0
    result = "WIN" if r["pnl"] > 0 else "LOSS"
    print(f"Round {i}: {r['entry'].strftime('%Y-%m-%d')} -> {r['expiry'].strftime('%Y-%m-%d')} ({days}d)")
    print(f"  Strike: ${r['strike']:.2f} | Entry: ${r['entry_price']:.2f} | Exit: ${r['exit_price']:.2f}")
    print(f"  Cost: ${r['cost']:,.0f} | Value: ${r['value']:,.0f} | P&L: ${r['pnl']:+,.0f} | ROI: {roi:+.0%} | {result}")
    print()
    total_cost += r["cost"]
    total_value += r["value"]

wins = sum(1 for r in rounds if r["pnl"] > 0)
losses = len(rounds) - wins

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total rounds:     {len(rounds)}")
print(f"Wins:             {wins}")
print(f"Losses:           {losses}")
print(f"Win rate:         {wins/len(rounds):.0%}" if rounds else "N/A")
print(f"Total premium:    ${total_cost:,.0f}")
print(f"Total value:      ${total_value:,.0f}")
print(f"Net P&L:          ${total_pnl:+,.0f}")
print(f"Return on premium:{total_pnl/total_cost:+.1%}" if total_cost else "N/A")
print(f"Capital at risk:  $10,000 per round")
