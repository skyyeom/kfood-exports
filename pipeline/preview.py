"""Local preview of the Automation & Data Health page and the TOP3, served from the pipeline's database.

    python -m pipeline.preview            # http://localhost:8765

A development preview until the M3 frontend exists. "Run now" runs a source in this process, so runs appear in
the feed live. Reads DATABASE_URL (default sqlite:///data/local.db).
"""

from __future__ import annotations

import json
import os
import sys
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd

from pipeline.config import CANDIDATES, FTA_WITH_KOREA, HS
from pipeline.db import Store
from pipeline.http import Http
from pipeline.indicators import CATEGORIES
from pipeline.raw import LocalRawStore
from pipeline.run import run_sources
from pipeline.sources import SOURCES

PAGE = Path(__file__).with_name("preview.html")

# Mirrors the cron lines in .github/workflows/ingest-*.yml (UTC): (weekday or None, day of month or None, hour)
SCHEDULES = {
    "fx": (None, None, 17),
    "comtrade": (0, None, 18),
    "wdi": (0, None, 18),
    "tariffs": (0, None, 18),
    "kcs_monthly": (None, 16, 19),
    "kcs_items": (None, 16, 19),
    "kcs_nations": (None, 16, 19),
    "pinksheet": (None, 5, 19),
}


def next_run(source: str, now: datetime | None = None) -> str | None:
    if source not in SCHEDULES:
        return None
    weekday, day, hour = SCHEDULES[source]
    t = (now or datetime.now(UTC)).replace(minute=0, second=0, microsecond=0)
    t = t.replace(hour=hour) if t.hour < hour else (t + timedelta(days=1)).replace(hour=hour)
    while (weekday is not None and t.weekday() != weekday) or (day is not None and t.day != day):
        t += timedelta(days=1)
    return t.isoformat()


def _records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records"))


def state(store: Store) -> dict:
    """Everything the preview page shows, as plain JSON."""
    runs = store.runs().sort_values("started_at", ascending=False)
    sources = []
    for name in sorted(SOURCES):
        mine = runs[runs.source == name]
        ok = mine[mine.status == "success"]
        sources.append(
            {
                "source": name,
                "status": mine.status.iloc[0] if len(mine) else "never run",
                "last_run": mine.started_at.iloc[0] if len(mine) else None,
                "last_success": ok.finished_at.iloc[0] if len(ok) else None,
                "message": mine.error.iloc[0] if len(mine) and isinstance(mine.error.iloc[0], str) else None,
                "next_run": next_run(name),
            }
        )
    recent = runs.head(15)
    feed = []
    for run in _records(recent):
        run["events"] = _records(store.events(run["run_id"])[["step", "status", "ts", "message", "metrics"]])
        feed.append(run)
    revisions = (
        pd.concat([store.revisions(r) for r in runs.run_id.head(30)], ignore_index=True)
        if len(runs)
        else pd.DataFrame()
    )
    revisions = revisions.sort_values("id", ascending=False).head(25) if len(revisions) else revisions
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sources": sources,
        "runs": feed,
        "revisions": _records(revisions),
        "ranking": {c: store.latest_ranking(category=c) for c in ("all", "1704", "1806", "1905", "2105")},
        "rows": {
            t: len(store.read(t))
            for t in ("trade_flows", "country_indicators", "tariffs", "fx_rates", "commodity_prices")
        },
    }


def _applied_tariffs(tariffs: pd.DataFrame, iso: str, today: str) -> list[dict]:
    """Per HS4: applied = min(MFN, preferential rate in force) + additional duties in force (data dictionary)."""
    t = tariffs[tariffs.importer_iso3 == iso]
    in_force = t[(t.effective_from <= today) & (t.effective_to.isna() | (t.effective_to > today))]
    out = []
    for heading in HS:
        lines = in_force[in_force.hs.str.startswith(heading)]
        mfn = lines[lines.rate_type == "mfn"].rate_pct
        pref = lines[lines.rate_type == "pref"]
        extra = lines[lines.rate_type == "additional"]
        mfn_pct = round(float(mfn.mean()), 2) if len(mfn) else None
        pref_pct = float(pref.rate_pct.min()) if len(pref) else None
        base = min(x for x in (mfn_pct, pref_pct) if x is not None) if (mfn_pct, pref_pct) != (None, None) else None
        out.append(
            {
                "hs": heading,
                "mfn_pct": mfn_pct,
                "mfn_lines": len(mfn),
                "preferential_pct": pref_pct,
                "agreement": ", ".join(sorted(set(pref.agreement))) or None,
                "additional_pct": float(extra.rate_pct.sum()) if len(extra) else 0.0,
                "additional": ", ".join(sorted(set(extra.agreement))) or None,
                "applied_pct": None if base is None else base + float(extra.rate_pct.sum()),
                "sources": sorted(set(lines.source_url.dropna())),
                "fta_with_korea": FTA_WITH_KOREA.get(iso),
                "fta_rate_missing": iso in FTA_WITH_KOREA and pref_pct is None,
            }
        )
    return out


