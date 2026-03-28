"""
Feature engineering for multiple compression detection.

Builds macro, market, and valuation features from raw data.
All features use only data available at prediction time (no lookahead).
"""
import numpy as np
import pandas as pd


def _safe_pct_change(series, periods):
    """Percentage change with NaN handling."""
    if series is None or len(series) < periods + 1:
        return None
    return series.pct_change(periods).iloc[-1]


def _safe_level(series):
    """Latest value from a series."""
    if series is None or len(series) == 0:
        return None
    val = series.iloc[-1]
    if isinstance(val, pd.Series):
        val = val.iloc[0]
    return float(val) if pd.notna(val) else None


def _rolling_percentile(series, value, window=504):
    """Where does value sit in the last N observations? (0-100)"""
    if series is None or len(series) < 20:
        return None
    recent = series.tail(window).dropna()
    if len(recent) == 0:
        return None
    return float((recent < value).sum() / len(recent) * 100)


def build_macro_features(fred):
    """Build macro-level features from FRED data."""
    features = {}

    # Fed Funds Rate
    ff = fred.get("FED_FUNDS_RATE")
    if ff is not None and len(ff) > 0:
        features["fed_funds_level"] = _safe_level(ff["VALUE"])
        features["fed_funds_3mo_chg"] = _safe_pct_change(ff["VALUE"], 3)
        features["fed_funds_6mo_chg"] = _safe_pct_change(ff["VALUE"], 6)

    # 10Y Treasury
    t10 = fred.get("10Y_TREASURY")
    if t10 is not None and len(t10) > 0:
        features["treasury_10y"] = _safe_level(t10["VALUE"])

    # 2Y Treasury
    t2 = fred.get("2Y_TREASURY")
    if t2 is not None and len(t2) > 0:
        features["treasury_2y"] = _safe_level(t2["VALUE"])

    # Yield curve spread
    yc = fred.get("YIELD_SPREAD_10Y2Y")
    if yc is not None and len(yc) > 0:
        features["yield_curve_spread"] = _safe_level(yc["VALUE"])
        features["yield_curve_inverted"] = 1 if (features.get("yield_curve_spread") or 1) < 0 else 0

    # CPI
    cpi = fred.get("CPI")
    if cpi is not None and len(cpi) > 12:
        features["cpi_yoy"] = _safe_pct_change(cpi["VALUE"], 12)

    # Core PCE
    pce = fred.get("CORE_PCE")
    if pce is not None and len(pce) > 12:
        features["core_pce_yoy"] = _safe_pct_change(pce["VALUE"], 12)

    # Unemployment
    unemp = fred.get("UNEMPLOYMENT")
    if unemp is not None and len(unemp) > 0:
        features["unemployment"] = _safe_level(unemp["VALUE"])
        if len(unemp) > 3:
            features["unemployment_3mo_chg"] = float(
                unemp["VALUE"].iloc[-1] - unemp["VALUE"].iloc[-4]
            ) if len(unemp) > 3 else None

    # Consumer Sentiment
    sent = fred.get("CONSUMER_SENTIMENT")
    if sent is not None and len(sent) > 0:
        features["consumer_sentiment"] = _safe_level(sent["VALUE"])
        if len(sent) > 3:
            features["sentiment_3mo_chg"] = float(
                sent["VALUE"].iloc[-1] - sent["VALUE"].iloc[-4]
            )

    # VIX
    vix = fred.get("VIX")
    if vix is not None and len(vix) > 0:
        features["vix_level"] = _safe_level(vix["VALUE"])
        features["vix_percentile"] = _rolling_percentile(
            vix["VALUE"], features.get("vix_level", 20)
        )

    # M2 Money Supply YoY
    m2 = fred.get("M2_MONEY_SUPPLY")
    if m2 is not None and len(m2) > 12:
        features["m2_yoy"] = _safe_pct_change(m2["VALUE"], 12)

    # Dollar Index
    dxy = fred.get("DOLLAR_INDEX")
    if dxy is not None and len(dxy) > 63:
        features["dollar_3mo_chg"] = _safe_pct_change(dxy["VALUE"], 63)

    return features


def build_stock_features(ticker, ticker_df, fundamentals_dict, spy_df=None):
    """Build per-stock features."""
    features = {"ticker": ticker}

    if ticker_df is None or len(ticker_df) < 252:
        return features

    close = ticker_df["Close"]

    # Momentum
    for label, periods in [("1mo", 21), ("3mo", 63), ("6mo", 126), ("12mo", 252)]:
        if len(close) > periods:
            features[f"momentum_{label}"] = float(
                close.iloc[-1] / close.iloc[-periods - 1] - 1
            )

    # Volatility (20d realized)
    if len(close) > 21:
        returns = close.pct_change().dropna()
        features["volatility_20d"] = float(returns.tail(20).std() * np.sqrt(252))

    # Distance from 52w high
    if len(close) > 252:
        high_52w = close.tail(252).max()
        features["dist_from_52w_high"] = float(close.iloc[-1] / high_52w - 1)

    # Relative strength vs SPY
    if spy_df is not None and len(spy_df) > 63:
        spy_close = spy_df["Close"]
        if len(spy_close) > 63 and len(close) > 63:
            stock_ret = float(close.iloc[-1] / close.iloc[-64] - 1)
            spy_ret = float(spy_close.iloc[-1] / spy_close.iloc[-64] - 1)
            features["rel_strength_vs_spy_3mo"] = stock_ret - spy_ret

    # Valuation features from fundamentals
    fund = fundamentals_dict.get(ticker, {})
    for key in ["trailingPE", "forwardPE", "evToEbitda", "priceToBook",
                "priceToSales", "beta", "profitMargins", "earningsGrowth",
                "revenueGrowth", "debtToEquity", "returnOnEquity"]:
        val = fund.get(key)
        if val is not None:
            features[key] = float(val)

    # Earnings yield vs 10Y (equity risk premium proxy)
    pe = fund.get("trailingPE")
    if pe and pe > 0:
        features["earnings_yield"] = 1.0 / pe

    return features


def build_all_features(data):
    """Build complete feature set from loaded data."""
    print("  Building macro features...")
    macro = build_macro_features(data["fred"])

    print("  Building stock features...")
    fund_dict = {f["ticker"]: f for f in data["fundamentals"]}
    spy_df = data["tickers"].get("SPY")

    stock_features = []
    for ticker, df in data["tickers"].items():
        if ticker.startswith("^") or ticker in ["SPY", "TLT", "HYG", "XLK", "XLF", "XLE", "XLV"]:
            continue  # skip indices and ETFs
        sf = build_stock_features(ticker, df, fund_dict, spy_df)
        # Merge macro features into each stock row
        sf.update(macro)
        stock_features.append(sf)

    features_df = pd.DataFrame(stock_features)
    print(f"  Built features for {len(features_df)} stocks, {len(features_df.columns)} columns")
    return features_df, macro
