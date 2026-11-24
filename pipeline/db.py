"""Database tables (see docs/data_dictionary.md) and the Store used by the pipeline."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd
import sqlalchemy as sa

metadata = sa.MetaData()


def _provenance() -> list[sa.Column]:
    return [sa.Column("retrieved_at", sa.Text, nullable=False), sa.Column("run_id", sa.Text, nullable=False)]


def _data_table(name: str, keys: list[tuple[str, type]], values: list[tuple[str, type]]) -> sa.Table:
    return sa.Table(
        name,
        metadata,
        *[sa.Column(k, t, nullable=False) for k, t in keys],
        *[sa.Column(v, t) for v, t in values],
        *_provenance(),
        sa.PrimaryKeyConstraint(*[k for k, _ in keys]),
    )


trade_flows = _data_table(
    "trade_flows",
    [
        ("source", sa.Text),
        ("reporter_iso3", sa.Text),
        ("partner_iso3", sa.Text),
        ("flow", sa.Text),
        ("hs", sa.Text),
        ("freq", sa.Text),
        ("period", sa.Text),
    ],
    [("value_usd", sa.Float), ("net_kg", sa.Float), ("imputed", sa.Boolean)],
)
country_indicators = _data_table(
    "country_indicators",
    [("source", sa.Text), ("iso3", sa.Text), ("indicator", sa.Text), ("year", sa.Integer)],
    [("value", sa.Float), ("unit", sa.Text), ("source_code", sa.Text), ("imputed", sa.Boolean)],
)
tariffs = _data_table(
    "tariffs",
    [
        ("source", sa.Text),
        ("importer_iso3", sa.Text),
        ("hs", sa.Text),
        ("rate_type", sa.Text),
        ("agreement", sa.Text),
        ("effective_from", sa.Text),
    ],
    [("effective_to", sa.Text), ("rate_pct", sa.Float), ("source_url", sa.Text)],
)
fx_rates = _data_table(
    "fx_rates",
    [("source", sa.Text), ("date", sa.Text), ("base", sa.Text), ("quote", sa.Text)],
    [("rate", sa.Float)],
)
commodity_prices = _data_table(
    "commodity_prices",
    [("source", sa.Text), ("commodity", sa.Text), ("month", sa.Text)],
    [("price", sa.Float), ("unit", sa.Text)],
)

ingest_runs = sa.Table(
    "ingest_runs",
    metadata,
    sa.Column("run_id", sa.Text, primary_key=True),
    sa.Column("source", sa.Text, nullable=False),
    sa.Column("trigger", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("started_at", sa.Text, nullable=False),
    sa.Column("finished_at", sa.Text),
    *[
        sa.Column(c, sa.Integer)
        for c in ("rows_fetched", "rows_inserted", "rows_updated", "rows_unchanged", "rows_invalid")
    ],
    sa.Column("error", sa.Text),
    sa.Column("ci_run_url", sa.Text),
)

ingest_events = sa.Table(
    "ingest_events",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("run_id", sa.Text, nullable=False),
    sa.Column("ts", sa.Text, nullable=False),
    sa.Column("step", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("message", sa.Text),
    sa.Column("metrics", sa.JSON),
)

data_revisions = sa.Table(
    "data_revisions",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("run_id", sa.Text, nullable=False),
    sa.Column("table_name", sa.Text, nullable=False),
    sa.Column("row_key", sa.JSON, nullable=False),
    sa.Column("field", sa.Text, nullable=False),
    sa.Column("old_value", sa.Text),
    sa.Column("new_value", sa.Text),
    sa.Column("detected_at", sa.Text, nullable=False),
)

ranking_snapshots = sa.Table(
    "ranking_snapshots",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("run_id", sa.Text, nullable=False),
    sa.Column("computed_at", sa.Text, nullable=False),
    sa.Column("category", sa.Text, nullable=False),
    sa.Column("variant", sa.Text, nullable=False),
    sa.Column("preset", sa.Text, nullable=False),
    sa.Column("payload", sa.JSON, nullable=False),
)

DATA_TABLES = {t.name: t for t in (trade_flows, country_indicators, tariffs, fx_rates, commodity_prices)}


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


@dataclass
class UpsertResult:
    inserted: int
    updated: int
    unchanged: int


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame rows as plain Python values, with NaN/NaT as None."""
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


