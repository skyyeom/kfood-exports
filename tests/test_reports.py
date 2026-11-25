"""Automated weekly reports, built from the pipeline's own data (no LLM text)."""

from datetime import UTC, datetime

from test_preview import seeded_store, trends_store

from pipeline.reports import build_report, to_markdown

NOW = datetime(2026, 11, 24, 21, 0, tzinfo=UTC)  # Tuesday of ISO week 48


def test_report_is_titled_by_iso_week_and_lists_the_current_top3():
    r = build_report(seeded_store(), now=NOW)

    assert r["week"] == "2026-W48" and r["title"] == "Week 48, 2026 (23–29 Nov)"
    assert [c["iso3"] for c in r["top3"]] == ["USA", "CHN", "PHL"]
    assert r["top3"][0]["headline"].startswith("Leads on market size")


def test_first_report_says_there_is_nothing_to_compare_with():
    r = build_report(seeded_store(), now=NOW)

    assert r["movers"] == [] and "first report" in r["headline"].lower()


def test_report_compares_ranks_with_the_ranking_a_week_earlier():
    store = seeded_store()
    current = store.latest_ranking()
    earlier = [dict(c, rank={"PHL": 5, "IND": 3}.get(c["iso3"], c["rank"])) for c in current]
    store.save_ranking("old-run", "all", "corrected", "default", earlier, computed_at="2026-11-16T00:00:00.000+00:00")

    r = build_report(store, now=NOW)

    phl = next(m for m in r["movers"] if m["iso3"] == "PHL")
    assert (phl["was"], phl["now"], phl["change"]) == (5, 3, 2)
    assert "Philippines" in r["headline"] and "India" in r["headline"]


def test_report_summarises_the_latest_month_of_exports_and_ingredient_prices():
    r = build_report(trends_store(), now=NOW)

    assert r["exports"]["period"] == "202610" and round(r["exports"]["yoy"], 3) == 0.3
    assert r["prices"][0]["commodity"] == "cocoa"


def test_report_counts_this_weeks_pipeline_runs():
    r = build_report(seeded_store(), now=NOW)

    assert r["health"]["runs"] >= 4 and r["health"]["failed"] == 0


def test_markdown_has_a_section_per_part_of_the_report():
    md = to_markdown(build_report(seeded_store(), now=NOW))

    for heading in (
        "# WellGTM weekly report",
        "## TOP3",
        "## Rank changes",
        "## Exports",
        "## Forecast",
        "## Ingredient prices",
        "## Data and pipeline",
    ):
        assert heading in md, heading


def test_reports_are_stored_and_listed_newest_first():
    store = seeded_store()
    store.save_report(build_report(store, now=NOW))
    store.save_report(build_report(store, now=datetime(2026, 12, 1, 21, tzinfo=UTC)))

    weeks = [r["week"] for r in store.list_reports()]
    assert weeks == ["2026-W49", "2026-W48"]
    assert store.get_report("2026-W48")["title"].startswith("Week 48")


def test_report_includes_tracked_markets_and_their_alerts():
    store = seeded_store()
    store.watch("PHL")

    r = build_report(store, now=NOW)

    assert [m["name"] for m in r["tracked"]] == ["Philippines"]
    assert "## Tracked markets" in to_markdown(r)
