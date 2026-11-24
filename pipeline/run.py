"""Run ingestion sources: fetch → upsert, with a run log per source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd

from pipeline.db import Store


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


def run_sources(sources: list[Source], store: Store, http: Any, trigger: str = "local") -> list[RunResult]:
    results = []
    for source in sources:
        run_id = store.start_run(source.name, trigger)
        store.log_event(run_id, "start")
        step = "fetch"
        try:
            df = source.fetch(http)
            store.log_event(run_id, "fetch", metrics={"rows": len(df)})
            step = "upsert"
            up = store.upsert(source.table, df, run_id)
            store.log_event(
                run_id, "upsert", metrics={"inserted": up.inserted, "updated": up.updated, "unchanged": up.unchanged}
            )
        except Exception as e:  # noqa: BLE001 — one failing source must not stop the others
            error = f"{type(e).__name__}: {e}"
            store.log_event(run_id, step, "error", message=error)
            store.log_event(run_id, "finish", "error")
            store.finish_run(run_id, "failed", error=error)
            results.append(RunResult(source.name, run_id, "failed"))
            continue
        store.log_event(run_id, "finish")
        store.finish_run(
            run_id,
            "success",
            rows_fetched=len(df),
            rows_inserted=up.inserted,
            rows_updated=up.updated,
            rows_unchanged=up.unchanged,
        )
        results.append(RunResult(source.name, run_id, "success", up.inserted, up.updated, up.unchanged))
    return results
