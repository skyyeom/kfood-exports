import json
import os
import zipfile

import pandas as pd
import pytest
from analysis_data import load_tables
from fakes import FIXTURES, RecordedHttp

from pipeline.db import Store
from pipeline.raw import LocalRawStore
from pipeline.run import run_sources
from pipeline.sources.fx import FxSource
from pipeline.sources.kcs_monthly import KcsMonthlySource


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
    s.drop_all()
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
        ["validate", "ok"],
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


def test_invalid_rows_are_rejected_and_counted_while_valid_rows_load(store):
    rows = fx_rows() + [
        {"source": "fx", "date": "2026-11-24", "base": "USD", "quote": "PHP", "rate": 58.1},
        {"source": "fx", "date": "2026-11-24", "base": "USD", "quote": "THB", "rate": 33.0},
        {"source": "fx", "date": "2026-11-24", "base": "USD", "quote": "XXX", "rate": -1.0},
    ]

    [result] = run_sources([StaticSource("fx", "fx_rates", rows)], store, http=None)

    assert (result.status, result.inserted) == ("success", 4)
    assert store.runs().rows_invalid.iloc[0] == 1
    assert store.events(result.run_id).set_index("step").loc["validate", "metrics"]["invalid"] == 1


def test_run_fails_when_more_than_a_fifth_of_rows_are_invalid(store):
    rows = fx_rows() + [{"source": "fx", "date": "not-a-date", "base": "USD", "quote": "PHP", "rate": 58.1}]

    [result] = run_sources([StaticSource("fx", "fx_rates", rows)], store, http=None)

    assert result.status == "failed"
    assert store.read("fx_rates").empty


def test_source_without_its_api_key_is_skipped_not_failed(store):
    [result] = run_sources([KcsMonthlySource(api_key="")], store, http=None)

    assert result.status == "skipped"
    fetch = store.events(result.run_id).set_index("step").loc["fetch"]
    assert fetch.status == "skipped" and "KCS_API_KEY" in fetch.message


def test_raw_upstream_responses_are_archived_per_run(store, tmp_path):
    http = RecordedHttp(("https://open.er-api.com/v6/latest/USD", {}, "fx_open_er_api.json"))
    raw = LocalRawStore(tmp_path)

    [result] = run_sources([FxSource()], store, http=http, raw_store=raw)

    raw = store.events(result.run_id).set_index("step").loc["fetch", "metrics"]["raw"]
    assert raw.endswith(f"raw/fx/{result.run_id}.zip")
    with zipfile.ZipFile(raw) as z:
        manifest = json.loads(z.read("manifest.json"))
        assert manifest[0]["url"] == "https://open.er-api.com/v6/latest/USD"
        assert z.read(manifest[0]["file"]) == (FIXTURES / "fx_open_er_api.json").read_bytes()


def test_one_unparseable_key_rejects_that_row_only(store):
    rows = [indicator_row(year=y) for y in (2020, 2021, 2022, 2023)] + [indicator_row(year="abc")]

    [result] = run_sources([StaticSource("wdi", "country_indicators", rows)], store, http=None)

    assert (result.status, result.inserted) == ("success", 4)
    assert store.runs().rows_invalid.iloc[0] == 1


def test_wrongly_typed_value_rejects_that_row_only(store):
    rows = [indicator_row(year=y) for y in (2020, 2021, 2022, 2023)] + [indicator_row(year=2024, value="n/a")]

    [result] = run_sources([StaticSource("wdi", "country_indicators", rows)], store, http=None)

    assert (result.status, result.inserted) == ("success", 4)


def test_payload_without_a_required_value_column_fails_the_run(store):
    rows = [{k: v for k, v in r.items() if k != "rate"} for r in fx_rows()]

    [result] = run_sources([StaticSource("fx", "fx_rates", rows)], store, http=None)

    assert result.status == "failed"


def test_boolean_strings_are_read_as_booleans(store):
    run_sources([StaticSource("wdi", "country_indicators", [indicator_row(imputed="False")])], store, http=None)

    assert not store.read("country_indicators").imputed.iloc[0]


def test_run_over_the_invalid_limit_logs_validation_once_as_an_error(store):
    rows = fx_rows() + [{"source": "fx", "date": "not-a-date", "base": "USD", "quote": "PHP", "rate": 58.1}]

    [result] = run_sources([StaticSource("fx", "fx_rates", rows)], store, http=None)

    validate = store.events(result.run_id).query("step == 'validate'")
    assert validate.status.tolist() == ["error"]


class PartlyFailingSource:
    """Fetches one page from upstream, then hits an error on the next."""

    name, table = "fx", "fx_rates"

    def fetch(self, http):
        http.get("https://open.er-api.com/v6/latest/USD")
        raise RuntimeError("second page failed")


def test_raw_responses_are_archived_even_when_the_fetch_fails_partway(store, tmp_path):
    http = RecordedHttp(("https://open.er-api.com/v6/latest/USD", {}, "fx_open_er_api.json"))

    [result] = run_sources([PartlyFailingSource()], store, http=http, raw_store=LocalRawStore(tmp_path))

    raw = store.events(result.run_id).set_index("step").loc["fetch", "metrics"]["raw"]
    with zipfile.ZipFile(raw) as z:
        assert json.loads(z.read("manifest.json"))[0]["url"] == "https://open.er-api.com/v6/latest/USD"


def scoring_sources():
    trade, indicators = load_tables()
    return [StaticSource("comtrade", "trade_flows", trade), StaticSource("wdi", "country_indicators", indicators)]


