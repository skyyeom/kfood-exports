"""Alerts for the current top markets: monthly rank moves, TOP3 changes, export swings and tariff revisions."""

from datetime import UTC, datetime

import pytest
from test_preview import months, save_month_change, seeded_store
from test_run import StaticSource

from pipeline.alerts import market_alerts
from pipeline.run import run_sources

NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)


@pytest.fixture
def store():
    s = seeded_store()
    save_month_change(s, {"PHL": 5, "IND": 3})  # last month's ranks
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
        for i, p in enumerate(months(start=(2024, 1)))  # inside the annual data: no provisional year
    ]
    run_sources([StaticSource("kcs_monthly", "trade_flows", flows)], s, http=None)
    return s


def by_country(alerts):
    out = {}
    for a in alerts:
        out.setdefault(a["iso3"], []).append(a)
    return out


def test_alerts_cover_the_current_top10_by_default(store):
    alerts = market_alerts(store, now=NOW)

    top10 = {r["iso3"] for r in store.latest_ranking()[:10]}
    assert {a["iso3"] for a in alerts} <= top10


def test_entering_the_top3_is_flagged(store):
    texts = [a["text"] for a in by_country(market_alerts(store, now=NOW))["PHL"]]

    assert "Entered the TOP3 (#5 → #3)." in texts


def test_leaving_the_top3_is_flagged(store):
    texts = [a["text"] for a in by_country(market_alerts(store, now=NOW))["IND"]]

    assert "Left the TOP3 (#3 → #4)." in texts


def test_a_large_change_in_monthly_exports_is_flagged(store):
    exports = [a for a in by_country(market_alerts(store, now=NOW))["PHL"] if a["kind"] == "exports"]

    assert len(exports) == 1 and "+50%" in exports[0]["text"]


def test_a_steady_market_has_no_alerts(store):
    assert "CHN" not in by_country(market_alerts(store, now=NOW))


def test_revised_tariffs_are_flagged(store):
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

    usa = by_country(market_alerts(store, now=datetime.now(UTC)))["USA"]

    assert any(a["kind"] == "tariff" and "15.0 → 10.0" in a["text"] for a in usa)