_TRUE, _FALSE = {"true", "1", "yes"}, {"false", "0", "no"}


def cast_value(value, to: type):
    """Cast to a column's Python type. A value that can't be cast is returned unchanged so validation rejects it."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if to is bool:
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        return True if text in _TRUE else False if text in _FALSE else value
    try:
        return to(value)
    except (TypeError, ValueError):
        return value


def _coerce_rows(t: sa.Table, df: pd.DataFrame) -> list[dict]:
    """Rows restricted to the table's columns, each value cast to its column's Python type."""
    cols = [c for c in df.columns if c in t.c]
    types = {c: t.c[c].type.python_type for c in cols}
    return [{c: cast_value(v, types[c]) for c, v in row.items()} for row in _records(df[cols])]


def _values_equal(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _as_text(v) -> str | None:
    return None if v is None else str(v)


class Store:
    def __init__(self, url: str):
        # Supabase and most hosts give postgres:// or postgresql:// URLs; we ship psycopg 3, not psycopg2
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                url = "postgresql+psycopg://" + url.removeprefix(prefix)
        self.engine = sa.create_engine(url)

    def create_all(self) -> None:
        metadata.create_all(self.engine)

    def is_migrated(self) -> bool:
        tables = set(sa.inspect(self.engine).get_table_names())
        return all(t in tables for t in metadata.tables)

    def start_run(self, source: str, trigger: str = "local", ci_run_url: str | None = None) -> str:
        run_id = str(uuid.uuid4())
        with self.engine.begin() as c:
            c.execute(
                ingest_runs.insert().values(
                    run_id=run_id,
                    source=source,
                    trigger=trigger,
                    status="running",
                    started_at=now(),
                    ci_run_url=ci_run_url,
                )
            )
        return run_id

    def log_event(
        self, run_id: str, step: str, status: str = "ok", message: str | None = None, metrics: dict | None = None
    ) -> None:
        with self.engine.begin() as c:
            c.execute(
                ingest_events.insert().values(
                    run_id=run_id, ts=now(), step=step, status=status, message=message, metrics=metrics
                )
            )

    def finish_run(self, run_id: str, status: str, error: str | None = None, **counts: int) -> None:
        with self.engine.begin() as c:
            c.execute(
                ingest_runs.update()
                .where(ingest_runs.c.run_id == run_id)
                .values(status=status, finished_at=now(), error=error, **counts)
            )

    def upsert(self, table: str, df: pd.DataFrame, run_id: str) -> UpsertResult:
        """Insert new rows and update changed ones, matched on the table's natural key.

        Unchanged rows are untouched, so they keep the run_id and retrieved_at of the run that last changed them.
        Only columns present in the payload are compared and updated.
        """
        if df.empty:
            return UpsertResult(0, 0, 0)
        t = DATA_TABLES[table]
        keys = [c.name for c in t.primary_key.columns]
        if missing := [k for k in keys if k not in df.columns]:
            raise ValueError(f"{table} payload is missing key columns {missing}")
        values = [c for c in df.columns if c in t.c and c not in keys and c not in ("retrieved_at", "run_id")]
        rows = _coerce_rows(t, df)
        by_key = {tuple(r[k] for k in keys): r for r in rows}
        if len(by_key) < len(rows):
            raise ValueError(f"{table} payload has {len(rows) - len(by_key)} duplicate natural keys")
        stamp = {"retrieved_at": now(), "run_id": run_id}
        with self.engine.begin() as c:
            sources = sorted({r["source"] for r in rows})
            existing = {
                tuple(r[k] for k in keys): r for r in c.execute(t.select().where(t.c.source.in_(sources))).mappings()
            }
            new, changed, revisions = [], [], []
            for key, row in by_key.items():
                old = existing.get(key)
                if old is None:
                    new.append(row | stamp)
                    continue
                diffs = [v for v in values if not _values_equal(old[v], row[v])]
                if diffs:
                    changed.append(row)
                    row_key = {k: row[k] for k in keys}
                    revisions += [
                        {
                            "run_id": run_id,
                            "table_name": table,
                            "row_key": row_key,
                            "field": v,
                            "old_value": _as_text(old[v]),
                            "new_value": _as_text(row[v]),
                            "detected_at": stamp["retrieved_at"],
                        }
                        for v in diffs
                    ]
            if new:
                c.execute(t.insert(), new)
            for row in changed:
                c.execute(
                    t.update().where(*[t.c[k] == row[k] for k in keys]).values(**{v: row[v] for v in values}, **stamp)
                )
            if revisions:
                c.execute(data_revisions.insert(), revisions)
        return UpsertResult(len(new), len(changed), len(rows) - len(new) - len(changed))

    def save_ranking(self, run_id: str, category: str, variant: str, preset: str, payload: list[dict]) -> None:
        with self.engine.begin() as c:
            c.execute(
                ranking_snapshots.insert().values(
                    run_id=run_id, computed_at=now(), category=category, variant=variant, preset=preset, payload=payload
                )
            )

    def latest_ranking(self, category: str = "all", variant: str = "corrected", preset: str = "default") -> list[dict]:
        r = ranking_snapshots.c
        q = (
            ranking_snapshots.select()
            .where(r.category == category, r.variant == variant, r.preset == preset)
            .order_by(r.id.desc())
            .limit(1)
        )
        with self.engine.connect() as c:
            row = c.execute(q).mappings().first()
        return row["payload"] if row else []

    def ranking_is_stale(self, inputs: tuple[str, ...] = ("trade_flows", "country_indicators")) -> bool:
        """True when scoring inputs changed after the latest ranking was computed (or no ranking exists yet)."""
        with self.engine.connect() as c:
            changed = max(
                (c.execute(sa.select(sa.func.max(DATA_TABLES[t].c.retrieved_at))).scalar() or "") for t in inputs
            )
            ranked = c.execute(sa.select(sa.func.max(ranking_snapshots.c.computed_at))).scalar() or ""
        return bool(changed) and changed > ranked

    def runs(self) -> pd.DataFrame:
        with self.engine.connect() as c:
            return pd.read_sql(ingest_runs.select().order_by(ingest_runs.c.started_at), c)

    def events(self, run_id: str) -> pd.DataFrame:
        with self.engine.connect() as c:
            return pd.read_sql(
                ingest_events.select().where(ingest_events.c.run_id == run_id).order_by(ingest_events.c.id), c
            )

    def revisions(self, run_id: str) -> pd.DataFrame:
        with self.engine.connect() as c:
            return pd.read_sql(
                data_revisions.select().where(data_revisions.c.run_id == run_id).order_by(data_revisions.c.id), c
            )

    def read(self, table: str) -> pd.DataFrame:
        with self.engine.connect() as c:
            return pd.read_sql(metadata.tables[table].select(), c)


def migration_sql() -> str:
    """Postgres DDL for every table, plus RLS: anyone may read, only the service role (which bypasses RLS) writes."""
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable

    parts = ["-- Generated by `python -m pipeline.db` from pipeline/db.py. Do not edit by hand.\n"]
    for t in metadata.sorted_tables:
        ddl = str(CreateTable(t, if_not_exists=True).compile(dialect=postgresql.dialect())).strip()
        parts.append(f"{ddl};\n")
    parts.append("-- Row-level security: public read for the dashboard; writes only via the service role.")
    for t in metadata.sorted_tables:
        parts.append(f"alter table {t.name} enable row level security;")
        parts.append(f'drop policy if exists "public read" on {t.name};')
        parts.append(f'create policy "public read" on {t.name} for select to anon, authenticated using (true);')
    parts.append("\n-- Live run feed on the Automation page (Supabase Realtime).")
    parts.append("do $$ begin")
    parts.append("  alter publication supabase_realtime add table ingest_runs, ingest_events;")
    parts.append("exception when duplicate_object then null; end $$;")
    parts.append("\n-- Private bucket for raw upstream responses (raw/{source}/{run_id}.zip).")
    parts.append("insert into storage.buckets (id, name, public) values ('raw', 'raw', false) on conflict do nothing;")
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    print(migration_sql(), end="")
