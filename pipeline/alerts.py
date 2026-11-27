"""Alerts worth acting on for the top markets: rank moves, TOP3 changes, export swings, tariff revisions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pipeline.config import CANDIDATES
from pipeline.db import Store

RANK_MOVE = 2  # places, week on week
EXPORT_SWING = 0.3  # |year-on-year change| in the latest month of 관세청 exports


def _rank_alert(was: int | None, now: int | None) -> dict | None:
    if was is None or now is None or was == now:
        return None
    if was > 3 >= now:
        return {"kind": "rank", "text": f"Entered the TOP3 (#{was} → #{now})."}
    if now > 3 >= was:
        return {"kind": "rank", "text": f"Left the TOP3 (#{was} → #{now})."}
    if abs(was - now) >= RANK_MOVE:
        return {"kind": "rank", "text": f"{'Up' if now < was else 'Down'} {abs(was - now)} places (#{was} → #{now})."}
    return None


def _exports(trade, iso: str) -> dict | None:
    mine = trade[(trade.source == "kcs_monthly") & (trade.partner_iso3 == iso) & (trade.flow == "X")]
    if mine.empty:
        return None
    totals = mine.groupby("period").value_usd.sum()
    p = totals.index.max()
    prior = f"{int(p[:4]) - 1}{p[4:]}"
    return {
        "period": p,
        "value_usd": float(totals[p]),
        "yoy": float(totals[p] / totals[prior] - 1) if totals.get(prior) else None,
        "last12_usd": float(totals.sort_index().tail(12).sum()),
    }


def market_alerts(
    store: Store, now: datetime | None = None, isos: list[str] | None = None, top: int = 10
) -> list[dict]:
    """Alerts for the given markets (default: the current top 10), comparing with the ranking a week earlier."""
    now = now or datetime.now(UTC)
    week_ago = (now - timedelta(days=7)).isoformat(timespec="milliseconds")
    current = store.latest_ranking()
    rank = {r["iso3"]: r["rank"] for r in current}
    previous = {r["iso3"]: r["rank"] for r in (store.ranking_before(week_ago) or [])}
    isos = isos or [r["iso3"] for r in current[:top]]
    trade = store.read("trade_flows")
    tariff_revisions = store.revisions_since(week_ago, "tariffs")

    alerts = []
    for iso in isos:
        found = [a for a in [_rank_alert(previous.get(iso), rank.get(iso))] if a]
        exports = _exports(trade, iso)
        if exports and exports["yoy"] is not None and abs(exports["yoy"]) >= EXPORT_SWING:
            found.append(
                {
                    "kind": "exports",
                    "text": f"Korean exports {exports['yoy'] * 100:+.0f}% on a year earlier "
                    f"in {exports['period'][:4]}-{exports['period'][4:]} (관세청).",
                }
            )
        for rev in tariff_revisions.itertuples():
            key = rev.row_key
            if key.get("importer_iso3") == iso:
                found.append(
                    {
                        "kind": "tariff",
                        "text": f"Tariff revised: HS {key['hs']} {key['rate_type']} "
                        f"{float(rev.old_value):.1f} → {float(rev.new_value):.1f}%.",
                    }
                )
        alerts += [a | {"iso3": iso, "name": CANDIDATES[iso][1]} for a in found]
    return alerts
