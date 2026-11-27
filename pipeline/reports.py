"""Automated weekly report: what changed in the ranking, the trade data and the pipeline, from the store alone.

    python -m pipeline.run --report        # scheduled weekly by .github/workflows/report-weekly.yml

Every sentence is assembled from stored numbers (no LLM), so each claim can be traced to its source.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pipeline.alerts import market_alerts
from pipeline.config import CANDIDATES, FTA_WITH_KOREA
from pipeline.db import Store
from pipeline.insights import trends_state

CATEGORY = {"1704": "Sugar confectionery", "1806": "Chocolate", "1905": "Bakery & biscuits", "2105": "Ice cream"}
COMMODITY = {"cocoa": "Cocoa", "sugar_world": "Sugar (world)", "wheat_us_hrw": "Wheat (US HRW)", "palm_oil": "Palm oil"}


def _name(iso: str) -> str:
    return CANDIDATES.get(iso, (None, iso))[1]


def _week(now: datetime) -> tuple[str, str]:
    year, week, weekday = now.isocalendar()
    start = (now - timedelta(days=weekday - 1)).date()
    end = start + timedelta(days=6)
    span = (
        f"{start.day}–{end.day} {end:%b}" if start.month == end.month else f"{start.day} {start:%b}–{end.day} {end:%b}"
    )
    return f"{year}-W{week:02d}", f"Week {week}, {year} ({span})"


def _month_label(month: dict) -> str:
    name = lambda ym: datetime.strptime(ym, "%Y-%m").strftime("%b")
    return f"{name(month['previous']['through'])} → {name(month['latest']['through'])} {month['latest']['through'][:4]}"


def _headline(top3: list[dict], movers: list[dict], month: dict | None, new_month: bool) -> str:
    names = ", ".join(c["name"] for c in top3)
    if not new_month:
        return f"No new monthly data this week. TOP3: {names}."
    label = _month_label(month)
    before = sorted(month["ranks"]["all"], key=month["ranks"]["all"].get)[:3]
    if before == [c["iso3"] for c in top3]:
        lead = f"New 관세청 month ({label}): TOP3 unchanged, {names}."
    else:
        entered = [c["name"] for c in top3 if c["iso3"] not in before]
        left = [_name(i) for i in before if i not in {c["iso3"] for c in top3}]
        lead = f"New 관세청 month ({label}): TOP3 is now {names}" + (
            f"; {', '.join(entered)} in, {', '.join(left)} out." if entered else " (order changed)."
        )
    big = [m for m in movers if abs(m["change"]) >= 2][:2]
    if big:
        lead += (
            " Biggest moves: "
            + "; ".join(
                f"{m['name']} {'up' if m['change'] > 0 else 'down'} {abs(m['change'])} to #{m['now']}" for m in big
            )
            + "."
        )
    return lead


def build_report(store: Store, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    week, title = _week(now)
    current = store.latest_ranking()
    # Rank changes are month on month, reported once: when a 관세청 month newer than the last report's arrives
    month = store.latest_ranking(variant="month_change")
    reported = [store.get_report(r["week"]) for r in store.list_reports() if r["week"] != week]
    last_month_reported = next((r.get("data_month") for r in reported if r and r.get("data_month")), None)
    new_month = bool(month) and month["latest"]["through"] != last_month_reported

    top3 = [
        {
            "iso3": c["iso3"],
            "name": c["reasons"]["name"],
            "rank": c["rank"],
            "score": c["score"],
            "headline": c["reasons"]["headline"],
            "confidence": c["reasons"]["confidence"]["level"],
        }
        for c in current[:3]
    ]
    movers = []
    if new_month:
        was = month["ranks"]["all"]
        movers = sorted(
            (
                {
                    "iso3": c["iso3"],
                    "name": c["reasons"]["name"],
                    "was": was[c["iso3"]],
                    "now": c["rank"],
                    "change": was[c["iso3"]] - c["rank"],
                }
                for c in current
                if c["iso3"] in was and was[c["iso3"]] != c["rank"]
            ),
            key=lambda m: -abs(m["change"]),
        )

    t = trends_state(store)
    exports = None
    if t["kfood_latest"]:
        p = t["kfood_latest"]["period"]
        by_cat = {}
        for cat, label in CATEGORY.items():
            vals = {r["period"]: r["value_usd"] for r in t["kfood_monthly"] if r["category"] == cat}
            prior = f"{int(p[:4]) - 1}{p[4:]}"
            if p in vals:
                by_cat[cat] = {
                    "name": label,
                    "value_usd": vals[p],
                    "yoy": vals[p] / vals[prior] - 1 if vals.get(prior) else None,
                }
        growing = sorted(
            (d for d in t["destinations"] if d["growth"] is not None and d["last12_usd"] >= 5e6),
            key=lambda d: -d["growth"],
        )[:3]
        exports = t["kfood_latest"] | {"by_category": by_cat, "fastest_destinations": growing}

    trend = t["score_trend"]
    forecast = None
    if trend:
        horizon = max(r["year"] for r in trend["forecast"])
        likely = sorted((r for r in trend["forecast"] if r["year"] == horizon), key=lambda r: -r["p_top3"])[:3]
        forecast = {
            "year": horizon,
            "top3": [{"name": r["name"], "p_top3": r["p_top3"]} for r in likely],
            "holdout": trend["holdout"],
        }

    runs = store.runs()
    week_runs = runs[runs.started_at >= (now - timedelta(days=7)).isoformat()] if len(runs) else runs
    missing_fta = sorted(_name(i) for i in FTA_WITH_KOREA if i not in _countries_with_pref(store))
    health = {
        "runs": len(week_runs),
        "failed": int((week_runs.status == "failed").sum()) if len(week_runs) else 0,
        "skipped": sorted(set(week_runs[week_runs.status == "skipped"].source)) if len(week_runs) else [],
        "rows_new": int(week_runs.rows_inserted.fillna(0).sum()) if len(week_runs) else 0,
        "rows_revised": int(week_runs.rows_updated.fillna(0).sum()) if len(week_runs) else 0,
        "fta_rates_missing": missing_fta,
    }

    return {
        "week": week,
        "title": title,
        "generated_at": now.isoformat(timespec="seconds"),
        "headline": _headline(top3, movers, month, new_month),
        "new_month": new_month,
        "data_month": month["latest"]["through"] if month else None,
        "month_label": _month_label(month) if month else None,
        "top3": top3,
        "movers": movers[:8],
        "exports": exports,
        "forecast": forecast,
        "prices": [{k: c[k] for k in ("commodity", "unit", "latest", "latest_month", "yoy")} for c in t["commodities"]],
        "health": health,
        "alerts": market_alerts(store, now=now),
    }


def _countries_with_pref(store: Store) -> set[str]:
    t = store.read("tariffs")
    return set(t[t.rate_type == "pref"].importer_iso3)


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v * 100:+.1f}%"


def _usd(v: float) -> str:
    return f"US${v / 1e6:,.1f}M" if v >= 1e6 else f"US${v:,.0f}"


def to_markdown(r: dict) -> str:
    """The report as Markdown, for download or posting to a channel."""
    lines = [
        f"# WellGTM weekly report: {r['title']}",
        "",
        f"**{r['headline']}**",
        "",
        f"_Generated automatically {r['generated_at']} from the WellGTM pipeline._",
        "",
        "## TOP3",
        "",
    ]
    lines += [
        f"{c['rank']}. **{c['name']}** (score {c['score']:.1f}, {c['confidence']}): {c['headline']}" for c in r["top3"]
    ]
    lines += ["", "## Rank changes", ""]
    if not r.get("new_month"):
        lines.append("- No new monthly data this week; 관세청 publishes the next month around the 15th.")
    elif r["movers"]:
        lines.append(f"Month on month, {r['month_label']} data:")
        lines += [f"- {m['name']}: #{m['was']} → #{m['now']} ({m['change']:+d})" for m in r["movers"]]
    else:
        lines.append(f"- No rank changes, {r['month_label']} data.")
    lines += ["", "## Exports", ""]
    if r["exports"]:
        e = r["exports"]
        lines.append(
            f"Korea's K-food exports in {e['period'][:4]}-{e['period'][4:]}: {_usd(e['value_usd'])} "
            f"({_pct(e['yoy'])} on a year earlier; 관세청)."
        )
        lines += [f"- {c['name']}: {_usd(c['value_usd'])} ({_pct(c['yoy'])})" for c in e["by_category"].values()]
        if e["fastest_destinations"]:
            lines.append(
                "- Fastest-growing destinations (12 months, ≥ US$5M): "
                + ", ".join(f"{d['name']} {_pct(d['growth'])}" for d in e["fastest_destinations"])
            )
    else:
        lines.append("No 관세청 monthly data loaded.")
    lines += ["", "## Forecast", ""]
    if r["forecast"]:
        f = r["forecast"]
        lines.append(
            f"Most likely TOP3 in {f['year']}: "
            + ", ".join(f"{c['name']} ({c['p_top3'] * 100:.0f}%)" for c in f["top3"])
            + "."
        )
        h = f["holdout"]
        lines.append(
            f"Accuracy check: forecasting {h['year']} from {h['trained_on']} predicted "
            f"{', '.join(h['predicted_top3'])}; actual {', '.join(h['actual_top3'])}."
        )
    else:
        lines.append("No forecast yet.")
    lines += ["", "## Alerts", ""]
    lines += [f"- **{a['name']}**: {a['text']}" for a in r.get("alerts", [])] or [
        "- No alerts for the top 10 markets this week."
    ]
    lines += ["", "## Ingredient prices", ""]
    lines += [
        f"- {COMMODITY.get(p['commodity'], p['commodity'])}: {p['latest']:.2f} {p['unit']} in "
        f"{p['latest_month']} ({_pct(p['yoy'])} on a year earlier)"
        for p in r["prices"]
    ] or ["- No price data."]
    h = r["health"]
    lines += [
        "",
        "## Data and pipeline",
        "",
        (
            f"- {h['runs']} runs this week, {h['failed']} failed; {h['rows_new']:,} new rows, "
            f"{h['rows_revised']:,} revised values."
        ),
    ]
    if h["skipped"]:
        lines.append(f"- Skipped: {', '.join(h['skipped'])}.")
    if h["fta_rates_missing"]:
        lines.append(
            f"- FTA preferential rates not yet entered for: {', '.join(h['fta_rates_missing'])} "
            "(applied tariffs shown as MFN)."
        )
    return "\n".join(lines) + "\n"
