from datetime import UTC, datetime

import pytest
from analysis_data import load_tables
from test_run import StaticSource, fx_rows

from pipeline.db import Store
from pipeline.preview import country_state, next_run, state, trends_state
from pipeline.run import run_sources


def seeded_store(url="sqlite://"):
    s = Store(url)
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


def country_store():
    s = seeded_store()
    monthly = [
        {
            "source": "kcs_monthly",
            "reporter_iso3": "KOR",
            "partner_iso3": "USA",
            "flow": "X",
            "hs": hs6,
            "freq": "M",
            "period": period,
            "value_usd": v,
            "net_kg": 1.0,
            "imputed": False,
        }
        for hs6, period, v in [
            ("210500", "202609", 4.0e6),
            ("210500", "202610", 4664249.0),
            ("190531", "202610", 1.0e6),
            ("190590", "202610", 11.0e6),
        ]
    ]
    totals = [
        {
            "source": "kcs_nations",
            "reporter_iso3": "KOR",
            "partner_iso3": "USA",
            "flow": "X",
            "hs": "TOTAL",
            "freq": "M",
            "period": "202610",
            "value_usd": 10.0e9,
            "net_kg": None,
            "imputed": False,
        }
    ]
    tariffs = [
        {
            "source": "wits",
            "importer_iso3": "USA",
            "hs": hs6,
            "rate_type": "mfn",
            "agreement": "",
            "effective_from": "2023-01-01",
            "rate_pct": r,
            "source_url": "u",
        }
        for hs6, r in [("170410", 4.0), ("170490", 8.0)]
    ] + [
        {
            "source": "override",
            "importer_iso3": "USA",
            "hs": "1704",
            "rate_type": t,
            "agreement": a,
            "effective_from": "2025-08-07",
            "rate_pct": r,
            "source_url": "u",
        }
        for t, a, r in [("pref", "KORUS", 0.0), ("additional", "US reciprocal tariff", 15.0)]
    ]
    run_sources(
        [
            StaticSource("kcs_monthly", "trade_flows", monthly),
            StaticSource("kcs_nations", "trade_flows", totals),
            StaticSource("tariffs", "tariffs", tariffs),
        ],
        s,
        http=None,
    )
    return s


def test_country_page_has_the_name_rank_and_reasons(shared_country_store):
    c = country_state(shared_country_store, "USA")

    assert (c["name"], c["ranking"]["all"]["rank"]) == ("United States", 1)
    assert c["ranking"]["all"]["reasons"]["confidence"]["level"] == "robust"


def test_country_page_shows_monthly_korean_exports_by_category(shared_country_store):
    months = {
        (m["category"], m["period"]): m["value_usd"] for m in country_state(shared_country_store, "USA")["monthly"]
    }

    assert months[("2105", "202610")] == 4664249.0
    assert months[("1905", "202610")] == 12.0e6  # HS6 lines 190531 + 190590 summed into the heading


def test_country_page_shows_foods_share_of_koreas_exports(shared_country_store):
    share = country_state(shared_country_store, "USA")["food_share"]

    assert share["period"] == "202610"
    assert share["share"] == (4664249.0 + 12.0e6) / 10.0e9


def test_country_page_applies_the_tariff_rule_mfn_or_fta_plus_additional_duties(shared_country_store):
    [sugar] = [t for t in country_state(shared_country_store, "USA")["tariffs"] if t["hs"] == "1704"]

    # min(MFN average 6%, KORUS 0%) + 15% reciprocal = 15%
    assert (sugar["mfn_pct"], sugar["preferential_pct"], sugar["additional_pct"], sugar["applied_pct"]) == (
        6.0,
        0.0,
        15.0,
        15.0,
    )


def test_unknown_country_is_rejected(shared_country_store):
    import pytest

    with pytest.raises(KeyError):
        country_state(shared_country_store, "XXX")


def test_tariffs_warn_when_an_fta_exists_but_its_rates_are_not_entered():
    s = country_store()
    tariffs = [
        {
            "source": "wits",
            "importer_iso3": "PHL",
            "hs": "170490",
            "rate_type": "mfn",
            "agreement": "",
            "effective_from": "2023-01-01",
            "rate_pct": 14.4,
            "source_url": "u",
        }
    ]
    run_sources([StaticSource("tariffs", "tariffs", tariffs)], s, http=None)

    [sugar] = [t for t in country_state(s, "PHL")["tariffs"] if t["hs"] == "1704"]
    usa = country_state(s, "USA")

    assert sugar["fta_with_korea"] == "ASEAN–Korea FTA (AKFTA)" and sugar["fta_rate_missing"] is True
    assert not any(t["fta_rate_missing"] for t in usa["tariffs"] if t["hs"] == "1704")


