"""
Phase 3: Feature Engineering
Build leading indicators from macro, market, valuation, and cross-asset data.
All features use only data available at prediction time (no lookahead).
"""
import pandas as pd
import numpy as np


def build_macro_features(fred: dict[str, pd.Series]) -> pd.DataFrame:
    """Build macro features from FRED series, resampled to daily."""
    features = pd.DataFrame()

    def _safe_get(name):
        s = fred.get(name)
        if s is None or len(s) == 0:
            return None
        # Resample to daily, forward fill
        s = s.resample("D").ffill()
        return s

    # Fed funds rate
    ffr = _safe_get("FED_FUNDS_RATE")
    if ffr is not None:
        features["ffr_level"] = ffr
        features["ffr_3mo_chg"] = ffr - ffr.shift(90)
        features["ffr_6mo_chg"] = ffr - ffr.shift(180)
        features["ffr_accel"] = features["ffr_3mo_chg"] - features["ffr_3mo_chg"].shift(90)

    # Yield curve
    yc = _safe_get("YIELD_SPREAD_10Y2Y")
    if yc is not None:
        features["yield_curve"] = yc
        features["yield_curve_slope"] = yc - yc.shift(30)
        features["yield_curve_inverted"] = (yc < 0).astype(int)
        # Days since inversion
        inverted = yc < 0
        days_since = inverted.groupby((~inverted).cumsum()).cumcount()
        features["days_since_inversion"] = days_since.where(inverted, 0)

    # CPI / inflation
    cpi = _safe_get("CPI")
    if cpi is not None:
        features["cpi_yoy"] = cpi.pct_change(365) * 100
        features["cpi_accel"] = features["cpi_yoy"] - features["cpi_yoy"].shift(90)

    # Core PCE
    pce = _safe_get("CORE_PCE")
    if pce is not None:
        features["core_pce_yoy"] = pce.pct_change(365) * 100

    # Unemployment
    unemp = _safe_get("UNEMPLOYMENT")
    if unemp is not None:
        features["unemployment"] = unemp
        features["unemployment_3mo_ma"] = unemp.rolling(90).mean()
        features["unemployment_direction"] = (unemp - unemp.shift(90)).apply(
            lambda x: 1 if x > 0.2 else (-1 if x < -0.2 else 0)
        )

    # Initial claims
    claims = _safe_get("INITIAL_CLAIMS")
    if claims is not None:
        features["claims_4wk_ma"] = claims.rolling(28).mean()
        features["claims_yoy"] = claims.pct_change(365)

    # Consumer sentiment
    sent = _safe_get("CONSUMER_SENTIMENT")
    if sent is not None:
        features["sentiment"] = sent
        features["sentiment_3mo_chg"] = sent - sent.shift(90)

    # VIX
    vix = _safe_get("VIX")
    if vix is not None:
        features["vix"] = vix
        features["vix_20d_ma"] = vix.rolling(20).mean()
        features["vix_2yr_pct"] = vix.rolling(504).rank(pct=True)

    # M2 money supply
    m2 = _safe_get("M2_MONEY_SUPPLY")
    if m2 is not None:
        features["m2_yoy"] = m2.pct_change(365) * 100

    # Dollar index
    dxy = _safe_get("DOLLAR_INDEX")
    if dxy is not None:
        features["dollar_3mo_chg"] = dxy.pct_change(90) * 100

    return features


def build_market_features(prices: pd.DataFrame, ticker: str, spy_prices: pd.Series = None) -> pd.DataFrame:
    """Build per-stock market features."""
    features = pd.DataFrame(index=prices.index)

    px = prices["price"] if "price" in prices.columns else prices.iloc[:, 0]

    # Momentum
    features["mom_1mo"] = px.pct_change(21)
    features["mom_3mo"] = px.pct_change(63)
    features["mom_6mo"] = px.pct_change(126)
    features["mom_12mo"] = px.pct_change(252)

    # Relative strength vs SPY
    if spy_prices is not None and len(spy_prices) > 0:
        # Align indices
        aligned_spy = spy_prices.reindex(px.index, method="ffill")
        if len(aligned_spy.dropna()) > 63:
            rel = px / aligned_spy
            features["rel_str_1mo"] = rel.pct_change(21)
            features["rel_str_3mo"] = rel.pct_change(63)

    # Volatility
    returns = px.pct_change()
    features["vol_20d"] = returns.rolling(20).std() * np.sqrt(252)
    vol_20d = features["vol_20d"]
    features["vol_of_vol"] = vol_20d.rolling(20).std()

    # Volume features (if available)
    if "Volume" in prices.columns:
        vol = prices["Volume"]
        features["vol_ratio_20_60"] = vol.rolling(20).mean() / vol.rolling(60).mean()

    # Distance from 52wk high
    high_52w = px.rolling(252, min_periods=126).max()
    features["dist_from_52w_high"] = (px - high_52w) / high_52w

    # Rolling beta (60d) vs SPY
    if spy_prices is not None and len(spy_prices) > 60:
        aligned_spy = spy_prices.reindex(px.index, method="ffill")
        spy_ret = aligned_spy.pct_change()
        stock_ret = px.pct_change()
        cov = stock_ret.rolling(60).cov(spy_ret)
        var = spy_ret.rolling(60).var()
        features["beta_60d"] = cov / var

    return features


