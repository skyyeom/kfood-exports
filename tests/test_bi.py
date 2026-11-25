"""BI-friendly flat tables, views and CSV export, for Power BI / Looker Studio / Metabase / Excel."""

import csv

import pandas as pd
import sqlalchemy as sa
from test_preview import seeded_store, trends_store

from pipeline.bi import BI_TABLES, BI_VIEWS, export_csv, refresh_bi_tables
from pipeline.db import migration_sql


def test_rankings_table_is_flat_with_names_pillars_and_confidence():
    store = seeded_store()

    rows = pd.read_sql("select * from bi_rankings where category = 'all' order by rank", store.engine)

    usa = rows.iloc[0]
    assert (usa.iso3, usa["name"], usa["rank"], usa.confidence) == ("USA", "United States", 1, "robust")
    assert {"market_growth", "market_size", "korean_momentum", "entry_ease", "p_top3", "headline"} <= set(rows.columns)
    assert set(pd.read_sql("select distinct category from bi_rankings", store.engine).category) == {
        "all",
        "1704",
        "1806",
        "1905",
        "2105",
    }


def test_forecast_and_history_tables_cover_past_and_future_years():
    store = seeded_store()

    years = pd.read_sql("select distinct year from bi_forecast", store.engine).year.tolist()
    past = pd.read_sql("select distinct year from bi_score_history", store.engine).year.tolist()

    assert sorted(years) == [2026, 2027, 2028] and sorted(past) == list(range(2020, 2026))


def test_refreshing_replaces_rather_than_appends():
    store = seeded_store()
    before = pd.read_sql("select count(*) n from bi_rankings", store.engine).n[0]

    refresh_bi_tables(store)

    assert pd.read_sql("select count(*) n from bi_rankings", store.engine).n[0] == before


def test_monthly_exports_view_sums_hs6_lines_into_categories():
    store = trends_store()

    v = pd.read_sql("select * from bi_monthly_exports where iso3 = 'USA' and period = '202610'", store.engine)

    assert (v.category.tolist(), v.value_usd.tolist(), v.month.tolist()) == (["1905"], [2.0e6], ["2026-10-01"])


def test_export_writes_one_csv_per_table_and_view(tmp_path):
    store = seeded_store()

    written = export_csv(store, tmp_path)

    assert sorted(p.stem for p in written) == sorted(list(BI_TABLES) + list(BI_VIEWS))
    with open(tmp_path / "bi_rankings.csv", newline="") as f:
        assert next(csv.DictReader(f))["name"] == "United States"


def test_migration_creates_views_and_a_read_only_bi_role():
    sql = migration_sql()

    for name in BI_VIEWS:
        assert f"create or replace view {name} as" in sql
    assert "create role bi_reader nologin" in sql
    assert "grant select on bi_rankings" in sql and "to bi_reader" in sql
    bi_lines = [line for line in sql.lower().splitlines() if "bi_reader" in line]
    assert not any(
        word in line
        for line in bi_lines
        for word in ("grant insert", "grant update", "grant delete", "grant all", "for insert", "for update", "for all")
    )


def test_sqlite_store_has_the_views_too():
    store = seeded_store()

    names = sa.inspect(store.engine).get_view_names()
    assert set(BI_VIEWS) <= set(names)
