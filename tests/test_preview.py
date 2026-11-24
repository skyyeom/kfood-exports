from datetime import UTC, datetime

from analysis_data import load_tables
from test_run import StaticSource, fx_rows

from pipeline.db import Store
from pipeline.preview import next_run, state
from pipeline.run import run_sources


def seeded_store():
    s = Store("sqlite://")
    s.create_all()
    trade, indicators = load_tables()
    run_sources(
        [
            StaticSource("comtrade", "trade_flows", trade),
            StaticSource("wdi", "country_indicators", indicators),
            StaticSource("fx", "fx_rates", fx_rows()),
        ],
        s,
        http=None,
    )
    run_sources([StaticSource("fx", "fx_rates", fx_rows(krw=1450.5))], s, http=None)
    return s


def test_state_reports_each_sources_latest_run():
    sources = {s["source"]: s for s in state(seeded_store())["sources"]}

    assert sources["fx"]["status"] == "success" and sources["fx"]["last_success"]
    assert sources["pinksheet"]["status"] == "never run"


def test_state_includes_the_current_top3_and_recent_revisions():
    st = state(seeded_store())

    assert [c["iso3"] for c in st["ranking"]["all"][:3]] == ["USA", "CHN", "PHL"]
    [rev] = st["revisions"]
    assert (rev["field"], rev["old_value"], rev["new_value"]) == ("rate", "1400.0", "1450.5")


def test_state_lists_runs_newest_first_with_their_steps():
    runs = state(seeded_store())["runs"]

    assert runs[0]["source"] == "fx"
    assert [e["step"] for e in runs[0]["events"]] == ["start", "fetch", "validate", "upsert", "finish"]


def test_next_weekly_run_is_the_coming_monday_1800_utc():
    assert next_run("comtrade", now=datetime(2026, 11, 24, 12, tzinfo=UTC)) == "2026-11-30T18:00:00+00:00"
