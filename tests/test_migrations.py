from pathlib import Path

from pipeline.db import migration_sql

MIGRATION = Path(__file__).resolve().parents[1] / "supabase/migrations/0001_init.sql"


def test_committed_migration_matches_the_table_definitions():
    assert MIGRATION.read_text() == migration_sql(), "regenerate with: python -m pipeline.db > " + str(MIGRATION)


def test_migration_lets_the_browser_read_every_table_but_write_none():
    sql = migration_sql()

    for table in ("trade_flows", "ingest_runs", "ingest_events", "data_revisions", "ranking_snapshots"):
        assert f"alter table {table} enable row level security;" in sql
        assert f'create policy "public read" on {table} for select to anon, authenticated using (true);' in sql
    assert "for insert" not in sql and "for update" not in sql
