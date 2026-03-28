# src/rangers/noah/tsunami/cli.py
"""Click-based CLI entry point for the Tsunami Engine."""

from __future__ import annotations

import logging
import sys
from typing import Optional

import click

from .adapters.yfinance_adapter import YFinanceAdapter
from .config import (
    COMPRESSION_GATE,
    DEFAULT_WIN_PROB,
    MAX_POSITION_PCT,
    VULNERABILITY_GATE,
)
from .db import get_connection, init_db
from .pipeline.backtester import run_backtest
from .pipeline.compressor import compress
from .pipeline.filter import filter_targets
from .pipeline.scanner import scan_ticker
from .pipeline.sizer import size_all
from .pipeline.underwriter import underwrite_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _get_adapter() -> YFinanceAdapter:
    return YFinanceAdapter()


@click.group()
@click.option("--db", default=None, help="Override SQLite database path.")
@click.pass_context
def cli(ctx: click.Context, db: Optional[str]) -> None:
    """Tsunami Engine: AI Disruption Multiple Compression Scanner."""
    ctx.ensure_object(dict)
    if db:
        ctx.obj["db_path"] = db
    else:
        from .config import DB_PATH
        ctx.obj["db_path"] = DB_PATH
    init_db(ctx.obj["db_path"])


# Also expose as 'tsunami' for backward compatibility
tsunami = cli


@cli.command()
@click.pass_context
def seed(ctx: click.Context) -> None:
    """Load historical casualties into the database."""
    import csv
    from .config import CASUALTIES_PATH

    db_path = ctx.obj["db_path"]

    with open(CASUALTIES_PATH, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with get_connection(db_path) as conn:
        for i, row in enumerate(rows, start=1):
            target_id = f"TGT_{i:03d}"
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO target_companies
                    (target_id, ticker, company, sector)
                    VALUES (?, ?, ?, ?)
                    """,
                    (target_id, row["ticker"], row["company"], row["sector"]),
                )
            except Exception as exc:
                click.echo(f"Warning: could not insert {row['ticker']}: {exc}")

    click.echo(f"Seeded {len(rows)} casualties into target_companies.")


@cli.command()
@click.argument("ticker")
@click.pass_context
def scan(ctx: click.Context, ticker: str) -> None:
    """Run vulnerability scan on a single ticker."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()
    ticker = ticker.upper()

    result = scan_ticker(ticker, adapter, db_path=db_path)
    if result is None:
        click.echo(f"{ticker}: Below vulnerability gate ({VULNERABILITY_GATE}). No action.")
    else:
        click.echo(
            f"{ticker}: vulnerability_score={result.vulnerability_score:.4f} "
            f"(gate={VULNERABILITY_GATE}). PASSED."
        )


@cli.command(name="compress")
@click.argument("ticker")
@click.pass_context
def compress_cmd(ctx: click.Context, ticker: str) -> None:
    """Calculate price target via multiple compression for a ticker."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()
    ticker = ticker.upper()

    # Must scan first
    prediction = scan_ticker(ticker, adapter, db_path=db_path)
    if prediction is None:
        click.echo(f"{ticker}: Did not pass scanner. Cannot compress.")
        return

    result = compress(prediction, db_path=db_path)
    if result is None:
        click.echo(
            f"{ticker}: Predicted drop below compression gate ({COMPRESSION_GATE:.0%}). No action."
        )
    else:
        click.echo(
            f"{ticker}: projected_price=${result.projected_price:.2f}, "
            f"predicted_drop={result.predicted_drop_pct:.2%}. QUALIFIED."
        )


@cli.command()
@click.pass_context
def backtest(ctx: click.Context) -> None:
    """Train model on historical casualties and extract feature weights."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    try:
        weights, r_squared = run_backtest(adapter, db_path=db_path)
        click.echo(f"Backtest complete. R-squared: {r_squared:.4f}")
        click.echo("Feature weights:")
        for feat, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            click.echo(f"  {feat}: {w:.4f}")
    except ValueError as exc:
        click.echo(f"Backtest failed: {exc}", err=True)
        sys.exit(1)


@cli.command(name="filter")
@click.pass_context
def filter_cmd(ctx: click.Context) -> None:
    """Rank targets by VRP (cheapest puts first)."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    # Load all targets that have predictions with predicted_drop > gate
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT tc.target_id, tc.ticker, tc.sector,
                   fp.sga_pct, fp.gross_margin_pct, fp.debt_to_equity,
                   fp.fcf_yield_pct, fp.roic_pct, fp.vulnerability_score,
                   fp.current_eps, fp.current_pe, fp.eps_decay_pct,
                   fp.terminal_pe, fp.projected_price, fp.predicted_drop_pct
            FROM target_companies tc
            JOIN fundamental_predictions fp ON tc.target_id = fp.target_id
            WHERE fp.predicted_drop_pct > ?
            AND fp.model_id = (
                SELECT MAX(model_id) FROM fundamental_predictions
                WHERE target_id = tc.target_id
            )
            """,
            (COMPRESSION_GATE,),
        ).fetchall()

    if not rows:
        click.echo("No targets with sufficient predicted drop. Run scan + compress first.")
        return

    from .models.schemas import Prediction

    predictions = []
    for r in rows:
        try:
            spot = adapter.get_price(r["ticker"])
        except Exception:
            spot = 0.0
        predictions.append(
            Prediction(
                target_id=r["target_id"],
                ticker=r["ticker"],
                sga_pct=r["sga_pct"] or 0.0,
                gross_margin_pct=r["gross_margin_pct"] or 0.0,
                debt_to_equity=r["debt_to_equity"] or 0.0,
                fcf_yield_pct=r["fcf_yield_pct"] or 0.0,
                roic_pct=r["roic_pct"] or 0.0,
                vulnerability_score=r["vulnerability_score"] or 0.0,
                current_eps=r["current_eps"] or 0.0,
                current_pe=r["current_pe"] or 0.0,
                current_spot=spot,
                eps_decay_pct=r["eps_decay_pct"] or 0.0,
                terminal_pe=r["terminal_pe"] or 0.0,
                projected_price=r["projected_price"] or 0.0,
                predicted_drop_pct=r["predicted_drop_pct"] or 0.0,
            )
        )

    filtered = filter_targets(predictions, adapter, db_path=db_path)
    if not filtered:
        click.echo("No targets passed VRP filter.")
        return

    click.echo(f"\n{'Ticker':<10} {'VRP':<10} {'IV':<10} {'HV':<10} {'Status':<15}")
    click.echo("-" * 55)
    for pred, friction in filtered:
        status = "DISCOUNT" if friction.vrp_spread < 0 else "FAIR VALUE"
        click.echo(
            f"{pred.ticker:<10} {friction.vrp_spread:<10.4f} "
            f"{friction.atm_put_iv:<10.4f} {friction.hv_252d:<10.4f} {status:<15}"
        )


