"""
Multiple Compression Scorer

Scores each stock on compression risk (0-100) based on:
1. Valuation stretch (how expensive vs history)
2. Macro headwinds (rates, yield curve, sentiment)
3. Momentum deterioration (are buyers leaving?)
4. AI disruption vulnerability (sector + labor exposure)

Also produces an overall market compression risk score.
"""
import numpy as np
import pandas as pd


# ── Sector classification for AI disruption risk ──────────────────────
AI_VULNERABLE_SECTORS = {
    "Technology", "Communication Services",
}
AI_RESILIENT_SECTORS = {
    "Energy", "Utilities", "Healthcare",
}
# Specific tickers flagged in the research paper
AI_LOSERS = {"CRM", "ADBE", "NOW", "ACN", "INTC"}
AI_WINNERS = {"NVDA", "AVGO", "AMAT", "GE", "XOM"}


def score_valuation_stretch(row):
    """0-100: How stretched is the valuation?"""
    score = 0
    weights = 0

    # Trailing P/E > 30 is elevated, > 40 is extreme
    pe = row.get("trailingPE")
    if pe and pe > 0:
        if pe > 50:
            score += 100
        elif pe > 40:
            score += 80
        elif pe > 30:
            score += 60
        elif pe > 25:
            score += 40
        elif pe > 20:
            score += 20
        else:
            score += 5
        weights += 1

    # Forward P/E divergence from trailing (expansion signal)
    fpe = row.get("forwardPE")
    if pe and fpe and pe > 0 and fpe > 0:
        expansion = pe / fpe
        if expansion > 1.3:
            score += 80  # trailing >> forward = earnings expected to catch up (risky if they don't)
        elif expansion > 1.1:
            score += 50
        elif expansion < 0.9:
            score += 20  # forward > trailing = market expects deceleration, already pricing compression
        weights += 1

    # EV/EBITDA
    ev = row.get("evToEbitda")
    if ev and ev > 0:
        if ev > 40:
            score += 90
        elif ev > 25:
            score += 60
        elif ev > 15:
            score += 30
        else:
            score += 10
        weights += 1

    # Price to Sales
    ps = row.get("priceToSales")
    if ps and ps > 0:
        if ps > 15:
            score += 85
        elif ps > 8:
            score += 55
        elif ps > 3:
            score += 25
        else:
            score += 5
        weights += 1

    return score / max(weights, 1)


def score_macro_headwinds(row):
    """0-100: How hostile is the macro environment for multiples?"""
    score = 0
    signals = 0

    # Fed funds rate level (higher = more pressure)
    ff = row.get("fed_funds_level")
    if ff is not None:
        if ff > 5:
            score += 90
        elif ff > 4:
            score += 70
        elif ff > 3:
            score += 50
        elif ff > 2:
            score += 30
        else:
            score += 10
        signals += 1

    # 10Y treasury (higher = long-duration assets compress)
    t10 = row.get("treasury_10y")
    if t10 is not None:
        if t10 > 5:
            score += 90
        elif t10 > 4.5:
            score += 70
        elif t10 > 4:
            score += 50
        elif t10 > 3.5:
            score += 30
        else:
            score += 10
        signals += 1

    # Yield curve inversion
    yc_inv = row.get("yield_curve_inverted")
    if yc_inv:
        score += 80
        signals += 1

    # VIX percentile (high = stress)
    vix_pct = row.get("vix_percentile")
    if vix_pct is not None:
        score += min(vix_pct, 100)
        signals += 1

    # Consumer sentiment (low = bad)
    sent = row.get("consumer_sentiment")
    if sent is not None:
        if sent < 60:
            score += 80
        elif sent < 70:
            score += 50
        elif sent < 80:
            score += 30
        else:
            score += 10
        signals += 1

    return score / max(signals, 1)


