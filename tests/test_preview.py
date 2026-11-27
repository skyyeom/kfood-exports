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


def test_country_page_has_the_name_rank_and_reasons():
    c = country_state(country_store(), "USA")

    assert (c["name"], c["ranking"]["all"]["rank"]) == ("United States", 1)
    assert c["ranking"]["all"]["reasons"]["confidence"]["level"] == "robust"


def test_country_page_shows_monthly_korean_exports_by_category():
    months = {(m["category"], m["period"]): m["value_usd"] for m in country_state(country_store(), "USA")["monthly"]}

    assert months[("2105", "202610")] == 4664249.0
    assert months[("1905", "202610")] == 12.0e6  # HS6 lines 190531 + 190590 summed into the heading


def test_country_page_shows_foods_share_of_koreas_exports():
    share = country_state(country_store(), "USA")["food_share"]

    assert share["period"] == "202610"
    assert share["share"] == (4664249.0 + 12.0e6) / 10.0e9


def test_country_page_applies_the_tariff_rule_mfn_or_fta_plus_additional_duties():
    [sugar] = [t for t in country_state(country_store(), "USA")["tariffs"] if t["hs"] == "1704"]

    # min(MFN average 6%, KORUS 0%) + 15% reciprocal = 15%
    assert (sugar["mfn_pct"], sugar["preferential_pct"], sugar["additional_pct"], sugar["applied_pct"]) == (
        6.0,
        0.0,
        15.0,
        15.0,
    )


def test_unknown_country_is_rejected():
    import pytest

    with pytest.raises(KeyError):
        country_state(country_store(), "XXX")


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
    trend = state(seeded_store())["trend"]

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