@cli.command()
@click.option("--portfolio", default=100000.0, help="Portfolio value in dollars.")
@click.pass_context
def size(ctx: click.Context, portfolio: float) -> None:
    """Kelly allocation across approved targets."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    # Rebuild predictions from DB
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT tc.target_id, tc.ticker,
                   fp.sga_pct, fp.gross_margin_pct, fp.debt_to_equity,
                   fp.fcf_yield_pct, fp.roic_pct, fp.vulnerability_score,
                   fp.current_eps, fp.current_pe, fp.eps_decay_pct,
                   fp.terminal_pe, fp.projected_price, fp.predicted_drop_pct,
                   mfl.live_spot, mfl.atm_put_iv, mfl.put_call_ratio,
                   mfl.est_premium_ask, mfl.hv_252d, mfl.vrp_spread
            FROM target_companies tc
            JOIN fundamental_predictions fp ON tc.target_id = fp.target_id
            JOIN market_friction_log mfl ON tc.target_id = mfl.target_id
            WHERE fp.predicted_drop_pct > ?
            AND mfl.vrp_spread < ?
            AND fp.model_id = (
                SELECT MAX(model_id) FROM fundamental_predictions
                WHERE target_id = tc.target_id
            )
            AND mfl.log_id = (
                SELECT MAX(log_id) FROM market_friction_log
                WHERE target_id = tc.target_id
            )
            """,
            (COMPRESSION_GATE, 0.15),
        ).fetchall()

    if not rows:
        click.echo("No filtered targets found. Run filter first.")
        return

    from .models.schemas import FrictionData, Prediction

    filtered = []
    for r in rows:
        pred = Prediction(
            target_id=r["target_id"], ticker=r["ticker"],
            sga_pct=r["sga_pct"] or 0.0, gross_margin_pct=r["gross_margin_pct"] or 0.0,
            debt_to_equity=r["debt_to_equity"] or 0.0, fcf_yield_pct=r["fcf_yield_pct"] or 0.0,
            roic_pct=r["roic_pct"] or 0.0, vulnerability_score=r["vulnerability_score"] or 0.0,
            current_eps=r["current_eps"] or 0.0, current_pe=r["current_pe"] or 0.0,
            current_spot=r["live_spot"] or 0.0, eps_decay_pct=r["eps_decay_pct"] or 0.0,
            terminal_pe=r["terminal_pe"] or 0.0, projected_price=r["projected_price"] or 0.0,
            predicted_drop_pct=r["predicted_drop_pct"] or 0.0,
        )
        friction = FrictionData(
            target_id=r["target_id"], ticker=r["ticker"],
            live_spot=r["live_spot"] or 0.0, atm_put_iv=r["atm_put_iv"] or 0.0,
            put_call_ratio=r["put_call_ratio"] or 1.0,
            est_premium_ask=r["est_premium_ask"] or 0.0,
            hv_252d=r["hv_252d"] or 0.0, vrp_spread=r["vrp_spread"] or 0.0,
        )
        filtered.append((pred, friction))

    signals = size_all(filtered, portfolio_value=portfolio)
    if not signals:
        click.echo("No positions sized (all rejected by Kelly).")
        return

    click.echo(f"\n{'Ticker':<10} {'Kelly%':<10} {'Capital':<12} {'Payoff':<10}")
    click.echo("-" * 42)
    for s in signals:
        click.echo(
            f"{s.ticker:<10} {s.kelly_pct:<10.4f} "
            f"${s.capital_to_deploy:<11.2f} {s.payoff_ratio:<10.2f}"
        )


