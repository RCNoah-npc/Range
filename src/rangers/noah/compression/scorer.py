"""
Phase 5: Scoring & Ranking
Score current market conditions and rank stocks by compression vulnerability.
"""
import pandas as pd
import numpy as np


def score_market(model, data: dict, feature_cols: list) -> dict:
    """Overall market compression risk score 0-100."""
    from .features import build_macro_features, build_cross_asset_features

    macro = build_macro_features(data["fred"])
    cross_asset = build_cross_asset_features(data["fred"], data["crypto"])

    # Build a synthetic "market" observation from latest data
    market_features = {}

    if not macro.empty:
        latest_macro = macro.dropna(how="all").iloc[-1] if len(macro.dropna(how="all")) > 0 else pd.Series()
        for col in latest_macro.index:
            if col in feature_cols:
                market_features[col] = latest_macro[col]

    if not cross_asset.empty:
        latest_ca = cross_asset.dropna(how="all").iloc[-1] if len(cross_asset.dropna(how="all")) > 0 else pd.Series()
        for col in latest_ca.index:
            if col in feature_cols:
                market_features[col] = latest_ca[col]

    # Fill missing feature columns with NaN (HistGBT handles them)
    row = pd.DataFrame([{col: market_features.get(col, np.nan) for col in feature_cols}])

    try:
        prob = model.predict_proba(row)[0][1]
    except Exception:
        prob = 0.5

    score = int(prob * 100)

    # Determine label
    if score >= 75:
        label = "Critical"
    elif score >= 50:
        label = "Elevated"
    elif score >= 25:
        label = "Moderate"
    else:
        label = "Low"

    # Top drivers from macro
    drivers = []
    if market_features.get("ffr_3mo_chg", 0) and market_features["ffr_3mo_chg"] > 0.25:
        drivers.append("Fed rate acceleration")
    if market_features.get("yield_curve", 0) and market_features["yield_curve"] < 0:
        drivers.append("Yield curve inverted")
    if market_features.get("vix_2yr_pct", 0) and market_features["vix_2yr_pct"] > 0.8:
        drivers.append("VIX elevated (top 20% of 2yr range)")
    if market_features.get("sentiment_3mo_chg", 0) and market_features["sentiment_3mo_chg"] < -5:
        drivers.append("Consumer sentiment deteriorating")
    if market_features.get("cpi_accel", 0) and market_features["cpi_accel"] > 0.5:
        drivers.append("Inflation accelerating")
    if not drivers:
        drivers.append("No acute macro triggers detected")

    return {
        "compression_risk": score,
        "label": label,
        "top_drivers": drivers[:3],
        "as_of": pd.Timestamp.now().isoformat(),
        "probability": float(prob),
    }


def rank_stocks(model, feature_sets: dict, fundamentals: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """Rank stocks by compression vulnerability score."""
    rankings = []

    fund_lookup = {}
    if not fundamentals.empty:
        fund_lookup = fundamentals.set_index("ticker").to_dict("index")

    for ticker, df in feature_sets.items():
        # Use latest observation
        latest = df[feature_cols].iloc[-1:] if len(df) > 0 else None
        if latest is None:
            continue

        try:
            prob = model.predict_proba(latest)[0][1]
        except Exception:
            continue

        score = int(prob * 100)
        fund = fund_lookup.get(ticker, {})

        # Identify top risk factors
        risk_factors = []
        if df.get("pe_5yr_pct") is not None:
            pe_pct = df["pe_5yr_pct"].iloc[-1]
            if not pd.isna(pe_pct) and pe_pct > 0.8:
                risk_factors.append(f"P/E at {pe_pct:.0%} of 5yr range")
        if df.get("pe_12mo_expansion") is not None:
            pe_exp = df["pe_12mo_expansion"].iloc[-1]
            if not pd.isna(pe_exp) and pe_exp > 0.3:
                risk_factors.append(f"P/E expanded {pe_exp:.0%} in 12mo")
        if df.get("mom_3mo") is not None:
            mom = df["mom_3mo"].iloc[-1]
            if not pd.isna(mom) and mom > 0.2:
                risk_factors.append(f"Strong 3mo momentum (+{mom:.0%}) — extended")
        if df.get("vol_20d") is not None:
            vol = df["vol_20d"].iloc[-1]
            if not pd.isna(vol) and vol > 0.4:
                risk_factors.append("High volatility")
        if df.get("beta_60d") is not None:
            beta = df["beta_60d"].iloc[-1]
            if not pd.isna(beta) and beta > 1.5:
                risk_factors.append(f"High beta ({beta:.1f})")
        if df.get("dist_from_52w_high") is not None:
            dist = df["dist_from_52w_high"].iloc[-1]
            if not pd.isna(dist) and dist > -0.05:
                risk_factors.append("Near 52-week high")

        if not risk_factors:
            risk_factors = ["Within normal parameters"]

        rankings.append({
            "ticker": ticker,
            "compression_risk_score": score,
            "current_pe": fund.get("trailingPE"),
            "pe_percentile_5yr": round(df["pe_5yr_pct"].iloc[-1] * 100, 1) if "pe_5yr_pct" in df and not pd.isna(df["pe_5yr_pct"].iloc[-1]) else None,
            "ev_ebitda": fund.get("evToEbitda"),
            "earnings_growth": fund.get("earningsGrowth"),
            "revenue_growth": fund.get("revenueGrowth"),
            "price_momentum_3mo": round(df["mom_3mo"].iloc[-1] * 100, 1) if "mom_3mo" in df and not pd.isna(df["mom_3mo"].iloc[-1]) else None,
            "sector": fund.get("sector"),
            "debt_to_equity": fund.get("debtToEquity"),
            "risk_factors": risk_factors[:3],
        })

    result = pd.DataFrame(rankings).sort_values("compression_risk_score", ascending=False)
    print(f"  ✓ Ranked {len(result)} stocks")
    return result.reset_index(drop=True)