def test_state_includes_the_score_trend_and_forecast():
    trend = state(seeded_store())["trend"]["all"]

    assert max(r["year"] for r in trend["history"]) == 2025 and min(r["year"] for r in trend["forecast"]) == 2026


def months(n=24, start=(2024, 11)):
    y, m = start
    out = []
    for _ in range(n):
        out.append(f"{y}{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def trends_store():
    s = Store("sqlite://")
    s.create_all()
    periods = months()  # 2024-11 .. 2026-10
    flows = []
    for i, p in enumerate(periods):
        later = i >= 12
        for partner, hs, before, after in [
            ("USA", "190590", 1.0e6, 2.0e6),
            ("PHL", "210500", 1.0e6, 1.5e6),
            ("WLD", "190590", 3.0e6, 4.0e6),
            ("WLD", "210500", 1.0e6, 1.2e6),
        ]:
            flows.append(
                {
                    "source": "kcs_monthly",
                    "reporter_iso3": "KOR",
                    "partner_iso3": partner,
                    "flow": "X",
                    "hs": hs,
                    "freq": "M",
                    "period": p,
                    "value_usd": after if later else before,
                    "net_kg": 1.0,
                    "imputed": False,
                }
            )
    prices = [
        {
            "source": "pinksheet",
            "commodity": "cocoa",
            "month": f"{p[:4]}-{p[4:]}",
            "price": 5.0 + i * 0.1,
            "unit": "USD/kg",
        }
        for i, p in enumerate(periods)
    ]
    run_sources(
        [StaticSource("kcs_monthly", "trade_flows", flows), StaticSource("pinksheet", "commodity_prices", prices)],
        s,
        http=None,
    )
    return s


def test_trends_show_koreas_monthly_kfood_exports_by_category():
    t = trends_state(trends_store())

    by = {(r["category"], r["period"]): r["value_usd"] for r in t["kfood_monthly"]}
    assert by[("1905", "202610")] == 4.0e6 and by[("2105", "202610")] == 1.2e6
    assert t["kfood_latest"] == {"period": "202610", "value_usd": 5.2e6, "yoy": 5.2e6 / 4.0e6 - 1}


def test_trends_rank_destinations_by_growth_over_the_last_12_months():
    growth = {r["iso3"]: r for r in trends_state(trends_store())["destinations"]}

    assert growth["USA"]["growth"] == pytest.approx(1.0) and growth["USA"]["last12_usd"] == 24.0e6
    assert growth["PHL"]["growth"] == pytest.approx(0.5)
    assert "WLD" not in growth


def test_trends_include_commodity_prices_with_change_over_a_year():
    [cocoa] = trends_state(trends_store())["commodities"]

    assert (cocoa["commodity"], cocoa["unit"], cocoa["latest_month"]) == ("cocoa", "USD/kg", "2026-10")
    assert cocoa["yoy"] == pytest.approx((5.0 + 2.3) / (5.0 + 1.1) - 1)
    assert len(cocoa["series"]) == 24


def count_queries(store, fn):
    import sqlalchemy as sa

    seen = []
    listener = lambda *a, **k: seen.append(1)
    sa.event.listen(store.engine, "before_cursor_execute", listener)
    try:
        fn()
    finally:
        sa.event.remove(store.engine, "before_cursor_execute", listener)
    return len(seen)


def test_a_dashboard_refresh_makes_a_small_fixed_number_of_queries():
    # Regression: one refresh made ~55 round trips (a query per run for events and for revisions) and read whole
    # tables to count rows; against Supabase that took 10.5 s and the browser abandoned the requests
    store = seeded_store()
    for _ in range(20):
        run_sources([StaticSource("fx", "fx_rates", fx_rows())], store, http=None)

    assert count_queries(store, lambda: state(store)) <= 15


def test_state_counts_rows_without_reading_whole_tables():
    store = seeded_store()

    assert state(store)["rows"]["trade_flows"] == len(store.read("trade_flows"))


def test_a_country_page_fetches_only_that_countrys_rows(shared_country_store):
    store = shared_country_store
    import sqlalchemy as sa

    statements = []
    listener = lambda conn, cur, stmt, *a: statements.append(stmt)
    sa.event.listen(store.engine, "before_cursor_execute", listener)
    try:
        country_state(store, "USA")
    finally:
        sa.event.remove(store.engine, "before_cursor_execute", listener)

    trade_reads = [s for s in statements if "FROM trade_flows" in s]
    assert len(statements) <= 6 and trade_reads and all("WHERE" in s for s in trade_reads)


@pytest.fixture(scope="module")
def last_week():
    return state(store_with_last_week())


@pytest.fixture(scope="module")
def shared_country_store():
    return country_store()


def save_month_change(store, moved=None, latest="2026-10", previous="2026-09"):
    """Record ranks on the previous month's 12-month window: today's ranks, except the `moved` countries."""
    current = store.latest_ranking()
    ranks = {c: {r["iso3"]: r["rank"] for r in current} for c in ("all", "1704", "1806", "1905", "2105")}
    ranks["all"].update(moved or {})
    window = lambda end: f"{int(end[:4]) - 1}-{int(end[5:]) % 12 + 1:02d} to {end}"
    store.save_ranking(
        "m",
        "all",
        "month_change",
        "default",
        {
            "latest": {"year": 2026, "through": latest, "window": window(latest)},
            "previous": {"year": 2026, "through": previous, "window": window(previous)},
            "ranks": ranks,
        },
    )


def store_with_last_week():
    store = country_store()  # USA exports, US tariffs incl. KORUS and the 15% reciprocal tariff
    world = [
        {
            "source": "kcs_monthly",
            "reporter_iso3": "KOR",
            "partner_iso3": "WLD",
            "flow": "X",
            "hs": "210500",
            "freq": "M",
            "period": p,
            "value_usd": v,
            "net_kg": 1.0,
            "imputed": False,
        }
        for p, v in (("202510", 8.0e7), ("202610", 1.0e8))
    ]
    run_sources([StaticSource("kcs_monthly", "trade_flows", world)], store, http=None)
    save_month_change(store, {"PHL": 5, "IND": 3})
    return store


def test_ranking_rows_carry_the_monthly_and_yearly_change(last_week):
    rows = {r["iso3"]: r for r in last_week["ranking"]["all"]}

    assert (rows["PHL"]["rank_change_month"], rows["IND"]["rank_change_month"], rows["USA"]["rank_change_month"]) == (
        2,
        -1,
        0,
    )
    assert all("rank_change_year" in r for r in rows.values())
    assert "rank_change" not in rows["USA"]  # no weekly comparison any more


def test_kpis_give_the_latest_exports_alerts_and_how_stable_the_top3_is(last_week):
    k = last_week["kpis"]

    assert k["exports"]["period"] == "202610" and k["exports"]["value_usd"] == 1.0e8
    assert k["exports"]["yoy"] == pytest.approx(0.25)
    assert k["alerts"] >= 1  # the Philippines entered the TOP3
    assert k["top3_robust"] == 2  # USA and China robust, the Philippines depends on priorities


def test_top3_cards_get_each_markets_latest_exports(last_week):
    usa = last_week["exports_by_country"]["USA"]

    assert (usa["period"], usa["value_usd"]) == ("202610", 4664249.0 + 12.0e6)


def test_next_steps_come_from_tariffs_and_caveats(last_week):
    steps = last_week["next_steps"]

    assert any("15% US reciprocal tariff" in s for s in steps["USA"])
    assert any("AKFTA" in s and "preferential rate" in s for s in steps["PHL"])
    assert any("depends on" in s for s in steps["PHL"])


def test_trends_and_forecasts_follow_the_selected_category(last_week):
    trends = last_week["trend"]

    assert set(trends) == {"all", "1704", "1806", "1905", "2105"}
    assert trends["2105"]["history"] != trends["all"]["history"]


def test_state_offers_the_scoring_presets():
    presets = state(seeded_store())["presets"]

    assert list(presets) == ["default", "scale", "growth"] and presets["scale"]["label"] == "Scale markets"


def test_yearly_change_compares_the_last_two_years_of_data():
    st = state(seeded_store())
    ranks_2024 = {r["iso3"]: r["rank"] for r in st["trend"]["all"]["history"] if r["year"] == 2024}

    rows = {r["iso3"]: r for r in st["ranking"]["all"]}
    assert st["change_basis"]["all"]["year"] == "2024 → 2025 data"
    assert rows["PHL"]["rank_change_year"] == ranks_2024["PHL"] - rows["PHL"]["rank"]


def test_without_monthly_data_there_is_no_monthly_change():
    st = state(seeded_store())

    assert st["change_basis"]["all"]["month"] is None
    assert all(r["rank_change_month"] is None for r in st["ranking"]["all"])


def test_monthly_change_compares_the_two_latest_12_month_windows(last_week):
    assert last_week["change_basis"]["all"]["month"] == "Sep → Oct 2026 data"
    assert last_week["provisional"]["through"] == "2026-10"


def test_destinations_say_which_are_re_export_hubs():
    t = trends_state(trends_store())

    assert all("hub" in d for d in t["destinations"])