def score_momentum(row):
    """0-100: Is momentum deteriorating? (Higher = more compression risk)"""
    score = 0
    signals = 0

    # 3mo momentum (negative = selling pressure)
    mom3 = row.get("momentum_3mo")
    if mom3 is not None:
        if mom3 < -0.20:
            score += 90
        elif mom3 < -0.10:
            score += 70
        elif mom3 < -0.05:
            score += 50
        elif mom3 < 0:
            score += 30
        else:
            score += 10
        signals += 1

    # Distance from 52w high (far away = weak)
    dist = row.get("dist_from_52w_high")
    if dist is not None:
        if dist < -0.30:
            score += 90
        elif dist < -0.20:
            score += 70
        elif dist < -0.10:
            score += 50
        elif dist < -0.05:
            score += 30
        else:
            score += 10
        signals += 1

    # Relative strength vs SPY (underperforming = risk)
    rs = row.get("rel_strength_vs_spy_3mo")
    if rs is not None:
        if rs < -0.15:
            score += 85
        elif rs < -0.05:
            score += 55
        elif rs < 0:
            score += 30
        else:
            score += 10
        signals += 1

    # High volatility = unstable
    vol = row.get("volatility_20d")
    if vol is not None:
        if vol > 0.60:
            score += 85
        elif vol > 0.40:
            score += 60
        elif vol > 0.25:
            score += 35
        else:
            score += 10
        signals += 1

    return score / max(signals, 1)


def score_ai_disruption(row):
    """0-100: How vulnerable to AI disruption? Based on research paper framework."""
    ticker = row.get("ticker", "")
    sector = None

    # Check fundamentals for sector
    for key in ["sector"]:
        if key in row and row[key]:
            sector = row[key]

    score = 30  # baseline

    # Sector-level adjustment
    if sector in AI_VULNERABLE_SECTORS:
        score += 25
    elif sector in AI_RESILIENT_SECTORS:
        score -= 20

    # Specific ticker flags from research
    if ticker in AI_LOSERS:
        score += 30
    elif ticker in AI_WINNERS:
        score -= 25

    # High P/E + high beta in tech = dot-com beta inversion risk
    pe = row.get("trailingPE")
    beta = row.get("beta")
    if pe and beta and sector in AI_VULNERABLE_SECTORS:
        if pe > 35 and beta > 1.3:
            score += 20  # Beta inversion risk — rewarding risk with premium

    # Low margins + high valuation = vulnerable
    margins = row.get("profitMargins")
    if margins is not None and pe is not None:
        if margins < 0.15 and pe > 30:
            score += 15

    return max(0, min(100, score))


def compute_compression_score(row):
    """
    Weighted composite compression risk score (0-100).

    Weights reflect research paper priorities:
    - Valuation stretch is the primary driver
    - Macro headwinds are the systemic trigger
    - Momentum confirms the signal
    - AI disruption is the idiosyncratic amplifier
    """
    val = score_valuation_stretch(row)
    macro = score_macro_headwinds(row)
    mom = score_momentum(row)
    ai = score_ai_disruption(row)

    composite = (
        val * 0.30 +
        macro * 0.25 +
        mom * 0.25 +
        ai * 0.20
    )

    return {
        "compression_risk_score": round(composite, 1),
        "valuation_score": round(val, 1),
        "macro_score": round(macro, 1),
        "momentum_score": round(mom, 1),
        "ai_disruption_score": round(ai, 1),
    }


def get_risk_label(score):
    """Convert numeric score to human label."""
    if score >= 75:
        return "Critical"
    elif score >= 60:
        return "High"
    elif score >= 40:
        return "Elevated"
    elif score >= 25:
        return "Moderate"
    else:
        return "Low"


