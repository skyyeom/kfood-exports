"""Run ingestion sources: fetch → upsert, with a run log per source."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

import pandas as pd

from pipeline.db import Store, UpsertResult


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


def run_sources(sources: list[Source], store: Store, http: Any, trigger: str = "local") -> list[RunResult]:
    results = []
    for source in sources:
        run_id = store.start_run(source.name, trigger)
        store.log_event(run_id, "start")
        step, fetched = "fetch", None
        try:
            df = source.fetch(http)
            fetched = len(df)
            store.log_event(run_id, "fetch", metrics={"rows": fetched})
            step = "upsert"
            changes = store.upsert(source.table, df, run_id)
            store.log_event(run_id, "upsert", metrics=asdict(changes))
        except Exception as e:  # noqa: BLE001 — one failing source must not stop the others
            error = f"{type(e).__name__}: {e}"
            store.log_event(run_id, step, "error", message=error)
            store.log_event(run_id, "finish", "error")
            store.finish_run(run_id, "failed", error=error, rows_fetched=fetched)
            results.append(RunResult(source.name, run_id, "failed"))
            continue
        store.log_event(run_id, "finish")
        store.finish_run(run_id, "success", rows_fetched=fetched, **_row_counts(changes))
        results.append(RunResult(source.name, run_id, "success", **asdict(changes)))
    return results
