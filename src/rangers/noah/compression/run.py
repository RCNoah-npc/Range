"""
Main entry point for compression detector.
Run from project root:
    python -m src.rangers.noah.compression.run

Or:
    python src/rangers/noah/compression/run.py
"""
import sys
import os

# Allow running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.rangers.noah.compression.ingest import load_all_data
from src.rangers.noah.compression.labeler import label_compression_events
from src.rangers.noah.compression.features import build_features
from src.rangers.noah.compression.model import train_and_evaluate
from src.rangers.noah.compression.scorer import score_market, rank_stocks
from src.rangers.noah.compression.output import write_outputs


def main():
    print("=" * 60)
    print("  Multiple Compression Signal Detector")
    print("  Powered by: Tsunami Engine + OpenClaw Data")
    print("=" * 60)

    print("\n[1/6] Loading data...")
    data = load_all_data()

    print("\n[2/6] Labeling compression events...")
    labeled = label_compression_events(data)

    if not labeled:
        print("\n  ERROR: No stocks could be labeled. Check data quality.")
        print("  Make sure collect_all_market_data.py ran successfully.")
        return

    print("\n[3/6] Engineering features...")
    feature_sets = build_features(labeled, data)

    if not feature_sets:
        print("\n  ERROR: No features could be built. Insufficient data overlap.")
        return

    print("\n[4/6] Training model...")
    model, metrics = train_and_evaluate(feature_sets)

    print("\n[5/6] Scoring current market...")
    market_score = score_market(model, data, metrics["feature_cols"])
    rankings = rank_stocks(model, feature_sets, data["fundamentals"], metrics["feature_cols"])

    print("\n[6/6] Writing outputs...")
    write_outputs(market_score, rankings, metrics)

    # Final summary
    print("\n" + "=" * 60)
    print(f"  MARKET COMPRESSION RISK: {market_score['compression_risk']}/100 ({market_score['label']})")
    print(f"  Drivers: {', '.join(market_score['top_drivers'])}")
    print(f"\n  Top 10 Compression Candidates:")
    print(f"  {'Ticker':<8} {'Risk':>5} {'P/E':>8} {'Sector':<20} Top Risk Factor")
    print(f"  {'─'*8} {'─'*5} {'─'*8} {'─'*20} {'─'*30}")
    for _, row in rankings.head(10).iterrows():
        pe_str = f"{row['current_pe']:.1f}" if row.get("current_pe") else "N/A"
        sector = (row.get("sector") or "Unknown")[:20]
        risk = row.get("risk_factors", [""])[0] if row.get("risk_factors") else ""
        print(f"  {row['ticker']:<8} {row['compression_risk_score']:>5} {pe_str:>8} {sector:<20} {risk}")
    print("=" * 60)


if __name__ == "__main__":
    main()