def build_valuation_features(labeled_df: pd.DataFrame) -> pd.DataFrame:
    """Build valuation features from PE proxy data."""
    features = pd.DataFrame(index=labeled_df.index)

    pe = labeled_df["pe_proxy"]

    # PE vs 5yr average (percentile within rolling window)
    features["pe_5yr_pct"] = pe.rolling(1260, min_periods=252).rank(pct=True)

    # PE expansion over last 12 months
    features["pe_12mo_expansion"] = pe.pct_change(252)

    # PE vs rolling median
    pe_median = pe.rolling(1260, min_periods=252).median()
    features["pe_vs_median"] = (pe - pe_median) / pe_median

    # Earnings growth vs multiple growth divergence
    eps = labeled_df["earnings_proxy"]
    eps_growth_12mo = eps.pct_change(252)
    pe_growth_12mo = pe.pct_change(252)
    features["earnings_vs_multiple_divergence"] = pe_growth_12mo - eps_growth_12mo

    return features


def build_cross_asset_features(fred: dict, crypto: dict) -> pd.DataFrame:
    """Build cross-asset features."""
    features = pd.DataFrame()

    # Equity risk premium (earnings yield - 10Y treasury)
    # Using SP500 earnings yield proxy from VIX level as rough proxy
    t10 = fred.get("10Y_TREASURY")
    sp500 = fred.get("SP500")
    if t10 is not None and sp500 is not None:
        t10_d = t10.resample("D").ffill()
        sp500_d = sp500.resample("D").ffill()
        # Rough earnings yield = 1/PE, approximate PE from level
        # Use actual 10Y as the comparison
        features["treasury_10y"] = t10_d

    # BTC correlation with equities (rolling 30d)
    btc = crypto.get("bitcoin")
    if btc is not None and sp500 is not None:
        sp500_d = sp500.resample("D").ffill()
        btc_ret = btc["price"].pct_change()
        sp_ret = sp500_d.pct_change()
        aligned = pd.concat([btc_ret, sp_ret], axis=1).dropna()
        if len(aligned) > 30:
            aligned.columns = ["btc", "sp500"]
            features["btc_sp500_corr_30d"] = aligned["btc"].rolling(30).corr(aligned["sp500"])

    return features


def build_features(labeled: dict[str, pd.DataFrame], data: dict) -> dict[str, pd.DataFrame]:
    """Build full feature set for each stock."""
    macro = build_macro_features(data["fred"])
    cross_asset = build_cross_asset_features(data["fred"], data["crypto"])

    # Get SPY prices for relative strength
    spy_prices = None
    try:
        if isinstance(data["stock_prices"].columns, pd.MultiIndex):
            if "SPY" in data["stock_prices"].columns.get_level_values(0):
                spy_prices = data["stock_prices"]["SPY"]["Close"].dropna()
    except (KeyError, TypeError):
        pass

    feature_sets = {}
    for ticker, df in labeled.items():
        # Market features
        mkt = build_market_features(df, ticker, spy_prices)

        # Valuation features
        val = build_valuation_features(df)

        # Combine all features
        combined = pd.concat([mkt, val], axis=1)

        # Add macro features (align by date)
        if not macro.empty:
            macro_aligned = macro.reindex(combined.index, method="ffill")
            combined = pd.concat([combined, macro_aligned], axis=1)

        # Add cross-asset
        if not cross_asset.empty:
            ca_aligned = cross_asset.reindex(combined.index, method="ffill")
            combined = pd.concat([combined, ca_aligned], axis=1)

        # Add target
        combined["target"] = df["label"].apply(lambda x: 1 if x >= 1 else 0)
        combined["target_multiclass"] = df["label"]

        # Drop rows with too many NaNs
        combined = combined.dropna(thresh=int(len(combined.columns) * 0.5))

        if len(combined) > 100:
            feature_sets[ticker] = combined

    total_rows = sum(len(df) for df in feature_sets.values())
    print(f"  ✓ Features built for {len(feature_sets)} stocks, {total_rows} total observations")
    return feature_sets