def get_top_risk_factors(scores_dict, row):
    """Return top 3 reasons for the compression risk score."""
    factors = []

    if scores_dict["valuation_score"] > 60:
        pe = row.get("trailingPE", "?")
        factors.append(f"Stretched valuation (P/E: {pe})")
    if scores_dict["macro_score"] > 60:
        factors.append("Hostile macro environment (elevated rates)")
    if scores_dict["momentum_score"] > 60:
        factors.append("Deteriorating price momentum")
    if scores_dict["ai_disruption_score"] > 60:
        factors.append("High AI disruption vulnerability")
    if scores_dict["valuation_score"] > 40 and scores_dict["valuation_score"] <= 60:
        factors.append("Moderately elevated valuation multiples")
    if scores_dict["macro_score"] > 40 and scores_dict["macro_score"] <= 60:
        factors.append("Mixed macro signals")

    # Specific flags
    yc = row.get("yield_curve_inverted")
    if yc:
        factors.append("Yield curve inverted")

    dist = row.get("dist_from_52w_high")
    if dist is not None and dist < -0.20:
        factors.append(f"Down {abs(dist)*100:.0f}% from 52-week high")

    return factors[:3] if factors else ["Within normal parameters"]


def score_market(features_df, macro_features):
    """Overall market compression risk score."""
    # Average the macro component across all stocks
    macro_score = score_macro_headwinds(macro_features)

    # Median valuation stretch across all stocks
    val_scores = []
    for _, row in features_df.iterrows():
        val_scores.append(score_valuation_stretch(row.to_dict()))
    median_val = np.median(val_scores) if val_scores else 50

    # Market-level momentum (SPY)
    spy_mom = features_df[features_df.get("ticker") == "SPY"]

    market_score = macro_score * 0.40 + median_val * 0.35 + (np.mean(val_scores) * 0.25 if val_scores else 50)

    # Top macro drivers
    drivers = []
    ff = macro_features.get("fed_funds_level")
    if ff and ff > 4:
        drivers.append(f"Fed funds rate at {ff}%")
    t10 = macro_features.get("treasury_10y")
    if t10 and t10 > 4:
        drivers.append(f"10Y Treasury at {t10}%")
    yc = macro_features.get("yield_curve_inverted")
    if yc:
        drivers.append("Yield curve inverted")
    vix = macro_features.get("vix_level")
    if vix and vix > 25:
        drivers.append(f"VIX elevated at {vix}")
    sent = macro_features.get("consumer_sentiment")
    if sent and sent < 70:
        drivers.append(f"Consumer sentiment weak ({sent})")

    if not drivers:
        drivers = ["Macro conditions within normal range"]

    return {
        "compression_risk": round(min(market_score, 100), 1),
        "label": get_risk_label(market_score),
        "macro_score": round(macro_score, 1),
        "median_valuation_score": round(median_val, 1),
        "top_drivers": drivers[:4],
    }


def rank_stocks(features_df):
    """Score and rank all stocks by compression risk."""
    rankings = []

    for _, row in features_df.iterrows():
        row_dict = row.to_dict()
        ticker = row_dict.get("ticker")
        if not ticker:
            continue

        scores = compute_compression_score(row_dict)
        risk_factors = get_top_risk_factors(scores, row_dict)

        rankings.append({
            "ticker": ticker,
            **scores,
            "label": get_risk_label(scores["compression_risk_score"]),
            "risk_factors": risk_factors,
            "current_pe": row_dict.get("trailingPE"),
            "forward_pe": row_dict.get("forwardPE"),
            "ev_ebitda": row_dict.get("evToEbitda"),
            "price_to_sales": row_dict.get("priceToSales"),
            "beta": row_dict.get("beta"),
            "earnings_growth": row_dict.get("earningsGrowth"),
            "revenue_growth": row_dict.get("revenueGrowth"),
            "profit_margins": row_dict.get("profitMargins"),
            "momentum_3mo": row_dict.get("momentum_3mo"),
            "dist_from_52w_high": row_dict.get("dist_from_52w_high"),
            "volatility_20d": row_dict.get("volatility_20d"),
        })

    rankings.sort(key=lambda x: x["compression_risk_score"], reverse=True)
    return rankings
