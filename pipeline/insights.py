"""Current trends computed from the store, shared by the dashboard and the weekly report."""

from __future__ import annotations

import json

import pandas as pd

from pipeline.config import CANDIDATES, HUBS
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
                        "hub": iso in HUBS,
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


def next_steps(row: dict, alerts: list[dict], tariffs: pd.DataFrame, today: str) -> list[str]:
    """Up to three data-based things to check next for a ranked market (no invented advice).

    Built from the market's alerts, tariffs in force, FTA status and the reason pack's confidence and caveats.
    """
    from pipeline.config import FTA_WITH_KOREA

    iso, reasons = row["iso3"], row.get("reasons", {})
    steps = []
    for a in alerts:
        if a["kind"] == "exports":
            up = "+" in a["text"]
            steps.append(
                f"{a['text'].rstrip('.')}: {'check distributor and supply capacity' if up else 'review distributor performance and pricing'}."
            )
    t = tariffs[
        (tariffs.importer_iso3 == iso)
        & (tariffs.effective_from <= today)
        & (tariffs.effective_to.isna() | (tariffs.effective_to > today))
    ]
    for extra in t[t.rate_type == "additional"].drop_duplicates("agreement").itertuples():
        steps.append(f"Price in the {extra.rate_pct:g}% {extra.agreement}.")
    if iso in FTA_WITH_KOREA and t[t.rate_type == "pref"].empty:
        steps.append(f"Confirm the {FTA_WITH_KOREA[iso]} preferential rate: the applied tariff shown is MFN.")
    level = reasons.get("confidence", {}).get("level")
    if level == "depends on priorities":
        steps.append("This pick depends on your priorities: compare it under the Scale and Growth presets.")
    elif level == "fragile":
        steps.append("This pick is fragile: small weight changes drop it out of the TOP3.")
    for caveat in reasons.get("caveats", []):
        if "reports imports from Korea" in caveat:
            steps.append("Check partner-side import data: it differs a lot from Korea's export figures.")
        elif "produces locally" in caveat:
            steps.append("Weigh local production against exports from Korea for this market.")
    return steps[:3]
