"""Tracker: watched markets, their changes since last week, and alerts."""

from datetime import UTC, datetime

import pytest
from test_preview import months, seeded_store
from test_run import StaticSource

from pipeline.run import run_sources
from pipeline.tracker import tracker_state

NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)


@pytest.fixture
def store():
    s = seeded_store()
    current = s.latest_ranking()
    earlier = [dict(c, rank={"PHL": 5, "IND": 3}.get(c["iso3"], c["rank"])) for c in current]
    s.save_ranking("old-run", "all", "corrected", "default", earlier, computed_at="2026-11-17T00:00:00.000+00:00")
    flows = [
        {
            "source": "kcs_monthly",
            "reporter_iso3": "KOR",
            "partner_iso3": iso,
            "flow": "X",
            "hs": "190590",
            "freq": "M",
            "period": p,
            "value_usd": v * (1.5 if i >= 12 else 1.0),
            "net_kg": 1.0,
            "imputed": False,
        }
        for iso, v in (("PHL", 1.0e6), ("USA", 1.0e7))
        for i, p in enumerate(months())
    ]
    run_sources([StaticSource("kcs_monthly", "trade_flows", flows)], s, http=None)
    return s


def test_watchlist_can_add_and_remove_markets(store):
    store.watch("PHL")
    store.watch("USA")
    store.unwatch("USA")

    assert store.watched() == ["PHL"]


def test_tracked_market_shows_rank_change_since_a_week_earlier(store):
    store.watch("PHL")

    [phl] = tracker_state(store, now=NOW)["markets"]

    assert (phl["name"], phl["rank"], phl["rank_week_ago"], phl["rank_change"]) == ("Philippines", 3, 5, 2)


def test_alerts_flag_entering_the_top3_and_big_rank_moves(store):
    store.watch("PHL")

    alerts = [a["text"] for a in tracker_state(store, now=NOW)["markets"][0]["alerts"]]

    assert "Entered the TOP3 (#5 → #3)." in alerts


def test_alerts_flag_a_large_change_in_monthly_exports(store):
    store.watch("PHL")

    phl = tracker_state(store, now=NOW)["markets"][0]

    assert phl["exports"]["period"] == "202610" and phl["exports"]["yoy"] == pytest.approx(0.5)
    assert any(a["kind"] == "exports" and "+50%" in a["text"] for a in phl["alerts"])


def test_a_steady_market_has_no_alerts(store):
    store.watch("CHN")

    assert tracker_state(store, now=NOW)["markets"][0]["alerts"] == []


def test_alerts_flag_revised_tariffs_for_a_tracked_market(store):
    store.watch("USA")
    tariff = {
        "source": "override",
        "importer_iso3": "USA",
        "hs": "1704",
        "rate_type": "additional",
        "agreement": "US reciprocal tariff",
        "effective_from": "2025-08-07",
        "source_url": "u",
    }
    run_sources([StaticSource("tariffs", "tariffs", [tariff | {"rate_pct": 15.0}])], store, http=None)
    run_sources([StaticSource("tariffs", "tariffs", [tariff | {"rate_pct": 10.0}])], store, http=None)

    usa = tracker_state(store, now=datetime.now(UTC))["markets"][0]

    assert any(a["kind"] == "tariff" and "15.0 → 10.0" in a["text"] for a in usa["alerts"])


def test_unknown_country_cannot_be_watched(store):
    with pytest.raises(KeyError):
        store.watch("XXX")