@cli.command()
@click.option("--portfolio", default=100000.0, help="Portfolio value in dollars.")
@click.pass_context
def underwrite(ctx: click.Context, portfolio: float) -> None:
    """Generate execution matrix (strikes, expiry, contracts)."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    # This is the final stage -- we rebuild the full pipeline state from DB
    # and run underwriter on the sized signals.
    # For simplicity, we re-run size to get signals.
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT tc.target_id, tc.ticker,
                   fp.projected_price, fp.predicted_drop_pct,
                   mfl.live_spot, mfl.vrp_spread, mfl.est_premium_ask
            FROM target_companies tc
            JOIN fundamental_predictions fp ON tc.target_id = fp.target_id
            JOIN market_friction_log mfl ON tc.target_id = mfl.target_id
            WHERE fp.predicted_drop_pct > ?
            AND mfl.vrp_spread < ?
            AND fp.model_id = (
                SELECT MAX(model_id) FROM fundamental_predictions
                WHERE target_id = tc.target_id
            )
            AND mfl.log_id = (
                SELECT MAX(log_id) FROM market_friction_log
                WHERE target_id = tc.target_id
            )
            """,
            (COMPRESSION_GATE, 0.15),
        ).fetchall()

    if not rows:
        click.echo("No qualified targets. Run the full pipeline first.")
        return

    from .models.schemas import Signal

    signals = []
    for r in rows:
        signals.append(
            Signal(
                target_id=r["target_id"], ticker=r["ticker"],
                predicted_drop_pct=r["predicted_drop_pct"] or 0.0,
                projected_price=r["projected_price"] or 0.0,
                current_spot=r["live_spot"] or 0.0,
                vrp_spread=r["vrp_spread"] or 0.0,
                kelly_pct=min(0.10, MAX_POSITION_PCT),
                capital_to_deploy=portfolio * min(0.10, MAX_POSITION_PCT),
                win_probability=DEFAULT_WIN_PROB,
                payoff_ratio=0.0,
            )
        )

    execution_matrix = underwrite_all(signals, adapter, db_path=db_path)
    if not execution_matrix:
        click.echo("No actionable signals.")
        return

    click.echo(
        f"\n{'Ticker':<8} {'Strike':<8} {'Expiry':<12} {'Cts':<5} "
        f"{'Premium':<10} {'Capital':<12} {'ROP':<8} {'Decision':<10}"
    )
    click.echo("-" * 73)
    for row in execution_matrix:
        click.echo(
            f"{row.ticker:<8} {row.strike:<8.2f} {row.expiry_date:<12} "
            f"{row.contracts:<5d} ${row.premium_per_share:<9.2f} "
            f"${row.capital_deployed:<11.2f} {row.rop:<8.2f} {row.decision:<10}"
        )


