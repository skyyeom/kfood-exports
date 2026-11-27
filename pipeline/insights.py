"""Current trends computed from the store, shared by the dashboard and the weekly report."""

from __future__ import annotations

import json

import pandas as pd

from pipeline.config import CANDIDATES
from pipeline.db import Store


def records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records"))


_records = records


def trends_state(store: Store) -> dict:
    """Current trends: Korea's monthly K-food exports, fastest-growing destinations, commodity prices, score trend."""
    kcs = store.read("trade_flows", source="kcs_monthly", flow="X")
    world = kcs[kcs.partner_iso3 == "WLD"].assign(category=lambda d: d.hs.str[:4])
    monthly = world.groupby(["category", "period"], as_index=False).value_usd.sum().sort_values("period")
    periods = sorted(monthly.period.unique())
    monthly = monthly[monthly.period.isin(periods[-36:])]

    latest = None
    if periods:
        totals = world.groupby("period").value_usd.sum()
        p = periods[-1]
        prior = f"{int(p[:4]) - 1}{p[4:]}"
        latest = {
            "period": p,
            "value_usd": float(totals[p]),
            "yoy": float(totals[p] / totals[prior] - 1) if prior in totals.index and totals[prior] else None,
        }

    destinations = []
    if len(periods) >= 24:
        last12, prev12 = set(periods[-12:]), set(periods[-24:-12])
        dest = kcs[kcs.partner_iso3 != "WLD"]
        a = dest[dest.period.isin(last12)].groupby("partner_iso3").value_usd.sum()
        b = dest[dest.period.isin(prev12)].groupby("partner_iso3").value_usd.sum()
        for iso in a.index:
            if iso in CANDIDATES:
                destinations.append(
                    {
                        "iso3": iso,
                        "name": CANDIDATES[iso][1],
                        "last12_usd": float(a[iso]),
                        "prev12_usd": float(b.get(iso, 0.0)),
                        "growth": float(a[iso] / b[iso] - 1) if b.get(iso) else None,
                    }
                )
        destinations.sort(key=lambda d: -d["last12_usd"])

    prices = store.read("commodity_prices").sort_values("month")
    commodities = []
    for name, g in prices.groupby("commodity"):
        g = g.tail(36)
        last, year_ago = g.iloc[-1], g[g.month == f"{int(g.month.iloc[-1][:4]) - 1}{g.month.iloc[-1][4:]}"]
        commodities.append(
            {
                "commodity": name,
                "unit": last.unit,
                "latest_month": last.month,
                "latest": float(last.price),
                "yoy": float(last.price / year_ago.price.iloc[0] - 1) if len(year_ago) else None,
                "series": _records(g[["month", "price"]]),
            }
        )

    return {
        "kfood_monthly": _records(monthly),
        "kfood_latest": latest,
        "destinations": destinations,
        "commodities": commodities,
        "score_trend": store.latest_ranking(variant="trend") or None,
    }
