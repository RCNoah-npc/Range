"""
Phase 2: Label Historical Compression Events
Identifies when PE multiples compressed in historical data.
Uses price drawdowns not explained by earnings deterioration as proxy.
"""
import pandas as pd
import numpy as np


def compute_rolling_pe_proxy(prices: pd.DataFrame, fundamentals: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Approximate historical P/E trajectories.
    Since we only have current fundamentals, we derive implied earnings
    from current PE and scale by price history.
    """
    results = {}
    if fundamentals.empty:
        return results

    for _, row in fundamentals.iterrows():
        ticker = row["ticker"]
        current_pe = row.get("trailingPE")
        if pd.isna(current_pe) or current_pe is None or current_pe <= 0:
            continue

        # Try to get price history for this ticker
        try:
            if isinstance(prices.columns, pd.MultiIndex):
                if ticker in prices.columns.get_level_values(0):
                    px = prices[ticker]["Close"].dropna()
                else:
                    continue
            else:
                continue
        except (KeyError, TypeError):
            continue

        if len(px) < 60:
            continue

        # Current implied earnings = current price / current PE
        current_price = px.iloc[-1]
        implied_current_eps = current_price / current_pe

        # Assume earnings grew roughly with a smoothed price trend
        # Use 252-day (1yr) rolling mean as "earnings proxy"
        earnings_proxy = px.rolling(252, min_periods=126).mean() / current_price * implied_current_eps
        earnings_proxy = earnings_proxy.dropna()

        if len(earnings_proxy) < 60:
            continue

        # Compute rolling PE proxy
        pe_proxy = px.loc[earnings_proxy.index] / earnings_proxy
        pe_proxy = pe_proxy.replace([np.inf, -np.inf], np.nan).dropna()

        results[ticker] = pd.DataFrame({
            "price": px.loc[pe_proxy.index],
            "earnings_proxy": earnings_proxy.loc[pe_proxy.index],
            "pe_proxy": pe_proxy,
        })

    return results


def label_compression_events(data: dict) -> dict[str, pd.DataFrame]:
    """
    Label each trading day per stock:
    0 = normal
    1 = compression approaching (within 3 months before event)
    2 = compression underway

    Compression event: PE proxy drops > 20% within 126 trading days (6 months)
    OR price drops > 25% while earnings proxy is flat/up.
    """
    pe_data = compute_rolling_pe_proxy(data["stock_prices"], data["fundamentals"])

    labeled = {}
    for ticker, df in pe_data.items():
        df = df.copy()
        df["label"] = 0

        # Method 1: PE proxy drawdown > 20% in 6-month window
        pe_peak = df["pe_proxy"].rolling(126, min_periods=1).max()
        pe_drawdown = (df["pe_proxy"] - pe_peak) / pe_peak
        compression_mask = pe_drawdown < -0.20

        # Method 2: Price drops > 25% while earnings proxy flat/up
        price_peak = df["price"].rolling(126, min_periods=1).max()
        price_drawdown = (df["price"] - price_peak) / price_peak
        earnings_change = df["earnings_proxy"].pct_change(63)  # 3-month earnings change
        price_crash_no_earnings = (price_drawdown < -0.25) & (earnings_change > -0.05)

        # Mark compression underway
        df.loc[compression_mask | price_crash_no_earnings, "label"] = 2

        # Mark approaching (3 months = 63 trading days before first compression day)
        compression_starts = df[df["label"] == 2].index
        for start in compression_starts:
            lookback = df.index[df.index < start]
            if len(lookback) > 0:
                approach_start = lookback[max(0, len(lookback) - 63)]
                approach_mask = (df.index >= approach_start) & (df.index < start) & (df["label"] == 0)
                df.loc[approach_mask, "label"] = 1

        labeled[ticker] = df

    total_events = sum((df["label"] == 2).any() for df in labeled.values())
    print(f"  ✓ Labeled {len(labeled)} stocks, {total_events} had compression events")
    return labeled