def test_new_trade_and_macro_data_produce_a_ranking_with_the_expected_top3(store):
    run_sources(scoring_sources(), store, http=None)

    ranking = store.latest_ranking(category="all")
    assert [c["iso3"] for c in ranking[:3]] == ["USA", "CHN", "PHL"]  # docs/pm/03_data_analysis.md §3


def test_rankings_are_stored_for_every_category(store):
    run_sources(scoring_sources(), store, http=None)

    for category in ("1704", "1806", "1905", "2105"):
        assert len(store.latest_ranking(category=category)) >= 3, category


def test_unchanged_data_does_not_rerank(store):
    run_sources(scoring_sources(), store, http=None)

    [_, wdi] = run_sources(scoring_sources(), store, http=None)

    assert store.events(wdi.run_id).set_index("step").loc["rerank", "status"] == "skipped"


@pytest.mark.parametrize(
    "url",
    ["postgresql://u:p@db.example.supabase.co:5432/postgres", "postgres://u:p@db.example.supabase.co:5432/postgres"],
)
def test_supabase_connection_strings_use_the_installed_psycopg_driver(url):
    assert Store(url).engine.url.drivername == "postgresql+psycopg"


def test_ranking_waits_for_korea_exports_instead_of_failing(store):
    trade, indicators = load_tables()
    imports_only = StaticSource("comtrade", "trade_flows", trade[trade.flow == "M"])

    [comtrade, _] = run_sources([imports_only, StaticSource("wdi", "country_indicators", indicators)], store, None)

    assert comtrade.status == "success"
    assert store.latest_ranking() == []


def test_data_without_a_current_ranking_is_ranked_on_the_next_run_even_if_unchanged(store):
    trade, indicators = load_tables()
    seed = store.start_run("seed")
    store.upsert("trade_flows", trade, seed)
    store.upsert("country_indicators", indicators, seed)

    run_sources([StaticSource("wdi", "country_indicators", indicators)], store, http=None)

    assert [c["iso3"] for c in store.latest_ranking()[:3]] == ["USA", "CHN", "PHL"]


def test_stored_ranking_explains_each_country(store):
    run_sources(scoring_sources(), store, http=None)

    usa = store.latest_ranking()[0]["reasons"]
    assert usa["summary"].startswith("The United States ranks #1")
    assert usa["confidence"]["level"] == "robust"


class KeyedSource:
    """Calls an API that takes its key as a query parameter, as data.go.kr does."""

    name, table = "fx", "fx_rates"

    def fetch(self, http):
        http.get("https://open.er-api.com/v6/latest/USD", params={"serviceKey": "SECRET-KEY", "pageNo": 1})
        return pd.DataFrame(fx_rows())


def test_raw_archive_never_stores_api_keys_sent_as_parameters(store, tmp_path):
    http = RecordedHttp(("https://open.er-api.com/v6/latest/USD", {}, "fx_open_er_api.json"))

    [result] = run_sources([KeyedSource()], store, http=http, raw_store=LocalRawStore(tmp_path))

    raw = store.events(result.run_id).set_index("step").loc["fetch", "metrics"]["raw"]
    with zipfile.ZipFile(raw) as z:
        manifest = z.read("manifest.json").decode()
    assert "SECRET-KEY" not in manifest
    assert json.loads(manifest)[0]["params"] == {"serviceKey": "<redacted>", "pageNo": 1}


def test_reranking_also_stores_score_history_and_forecast(store):
    run_sources(scoring_sources(), store, http=None)

    trend = store.latest_ranking(variant="trend")
    assert {r["year"] for r in trend["history"]} == {2020, 2021, 2022, 2023, 2024, 2025}
    assert {r["year"] for r in trend["forecast"]} == {2026, 2027, 2028}
    assert trend["holdout"]["actual_top3"] == ["USA", "CHN", "PHL"]
    assert next(r for r in trend["history"] if r["iso3"] == "USA")["name"] == "United States"


def months_between(start, end):
    y, m, out = int(start[:4]), int(start[4:]), []
    while f"{y}{m:02d}" <= end:
        out.append(f"{y}{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def test_monthly_korean_exports_make_a_provisional_ranking_and_a_month_on_month_comparison(store):
    trade, indicators = load_tables()
    monthly = [
        {
            "source": "kcs_monthly",
            "reporter_iso3": "KOR",
            "partner_iso3": iso,
            "flow": "X",
            "hs": "190590",
            "freq": "M",
            "period": p,
            "value_usd": v,
            "net_kg": 1.0,
            "imputed": False,
        }
        for iso, v in (("USA", 1.6e7), ("PHL", 3.0e6), ("WLD", 6.0e7))
        for p in months_between("202501", "202610")
    ]

    run_sources(
        [
            StaticSource("comtrade", "trade_flows", trade),
            StaticSource("wdi", "country_indicators", indicators),
            StaticSource("kcs_monthly", "trade_flows", monthly),
        ],
        store,
        http=None,
    )

    usa = next(r for r in store.latest_ranking() if r["iso3"] == "USA")
    change = store.latest_ranking(variant="month_change")
    assert usa["reasons"]["strengths"][1]["facts"][0]["period"] == "2026"  # Korean exports: provisional 2026
    assert change["latest"]["through"] == "2026-10" and change["previous"]["through"] == "2026-09"
    assert set(change["ranks"]) == {"all", "1704", "1806", "1905", "2105"} and change["ranks"]["all"]["USA"] >= 1
