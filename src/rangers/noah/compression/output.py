"""
Phase 6: Output Generation
Produce CSV, JSON, and dashboard-ready outputs.
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime


OUTPUT_DIR = Path(__file__).resolve().parents[0] / "output"


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_outputs(market_score: dict, rankings: pd.DataFrame, metrics: dict):
    """Write all output files."""
    ensure_output_dir()

    # 1. Rankings CSV
    rankings.to_csv(OUTPUT_DIR / "compression_rankings.csv", index=False)
    print(f"  ✓ compression_rankings.csv ({len(rankings)} stocks)")

    # 2. Rankings JSON (dashboard format)
    stock_rankings_json = []
    for _, row in rankings.iterrows():
        entry = {
            "ticker": row["ticker"],
            "compression_risk": int(row["compression_risk_score"]),
            "current_pe": _safe_num(row.get("current_pe")),
            "pe_percentile_5yr": _safe_num(row.get("pe_percentile_5yr")),
            "ev_ebitda": _safe_num(row.get("ev_ebitda")),
            "earnings_growth": _safe_pct(row.get("earnings_growth")),
            "revenue_growth": _safe_pct(row.get("revenue_growth")),
            "price_momentum_3mo": _safe_num(row.get("price_momentum_3mo")),
            "sector": row.get("sector"),
            "debt_to_equity": _safe_num(row.get("debt_to_equity")),
            "risk_factors": row.get("risk_factors", []),
        }
        stock_rankings_json.append(entry)

    dashboard_data = {
        "market_score": market_score,
        "stock_rankings": stock_rankings_json,
        "generated_at": datetime.now().isoformat(),
        "model_metrics": {
            "avg_precision": metrics.get("avg_precision"),
            "avg_recall": metrics.get("avg_recall"),
            "avg_f1": metrics.get("avg_f1"),
            "avg_precision_top_decile": metrics.get("avg_precision_top_decile"),
        },
    }
    _write_json(dashboard_data, OUTPUT_DIR / "compression_rankings.json")
    print(f"  ✓ compression_rankings.json")

    # 3. Market score standalone
    _write_json(market_score, OUTPUT_DIR / "market_score.json")
    print(f"  ✓ market_score.json")

    # 4. Model report
    model_report = {
        "avg_precision": metrics.get("avg_precision"),
        "avg_recall": metrics.get("avg_recall"),
        "avg_f1": metrics.get("avg_f1"),
        "avg_precision_top_decile": metrics.get("avg_precision_top_decile"),
        "feature_importances": metrics.get("feature_importances", {}),
        "cv_folds": metrics.get("cv_folds", []),
        "generated_at": datetime.now().isoformat(),
    }
    _write_json(model_report, OUTPUT_DIR / "model_report.json")
    print(f"  ✓ model_report.json")


def _write_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _safe_num(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return round(float(val), 2)
    except (TypeError, ValueError):
        return None


def _safe_pct(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return round(float(val) * 100, 1)
    except (TypeError, ValueError):
        return None
