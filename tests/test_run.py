import os

import pandas as pd
import pytest

from pipeline.db import Store, metadata
from pipeline.run import run_sources


class StaticSource:
    """A source whose upstream API returns a fixed payload (the external boundary)."""

    def __init__(self, name, table, rows):
        self.name, self.table, self._rows = name, table, rows

    def fetch(self, http):
        return pd.DataFrame(self._rows)


def fx_rows(krw=1400.0, jpy=150.0):
    return [
        {"source": "fx", "date": "2026-11-24", "base": "USD", "quote": "KRW", "rate": krw},
        {"source": "fx", "date": "2026-11-24", "base": "USD", "quote": "JPY", "rate": jpy},
    ]


@pytest.fixture
def store():
    """In-memory SQLite by default; set TEST_DATABASE_URL to run the same tests against Postgres."""
    s = Store(os.environ.get("TEST_DATABASE_URL", "sqlite://"))
    metadata.drop_all(s.engine)
    s.create_all()
    return s


def test_successful_run_makes_rows_readable_with_provenance(store):
    [result] = run_sources([StaticSource("fx", "fx_rates", fx_rows())], store, http=None)

    assert result.status == "success"
    rows = store.read("fx_rates")
    assert sorted(rows.quote) == ["JPY", "KRW"]
    assert set(rows.run_id) == {result.run_id}
    assert rows.retrieved_at.notna().all()


def test_rerun_with_unchanged_upstream_data_changes_nothing(store):
    source = StaticSource("fx", "fx_rates", fx_rows())
    run_sources([source], store, http=None)

    [second] = run_sources([source], store, http=None)

    assert (second.status, second.inserted, second.updated, second.unchanged) == ("success", 0, 0, 2)
    assert store.revisions(second.run_id).empty
    assert len(store.read("fx_rates")) == 2


def test_unchanged_rows_keep_the_run_that_last_changed_them(store):
    source = StaticSource("fx", "fx_rates", fx_rows())
    [first] = run_sources([source], store, http=None)

    run_sources([source], store, http=None)

    assert set(store.read("fx_rates").run_id) == {first.run_id}


def test_revised_upstream_value_is_updated_and_recorded_old_to_new(store):
    run_sources([StaticSource("fx", "fx_rates", fx_rows(krw=1400.0))], store, http=None)

    [second] = run_sources([StaticSource("fx", "fx_rates", fx_rows(krw=1450.5))], store, http=None)

    assert (second.inserted, second.updated, second.unchanged) == (0, 1, 1)
    krw = store.read("fx_rates").set_index("quote").loc["KRW"]
    assert (krw.rate, krw.run_id) == (1450.5, second.run_id)
    [rev] = store.revisions(second.run_id).to_dict(orient="records")
    assert (rev["table_name"], rev["field"], rev["old_value"], rev["new_value"]) == (
        "fx_rates",
        "rate",
        "1400.0",
        "1450.5",
    )
    assert rev["row_key"] == {"source": "fx", "date": "2026-11-24", "base": "USD", "quote": "KRW"}


class BrokenSource:
    name, table = "comtrade", "trade_flows"

    def fetch(self, http):
        raise ConnectionError("upstream returned 503")


def test_failing_source_is_logged_and_does_not_stop_other_sources(store):
    broken, fx = run_sources([BrokenSource(), StaticSource("fx", "fx_rates", fx_rows())], store, http=None)

    assert (broken.status, fx.status) == ("failed", "success")
    runs = store.runs().set_index("source")
    assert runs.loc["comtrade", "status"] == "failed"
    assert "upstream returned 503" in runs.loc["comtrade", "error"]
    assert len(store.read("fx_rates")) == 2


def test_successful_run_records_each_step_for_the_live_feed(store):
    [ok] = run_sources([StaticSource("fx", "fx_rates", fx_rows())], store, http=None)

    events = store.events(ok.run_id)
    assert events[["step", "status"]].values.tolist() == [
        ["start", "ok"],
        ["fetch", "ok"],
        ["upsert", "ok"],
        ["finish", "ok"],
    ]


def test_fetch_step_reports_rows_fetched(store):
    [ok] = run_sources([StaticSource("fx", "fx_rates", fx_rows())], store, http=None)

    assert store.events(ok.run_id).set_index("step").loc["fetch", "metrics"] == {"rows": 2}


def test_failed_run_records_the_failing_step(store):
    [bad] = run_sources([BrokenSource()], store, http=None)

    assert store.events(bad.run_id)[["step", "status"]].values.tolist() == [
        ["start", "ok"],
        ["fetch", "error"],
        ["finish", "error"],
    ]


def test_run_has_a_measurable_duration(store):
    [ok] = run_sources([StaticSource("fx", "fx_rates", fx_rows())], store, http=None)

    run = store.runs().set_index("run_id").loc[ok.run_id]
    assert "." in run.started_at and "." in run.finished_at  # sub-second timestamps


def test_empty_fetch_succeeds_with_no_rows(store):
    [result] = run_sources([StaticSource("fx", "fx_rates", [])], store, http=None)

    assert (result.status, result.inserted) == ("success", 0)


def test_duplicate_keys_in_one_payload_fail_the_run_without_writing(store):
    rows = fx_rows() + [fx_rows(krw=1500.0)[0]]

    [result] = run_sources([StaticSource("fx", "fx_rates", rows)], store, http=None)

    assert result.status == "failed"
    assert "duplicate" in store.runs().error.iloc[0].lower()
    assert store.read("fx_rates").empty


def test_failed_upsert_still_records_rows_fetched(store):
    rows = fx_rows() + [fx_rows(krw=1500.0)[0]]

    [result] = run_sources([StaticSource("fx", "fx_rates", rows)], store, http=None)

    assert store.runs().set_index("run_id").loc[result.run_id, "rows_fetched"] == 3


def indicator_row(**overrides):
    row = {
        "source": "wdi",
        "iso3": "PHL",
        "indicator": "gdp_per_capita_usd",
        "year": 2024,
        "value": 3985.29,
        "unit": "USD",
        "source_code": "NY.GDP.PCAP.CD",
        "imputed": False,
    }
    return row | overrides


def test_column_missing_from_payload_leaves_stored_value_alone(store):
    run_sources([StaticSource("wdi", "country_indicators", [indicator_row()])], store, http=None)
    without_unit = {k: v for k, v in indicator_row().items() if k != "unit"}

    [second] = run_sources([StaticSource("wdi", "country_indicators", [without_unit])], store, http=None)

    assert (second.updated, store.read("country_indicators").unit.iloc[0]) == (0, "USD")


def test_values_are_coerced_to_column_types_so_reruns_match(store):
    payload = [indicator_row(year="2024", source_code=123)]
    run_sources([StaticSource("wdi", "country_indicators", payload)], store, http=None)

    [second] = run_sources([StaticSource("wdi", "country_indicators", payload)], store, http=None)

    assert (second.status, second.inserted, second.updated, second.unchanged) == ("success", 0, 0, 1)
