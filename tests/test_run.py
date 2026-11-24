import pandas as pd
import pytest

from pipeline.db import Store
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
    s = Store("sqlite://")
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
    assert len(store.read("fx_rates")) == 2


def test_revised_upstream_value_is_updated_and_recorded_old_to_new(store):
    run_sources([StaticSource("fx", "fx_rates", fx_rows(krw=1400.0))], store, http=None)

    [second] = run_sources([StaticSource("fx", "fx_rates", fx_rows(krw=1450.5))], store, http=None)

    assert (second.inserted, second.updated, second.unchanged) == (0, 1, 1)
    krw = store.read("fx_rates").set_index("quote").loc["KRW"]
    assert (krw.rate, krw.run_id) == (1450.5, second.run_id)
    [rev] = store.revisions(second.run_id).to_dict(orient="records")
    assert (rev["table_name"], rev["field"], rev["old_value"], rev["new_value"]) == ("fx_rates", "rate", "1400.0", "1450.5")
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


def test_run_records_each_step_as_an_event_for_the_live_feed(store):
    [ok] = run_sources([StaticSource("fx", "fx_rates", fx_rows())], store, http=None)
    [bad] = run_sources([BrokenSource()], store, http=None)

    ok_steps = store.events(ok.run_id)[["step", "status"]].values.tolist()
    assert ok_steps == [["start", "ok"], ["fetch", "ok"], ["upsert", "ok"], ["finish", "ok"]]
    assert store.events(ok.run_id).set_index("step").loc["fetch", "metrics"] == {"rows": 2}
    bad_steps = store.events(bad.run_id)[["step", "status"]].values.tolist()
    assert bad_steps == [["start", "ok"], ["fetch", "error"], ["finish", "error"]]
