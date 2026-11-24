"""Run ingestion sources: fetch → validate → upsert → re-rank, with a run and step log per source.

    python -m pipeline.run --source fx [--source wdi ...] | --all

Environment: DATABASE_URL (default sqlite:///data/local.db); SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY to archive
raw responses in Supabase Storage (otherwise under ./data/raw); GITHUB_* variables set by Actions.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from pipeline.db import Store, UpsertResult
from pipeline.forecast import trends
from pipeline.http import Http
from pipeline.indicators import InsufficientData, rankings
from pipeline.raw import LocalRawStore, RecordingHttp, SupabaseRawStore
from pipeline.schema import validate
from pipeline.sources import SOURCES
from pipeline.sources.base import SkipSource

MAX_INVALID_SHARE = 0.2
RANKING_INPUTS = {"trade_flows", "country_indicators"}


class Source(Protocol):
    name: str
    table: str

    def fetch(self, http: Any) -> pd.DataFrame: ...


@dataclass
class RunResult:
    source: str
    run_id: str
    status: str
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0


def _row_counts(changes: UpsertResult) -> dict[str, int]:
    return {f"rows_{k}": v for k, v in asdict(changes).items()}


def _rerank(store: Store, run_id: str, force: bool = False) -> None:
    """Re-rank when scoring inputs changed since the last ranking, so a ranking missed earlier is caught up."""
    if not force and not store.ranking_is_stale():
        store.log_event(run_id, "rerank", "skipped", message="no trade or macro data changed")
        return
    trade, indicators = store.read("trade_flows"), store.read("country_indicators")
    try:
        by_category = rankings(trade, indicators)
    except InsufficientData as e:
        store.log_event(run_id, "rerank", "skipped", message=str(e))
        return
    for category, rows in by_category.items():
        store.save_ranking(run_id, category, "corrected", "default", rows)
    store.save_ranking(run_id, "all", "trend", "default", trends(trade, indicators))
    top3 = [r["iso3"] for r in by_category["all"][:3]]
    store.log_event(run_id, "rerank", metrics={"categories": len(by_category), "top3": top3})


def run_sources(
    sources: list[Source],
    store: Store,
    http: Any,
    trigger: str = "local",
    raw_store: Any = None,
    ci_run_url: str | None = None,
) -> list[RunResult]:
    results = []
    for source in sources:
        run_id = store.start_run(source.name, trigger, ci_run_url)
        store.log_event(run_id, "start")
        step, fetched, invalid, raw = "fetch", None, None, None
        try:
            recorder = RecordingHttp(http)
            try:
                df = source.fetch(recorder)
            finally:  # keep what upstream sent even when the fetch fails partway
                if raw_store and recorder.responses:
                    raw = raw_store.put(f"raw/{source.name}/{run_id}.zip", recorder.archive())
            fetched = len(df)
            store.log_event(run_id, "fetch", metrics={"rows": fetched, "raw": raw} if raw else {"rows": fetched})
            step = "validate"
            df, invalid, examples = validate(source.table, df)
            if fetched and invalid / fetched > MAX_INVALID_SHARE:
                raise ValueError(f"{invalid} of {fetched} rows failed validation: {'; '.join(examples)}")
            store.log_event(
                run_id,
                "validate",
                "ok" if not invalid else "warning",
                message="; ".join(examples) or None,
                metrics={"invalid": invalid},
            )
            step = "upsert"
            changes = store.upsert(source.table, df, run_id)
            store.log_event(run_id, "upsert", metrics=asdict(changes))
            if source.table in RANKING_INPUTS:
                step = "rerank"
                _rerank(store, run_id)
        except SkipSource as e:
            store.log_event(run_id, step, "skipped", message=str(e))
            store.log_event(run_id, "finish", "skipped")
            store.finish_run(run_id, "skipped", error=str(e))
            results.append(RunResult(source.name, run_id, "skipped"))
            continue
        except Exception as e:  # noqa: BLE001 — one failing source must not stop the others
            error = f"{type(e).__name__}: {e}"
            store.log_event(
                run_id, step, "error", message=error, metrics={"raw": raw} if raw and step == "fetch" else None
            )
            store.log_event(run_id, "finish", "error")
            store.finish_run(run_id, "failed", error=error, rows_fetched=fetched, rows_invalid=invalid)
            results.append(RunResult(source.name, run_id, "failed"))
            continue
        store.log_event(run_id, "finish")
        store.finish_run(run_id, "success", rows_fetched=fetched, rows_invalid=invalid, **_row_counts(changes))
        results.append(RunResult(source.name, run_id, "success", **asdict(changes)))
    return results


def _weekly_report(store: Store, trigger: str, ci_run_url: str | None) -> int:
    from pipeline.reports import build_report

    run_id = store.start_run("report", trigger, ci_run_url)
    store.log_event(run_id, "start")
    try:
        report = build_report(store)
        store.save_report(report)
    except Exception as e:  # noqa: BLE001 — logged for the Automation page, then reported via the exit code
        store.log_event(run_id, "report", "error", message=f"{type(e).__name__}: {e}")
        store.log_event(run_id, "finish", "error")
        store.finish_run(run_id, "failed", error=f"{type(e).__name__}: {e}")
        return 1
    store.log_event(run_id, "report", message=report["headline"], metrics={"week": report["week"]})
    store.log_event(run_id, "finish")
    store.finish_run(run_id, "success")
    print(f"report       success  {report['week']}: {report['headline']}")
    return 0


def _forced_rerank(store: Store, trigger: str, ci_run_url: str | None) -> int:
    run_id = store.start_run("rerank", trigger, ci_run_url)
    store.log_event(run_id, "start")
    try:
        _rerank(store, run_id, force=True)
    except Exception as e:  # noqa: BLE001 — logged for the Automation page, then reported via the exit code
        store.log_event(run_id, "rerank", "error", message=f"{type(e).__name__}: {e}")
        store.log_event(run_id, "finish", "error")
        store.finish_run(run_id, "failed", error=f"{type(e).__name__}: {e}")
        return 1
    store.log_event(run_id, "finish")
    store.finish_run(run_id, "success")
    print(f"rerank       success  run {run_id}")
    return 0


GITHUB_TRIGGERS = {"schedule": "schedule", "workflow_dispatch": "manual", "push": "ci", "pull_request": "ci"}


def _trigger(env) -> tuple[str, str | None]:
    event = env.get("GITHUB_EVENT_NAME")
    if not event:
        return "local", None
    url = f"{env.get('GITHUB_SERVER_URL')}/{env.get('GITHUB_REPOSITORY')}/actions/runs/{env.get('GITHUB_RUN_ID')}"
    return GITHUB_TRIGGERS.get(event, event), url


def _raw_store(env):
    if env.get("SUPABASE_URL") and env.get("SUPABASE_SERVICE_ROLE_KEY"):
        return SupabaseRawStore(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])
    return LocalRawStore(env.get("RAW_DIR", "data"))


def main(argv: list[str] | None = None, env=None, http: Any = None) -> int:
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(prog="python -m pipeline.run")
    parser.add_argument("--source", action="append", choices=sorted(SOURCES), help="repeatable")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--rerank", action="store_true", help="recompute rankings now (e.g. after a scoring change)")
    parser.add_argument("--report", action="store_true", help="generate and store this week's report")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:  # argparse exits 2 on bad arguments
        return int(e.code or 0)
    names = sorted(SOURCES) if args.all else args.source
    if not names and not args.rerank and not args.report:
        parser.print_usage()
        return 2
    url = env.get("DATABASE_URL", "sqlite:///data/local.db")
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    store = Store(url)
    if url.startswith("sqlite"):
        store.create_all()
    elif not store.is_migrated():  # never create tables on Postgres here: they would have no RLS policies
        print("Database has no WellGTM tables. Run supabase/migrations/0001_init.sql first.", file=sys.stderr)
        return 3
    trigger, ci_run_url = _trigger(env)
    if args.rerank:
        return _forced_rerank(store, trigger, ci_run_url)
    if args.report:
        return _weekly_report(store, trigger, ci_run_url)
    results = run_sources([SOURCES[n]() for n in names], store, http or Http(), trigger, _raw_store(env), ci_run_url)
    for r in results:
        print(f"{r.source:12} {r.status:8} +{r.inserted} ~{r.updated} ={r.unchanged}  run {r.run_id}")
    return 1 if any(r.status == "failed" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
