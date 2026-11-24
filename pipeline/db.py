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
    [("source", sa.Text), ("reporter_iso3", sa.Text), ("partner_iso3", sa.Text), ("flow", sa.Text),
     ("hs", sa.Text), ("freq", sa.Text), ("period", sa.Text)],
    [("value_usd", sa.Float), ("net_kg", sa.Float), ("imputed", sa.Boolean)],
)
country_indicators = _data_table(
    "country_indicators",
    [("source", sa.Text), ("iso3", sa.Text), ("indicator", sa.Text), ("year", sa.Integer)],
    [("value", sa.Float), ("unit", sa.Text), ("source_code", sa.Text), ("imputed", sa.Boolean)],
)
tariffs = _data_table(
    "tariffs",
    [("source", sa.Text), ("importer_iso3", sa.Text), ("hs", sa.Text), ("rate_type", sa.Text),
     ("agreement", sa.Text), ("effective_from", sa.Text)],
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
    *[sa.Column(c, sa.Integer) for c in ("rows_fetched", "rows_inserted", "rows_updated", "rows_unchanged",
                                         "rows_invalid")],
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

DATA_TABLES = {t.name: t for t in (trade_flows, country_indicators, tariffs, fx_rates, commodity_prices)}


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class UpsertResult:
    inserted: int
    updated: int
    unchanged: int


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame rows as plain Python values, with NaN/NaT as None."""
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


def _same(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) or isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _text(v) -> str | None:
    return None if v is None else str(v)


class Store:
    def __init__(self, url: str):
        self.engine = sa.create_engine(url)

    def create_all(self) -> None:
        metadata.create_all(self.engine)

    def start_run(self, source: str, trigger: str = "local", ci_run_url: str | None = None) -> str:
        run_id = str(uuid.uuid4())
        with self.engine.begin() as c:
            c.execute(ingest_runs.insert().values(run_id=run_id, source=source, trigger=trigger, status="running",
                                                  started_at=now(), ci_run_url=ci_run_url))
        return run_id

    def log_event(self, run_id: str, step: str, status: str = "ok", message: str | None = None,
                  metrics: dict | None = None) -> None:
        with self.engine.begin() as c:
            c.execute(ingest_events.insert().values(run_id=run_id, ts=now(), step=step, status=status,
                                                    message=message, metrics=metrics))

    def finish_run(self, run_id: str, status: str, error: str | None = None, **counts: int) -> None:
        with self.engine.begin() as c:
            c.execute(ingest_runs.update().where(ingest_runs.c.run_id == run_id)
                      .values(status=status, finished_at=now(), error=error, **counts))

    def upsert(self, table: str, df: pd.DataFrame, run_id: str) -> UpsertResult:
        """Insert new rows and update changed ones, matched on the table's natural key. Unchanged rows are untouched."""
        t = DATA_TABLES[table]
        keys = [c.name for c in t.primary_key.columns]
        values = [c.name for c in t.columns if c.name not in keys and c.name not in ("retrieved_at", "run_id")]
        stamp = {"retrieved_at": now(), "run_id": run_id}
        with self.engine.begin() as c:
            sources = df["source"].unique().tolist()
            existing = {tuple(r[k] for k in keys): r for r in c.execute(t.select().where(t.c.source.in_(sources)))
                        .mappings()}
            new, changed, revisions = [], [], []
            for row in _records(df):
                row = {col: row.get(col) for col in keys + values}
                old = existing.get(tuple(row[k] for k in keys))
                if old is None:
                    new.append(row | stamp)
                    continue
                diffs = [v for v in values if not _same(old[v], row[v])]
                if diffs:
                    changed.append(row)
                    row_key = {k: row[k] for k in keys}
                    revisions += [{"run_id": run_id, "table_name": table, "row_key": row_key, "field": v,
                                   "old_value": _text(old[v]), "new_value": _text(row[v]),
                                   "detected_at": stamp["retrieved_at"]} for v in diffs]
            if new:
                c.execute(t.insert(), new)
            for row in changed:
                c.execute(t.update().where(*[t.c[k] == row[k] for k in keys]).values(**{v: row[v] for v in values},
                                                                                   **stamp))
            if revisions:
                c.execute(data_revisions.insert(), revisions)
        return UpsertResult(len(new), len(changed), len(df) - len(new) - len(changed))

    def runs(self) -> pd.DataFrame:
        with self.engine.connect() as c:
            return pd.read_sql(ingest_runs.select().order_by(ingest_runs.c.started_at), c)

    def events(self, run_id: str) -> pd.DataFrame:
        with self.engine.connect() as c:
            return pd.read_sql(ingest_events.select().where(ingest_events.c.run_id == run_id)
                               .order_by(ingest_events.c.id), c)

    def revisions(self, run_id: str) -> pd.DataFrame:
        with self.engine.connect() as c:
            return pd.read_sql(data_revisions.select().where(data_revisions.c.run_id == run_id), c)

    def read(self, table: str) -> pd.DataFrame:
        with self.engine.connect() as c:
            return pd.read_sql(metadata.tables[table].select(), c)
