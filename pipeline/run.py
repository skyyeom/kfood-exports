"""Run ingestion sources: fetch → upsert, with a run log per source."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

import pandas as pd

from pipeline.db import Store, UpsertResult
from pipeline.raw import RecordingHttp
from pipeline.schema import validate
from pipeline.sources.base import SkipSource

MAX_INVALID_SHARE = 0.2


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


def run_sources(
    sources: list[Source], store: Store, http: Any, trigger: str = "local", raw_store: Any = None
) -> list[RunResult]:
    results = []
    for source in sources:
        run_id = store.start_run(source.name, trigger)
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
