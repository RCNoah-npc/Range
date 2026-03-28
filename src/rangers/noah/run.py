"""
Multiple Compression Signal Detector — Run Entry Point

Usage (from project root):
    python -m src.rangers.noah.run

Or directly:
    python src/rangers/noah/run.py

Outputs go to: agent_drops/output/
"""
import os
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rangers.noah.ingest import load_all_data
from src.rangers.noah.features import build_all_features
from src.rangers.noah.scorer import score_market, rank_stocks
from src.rangers.noah.output import write_outputs


def main():
    print("=" * 60)
    print("  Multiple Compression Signal Detector")
    print("=" * 60)

    print("\n1. Loading data...")
    data = load_all_data()

    print("\n2. Engineering features...")
    features_df, macro_features = build_all_features(data)

    print("\n3. Scoring market...")
    market = score_market(features_df, macro_features)

    print("\n4. Ranking stocks...")
    rankings = rank_stocks(features_df)

    print("\n5. Writing outputs...")
    output_dir = project_root / "agent_drops" / "output"
    dashboard_path = write_outputs(market, rankings, str(output_dir))

    # Print summary
    print("\n" + "=" * 60)
    print(f"  MARKET COMPRESSION RISK: {market['compression_risk']}/100 ({market['label']})")
    print(f"  Top drivers: {', '.join(market['top_drivers'][:3])}")
    print("=" * 60)

    print(f"\n  Top 10 Compression Candidates:")
    print(f"  {'Ticker':<8} {'Score':>6} {'Label':<10} {'P/E':>8} {'EV/EBITDA':>10} {'Top Risk Factor'}")
    print(f"  {'-'*8} {'-'*6} {'-'*10} {'-'*8} {'-'*10} {'-'*30}")
    for r in rankings[:10]:
        pe = f"{r['current_pe']:.1f}" if r.get("current_pe") else "N/A"
        ev = f"{r['ev_ebitda']:.1f}" if r.get("ev_ebitda") else "N/A"
        factor = r["risk_factors"][0] if r["risk_factors"] else ""
        print(f"  {r['ticker']:<8} {r['compression_risk_score']:>6.1f} {r['label']:<10} {pe:>8} {ev:>10} {factor}")

    print(f"\n  Bottom 5 (Least Compression Risk):")
    for r in rankings[-5:]:
        pe = f"{r['current_pe']:.1f}" if r.get("current_pe") else "N/A"
        print(f"  {r['ticker']:<8} {r['compression_risk_score']:>6.1f} {r['label']:<10} P/E: {pe}")

    print(f"\n  Full results: {dashboard_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