@cli.command()
@click.option("--portfolio", default=100000.0, help="Portfolio value in dollars.")
@click.option("--paper", is_flag=True, help="Paper trading mode.")
@click.pass_context
def run(ctx: click.Context, portfolio: float, paper: bool) -> None:
    """Full pipeline end-to-end."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()
    mode = "PAPER" if paper else "LIVE"
    click.echo(f"=== Tsunami Engine [{mode}] ===\n")

    # Load all targets
    with get_connection(db_path) as conn:
        targets = conn.execute(
            "SELECT target_id, ticker, company, sector FROM target_companies"
        ).fetchall()

    if not targets:
        click.echo("No targets in database. Run 'tsunami seed' first.")
        return

    # Stage 1+2: Scan and compress each target
    click.echo(f"Stage 1+2: Scanning and compressing {len(targets)} targets...")
    qualified = []
    for t in targets:
        ticker = t["ticker"]
        prediction = scan_ticker(ticker, adapter, db_path=db_path)
        if prediction is None:
            click.echo(f"  {ticker}: below vulnerability gate -- skipped")
            continue

        compressed = compress(prediction, db_path=db_path)
        if compressed is None:
            click.echo(f"  {ticker}: below compression gate -- skipped")
            continue

        click.echo(
            f"  {ticker}: vuln={compressed.vulnerability_score:.3f}, "
            f"drop={compressed.predicted_drop_pct:.1%}, "
            f"target=${compressed.projected_price:.2f}"
        )
        qualified.append(compressed)

    if not qualified:
        click.echo("\nNo actionable signals.")
        return

    # Stage 3 (optional): VRP Filter
    click.echo(f"\nStage 4: VRP filtering {len(qualified)} targets...")
    filtered = filter_targets(qualified, adapter, db_path=db_path)
    if not filtered:
        click.echo("All targets rejected by VRP filter.")
        return
    click.echo(f"  {len(filtered)} targets passed VRP filter")

    # Stage 4: Size
    click.echo(f"\nStage 5: Kelly sizing (portfolio=${portfolio:,.0f})...")
    signals = size_all(filtered, portfolio_value=portfolio)
    if not signals:
        click.echo("All positions rejected by Kelly criterion.")
        return
    click.echo(f"  {len(signals)} positions sized")

    # Stage 5: Underwrite
    click.echo(f"\nStage 6: Underwriting...")
    execution_matrix = underwrite_all(signals, adapter, db_path=db_path)

    if not execution_matrix:
        click.echo("No contracts available for underwriting.")
        return

    # Print execution matrix
    click.echo(
        f"\n{'Ticker':<8} {'Strike':<8} {'Expiry':<12} {'Cts':<5} "
        f"{'Premium':<10} {'Capital':<12} {'ROP':<8} {'Decision':<10}"
    )
    click.echo("=" * 73)
    for row in execution_matrix:
        click.echo(
            f"{row.ticker:<8} {row.strike:<8.2f} {row.expiry_date:<12} "
            f"{row.contracts:<5d} ${row.premium_per_share:<9.2f} "
            f"${row.capital_deployed:<11.2f} {row.rop:<8.2f} {row.decision:<10}"
        )

    execute_count = sum(1 for r in execution_matrix if r.decision == "EXECUTE")
    total_capital = sum(r.capital_deployed for r in execution_matrix if r.decision == "EXECUTE")
    click.echo(f"\nSummary: {execute_count} EXECUTE, total capital=${total_capital:,.2f}")

    # Paper trade persistence
    if paper:
        click.echo("\n[PAPER MODE] Writing to paper_positions...")
        with get_connection(db_path) as conn:
            for row in execution_matrix:
                if row.decision == "EXECUTE":
                    # Find the matching signal
                    sig = next((s for s in signals if s.ticker == row.ticker), None)
                    if sig:
                        conn.execute(
                            """
                            INSERT INTO paper_positions (
                                target_id, strike, expiry_date, premium_at_open,
                                contracts, capital_deployed, spot_at_open,
                                predicted_drop_pct, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                            """,
                            (
                                sig.target_id,
                                row.strike,
                                row.expiry_date,
                                row.premium_per_share,
                                row.contracts,
                                row.capital_deployed,
                                sig.current_spot,
                                sig.predicted_drop_pct,
                            ),
                        )
        click.echo("Paper positions saved.")


@cli.command()
@click.pass_context
def test(ctx: click.Context) -> None:
    """Smoke test against CHGG (known casualty)."""
    db_path = ctx.obj["db_path"]
    adapter = _get_adapter()

    click.echo("=== Smoke Test: CHGG ===\n")

    # Ensure CHGG is in the DB
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT target_id FROM target_companies WHERE ticker = 'CHGG'"
        ).fetchone()
        if not row:
            conn.execute(
                """
                INSERT INTO target_companies (target_id, ticker, company, sector)
                VALUES ('TGT_001', 'CHGG', 'Chegg', 'EdTech')
                """
            )

    # Scan
    prediction = scan_ticker("CHGG", adapter, db_path=db_path)
    if prediction is None:
        click.echo("FAIL: CHGG did not pass scanner.")
        sys.exit(1)
    click.echo(f"Scanner: vulnerability_score={prediction.vulnerability_score:.4f} PASS")

    # Compress
    compressed = compress(prediction, db_path=db_path)
    if compressed is None:
        click.echo("FAIL: CHGG did not pass compressor.")
        sys.exit(1)

    drop = compressed.predicted_drop_pct
    click.echo(
        f"Compressor: projected_price=${compressed.projected_price:.2f}, "
        f"predicted_drop={drop:.1%}"
    )

    # Validate against known range
    if 0.30 <= drop <= 0.90:
        click.echo(f"Smoke test PASSED: predicted drop {drop:.1%} is in range [30%, 90%]")
    else:
        click.echo(
            f"WARNING: predicted drop {drop:.1%} outside expected range [30%, 90%]. "
            "Model may need recalibration."
        )


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