def country_state(store: Store, iso: str) -> dict:
    """Everything the country page shows for one candidate market."""
    if iso not in CANDIDATES:
        raise KeyError(iso)
    ranking = {}
    for category in CATEGORIES:
        rows = store.latest_ranking(category=category)
        row = next((r for r in rows if r["iso3"] == iso), None)
        ranking[category] = row | {"of": len(rows)} if row else None

    trade = store.read("trade_flows")
    mine = trade[(trade.partner_iso3 == iso) & (trade.flow == "X") & (trade.freq == "M")]
    food = mine[mine.source == "kcs_monthly"].assign(category=lambda d: d.hs.str[:4])
    monthly = food.groupby(["category", "period"], as_index=False).value_usd.sum().sort_values("period")
    recent = sorted(monthly.period.unique())[-36:]
    monthly = monthly[monthly.period.isin(recent)]

    totals = mine[mine.source == "kcs_nations"].set_index("period").value_usd
    food_by_month = food.groupby("period").value_usd.sum()
    common = sorted(set(totals.index) & set(food_by_month.index))
    share = None
    if common:
        last = common[-1]
        share = {
            "period": last,
            "food_usd": float(food_by_month[last]),
            "total_usd": float(totals[last]),
            "share": float(food_by_month[last] / totals[last]),
        }

    return {
        "iso3": iso,
        "name": CANDIDATES[iso][1],
        "ranking": ranking,
        "monthly": _records(monthly),
        "food_share": share,
        "tariffs": _applied_tariffs(store.read("tariffs"), iso, datetime.now(UTC).date().isoformat()),
    }


class _Handler(BaseHTTPRequestHandler):
    store: Store
    running: set[str]
    lock = threading.Lock()

    def _send(self, code: int, body: bytes, kind: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path.startswith("/api/country/"):
            try:
                body = country_state(self.store, path.rsplit("/", 1)[-1].upper())
            except KeyError:
                return self._send(404, b'{"error": "unknown country"}')
            self._send(200, json.dumps(body, default=str).encode())
        elif path == "/api/state":
            self._send(200, json.dumps(state(self.store) | {"running": sorted(self.running)}, default=str).encode())
        else:
            self._send(404, b'{"error": "not found"}')

    def do_POST(self):
        url = urlparse(self.path)
        source = (parse_qs(url.query).get("source") or [""])[0]
        if url.path != "/api/run" or source not in SOURCES:
            return self._send(400, b'{"error": "unknown source"}')
        with self.lock:
            if source in self.running:
                return self._send(409, b'{"error": "already running"}')
            self.running.add(source)
        threading.Thread(target=self._run, args=(source,), daemon=True).start()
        self._send(202, json.dumps({"started": source}).encode())

    def _run(self, source: str) -> None:
        try:
            run_sources([SOURCES[source]()], self.store, Http(), trigger="manual", raw_store=LocalRawStore("data"))
        finally:
            with self.lock:
                self.running.discard(source)

    def log_message(self, *args):  # keep the terminal quiet
        pass


def main(port: int = 8765) -> None:
    url = os.environ.get("DATABASE_URL", "sqlite:///data/local.db")
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    store = Store(url)
    if url.startswith("sqlite"):
        store.create_all()
    handler = type("Handler", (_Handler,), {"store": store, "running": set()})
    print(f"WellGTM preview on http://localhost:{port}  (database: {url.split('@')[-1]})")
    ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
