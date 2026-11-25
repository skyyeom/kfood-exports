"""BI layer: flat tables refreshed on every re-rank, views over the raw data, and CSV export.

    python -m pipeline.bi export [--out data/exports]     # CSVs for Excel / Power BI

Power BI, Looker Studio, Metabase or Tableau can instead connect to the Supabase Postgres directly with the
read-only bi_reader role; see docs/bi_guide.md.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import sqlalchemy as sa

from pipeline.db import BI_TABLE_NAMES, BI_VIEWS, Store, metadata, now

BI_TABLES = BI_TABLE_NAMES
PILLARS = {
    "Market growth": "market_growth",
    "Market size": "market_size",
    "K-momentum (trade)": "korean_momentum",
    "Entry ease": "entry_ease",
}


def _replace(conn, name: str, rows: list[dict]) -> None:
    table = metadata.tables[name]
    conn.execute(table.delete())
    if rows:
        conn.execute(table.insert(), rows)


def refresh_bi_tables(store: Store) -> None:
    """Rewrite the flat BI tables from the latest rankings and trend (one transaction, so readers never see half)."""
    stamp = now()
    rankings = []
    for category in ("all", "1704", "1806", "1905", "2105"):
        for r in store.latest_ranking(category=category):
            reasons = r.get("reasons", {})
            rankings.append(
                {
                    "category": category,
                    "iso3": r["iso3"],
                    "name": reasons.get("name", r["iso3"]),
                    "rank": r["rank"],
                    "score": r["score"],
                    **{col: r.get(p) for p, col in PILLARS.items()},
                    "p_top3": r.get("top3_probability"),
                    "p_top3_any_weights": r.get("top3_prob_random_weights"),
                    "confidence": reasons.get("confidence", {}).get("level"),
                    "headline": reasons.get("headline"),
                    "latest_year": int(r["latest_year"]) if r.get("latest_year") else None,
                    "computed_at": stamp,
                }
            )
    trend = store.latest_ranking(variant="trend") or {}
    forecast = [
        {k: f[k] for k in ("year", "iso3", "name", "score", "low", "high", "rank", "p_top3", "model")}
        | {"computed_at": stamp}
        for f in trend.get("forecast", [])
    ]
    history = [
        {k: h[k] for k in ("year", "iso3", "name", "score", "rank")} | {"computed_at": stamp}
        for h in trend.get("history", [])
    ]
    with store.engine.begin() as c:
        _replace(c, "bi_rankings", rankings)
        _replace(c, "bi_forecast", forecast)
        _replace(c, "bi_score_history", history)


def export_csv(store: Store, out: Path | str) -> list[Path]:
    """One CSV per BI table and view."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    with store.engine.connect() as c:
        for name in (*BI_TABLES, *BI_VIEWS):
            path = out / f"{name}.csv"
            pd.read_sql(sa.text(f"select * from {name}"), c).to_csv(path, index=False)
            written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline.bi")
    parser.add_argument("command", choices=["export"])
    parser.add_argument("--out", default="data/exports")
    args = parser.parse_args(argv)
    store = Store(os.environ.get("DATABASE_URL", "sqlite:///data/local.db"))
    for path in export_csv(store, args.out):
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
