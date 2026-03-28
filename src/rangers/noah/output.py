"""
Output module — generates JSON and CSV for the dashboard widget.
"""
import json
import os
from datetime import datetime, timezone


def write_outputs(market_score, rankings, output_dir):
    """Write all output files for the dashboard."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Dashboard JSON — the main file the widget reads
    dashboard_data = {
        "generated_at": timestamp,
        "market_score": {
            **market_score,
            "as_of": timestamp,
        },
        "stock_rankings": rankings,
        "summary": {
            "total_scored": len(rankings),
            "critical": sum(1 for r in rankings if r["label"] == "Critical"),
            "high": sum(1 for r in rankings if r["label"] == "High"),
            "elevated": sum(1 for r in rankings if r["label"] == "Elevated"),
            "moderate": sum(1 for r in rankings if r["label"] == "Moderate"),
            "low": sum(1 for r in rankings if r["label"] == "Low"),
        }
    }

    dashboard_path = os.path.join(output_dir, "compression_dashboard.json")
    with open(dashboard_path, "w") as f:
        json.dump(dashboard_data, f, indent=2, default=str)
    print(f"  ✓ {dashboard_path}")

    # 2. Market score standalone
    market_path = os.path.join(output_dir, "market_score.json")
    with open(market_path, "w") as f:
        json.dump({"market_score": market_score, "as_of": timestamp}, f, indent=2)
    print(f"  ✓ {market_path}")

    # 3. CSV rankings
    csv_path = os.path.join(output_dir, "compression_rankings.csv")
    import csv
    if rankings:
        fieldnames = [k for k in rankings[0].keys() if k != "risk_factors"]
        fieldnames.append("risk_factors")
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rankings:
                row = {**r}
                row["risk_factors"] = " | ".join(r.get("risk_factors", []))
                writer.writerow(row)
    print(f"  ✓ {csv_path}")

    return dashboard_path
