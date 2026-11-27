"""Local preview of the Automation & Data Health page and the TOP3, served from the pipeline's database.

    python -m pipeline.preview            # http://localhost:8765

A development preview until the M3 frontend exists. "Run now" runs a source in this process, so runs appear in
the feed live. Reads DATABASE_URL (default sqlite:///data/local.db).
"""

from __future__ import annotations

import hmac
import json
import os
import sys
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd

from pipeline.auth import LoginThrottle, Sessions, verify_password
from pipeline.config import CANDIDATES, FTA_WITH_KOREA, HS
from pipeline.db import Store
from pipeline.http import Http
from pipeline.indicators import CATEGORIES
from pipeline.insights import records as _records
from pipeline.insights import trends_state
from pipeline.raw import LocalRawStore
from pipeline.run import run_sources
from pipeline.sources import SOURCES

PAGE = Path(__file__).with_name("preview.html")
LOGIN_PAGE = Path(__file__).with_name("login.html")
COOKIE = "wellgtm_session"

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
        "trend": store.latest_ranking(variant="trend") or None,
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
    username: str
    password_hash: str
    sessions: Sessions
    throttle: LoginThrottle

    # ---- sign-in gate: only /login is public; every other page and API call needs a session ----
    def _token(self) -> str | None:
        for part in (self.headers.get("Cookie") or "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == COOKIE:
                return value
        return None

    def _user(self) -> str | None:
        return self.sessions.user(self._token())

    def _refuse(self, path: str) -> None:
        if path.startswith("/api/"):
            return self._send(401, b'{"error": "not signed in"}')
        self.send_response(303)
        self.send_header("Location", "/login")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _read_body(self) -> dict:
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()
        if "json" in (self.headers.get("Content-Type") or ""):
            try:
                return json.loads(raw or "{}")
            except json.JSONDecodeError:
                return {}
        return {k: v[0] for k, v in parse_qs(raw).items()}

    def _login(self) -> None:
        address = self.client_address[0]
        body = self._read_body()  # read before any reply: an unread request body can reset the connection
        if self.throttle.locked(address):
            return self._send(429, b'{"error": "Too many failed attempts. Wait a minute and try again."}')
        user, password = str(body.get("username", "")), str(body.get("password", ""))
        name_ok = hmac.compare_digest(user.encode(), self.username.encode())
        if not (verify_password(password, self.password_hash) and name_ok):
            self.throttle.failed(address)
            return self._send(401, b'{"error": "Wrong username or password."}')
        self.throttle.succeeded(address)
        token = self.sessions.create(user)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Set-Cookie", f"{COOKIE}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={self.sessions.ttl}"
        )
        self.end_headers()
        self.wfile.write(json.dumps({"user": user}).encode())

    def _logout(self) -> None:
        self.sessions.end(self._token())
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Set-Cookie", f"{COOKIE}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/login":
            return self._send(200, LOGIN_PAGE.read_bytes(), "text/html; charset=utf-8")
        user = self._user()
        if not user:
            return self._refuse(path)
        if path == "/api/me":
            return self._send(200, json.dumps({"user": user}).encode())
        self._get(path)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/login":
            return self._login()
        if not self._user():
            return self._refuse(path)
        if path == "/logout":
            return self._logout()
        self._post()

    def _send(self, code: int, body: bytes, kind: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _get(self, path: str) -> None:
        if path == "/":
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path.startswith("/api/country/"):
            try:
                body = country_state(self.store, path.rsplit("/", 1)[-1].upper())
            except KeyError:
                return self._send(404, b'{"error": "unknown country"}')
            self._send(200, json.dumps(body, default=str).encode())
        elif path == "/api/bi.zip":
            import io
            import tempfile
            import zipfile

            from pipeline.bi import export_csv

            with tempfile.TemporaryDirectory() as tmp:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                    for csv_path in export_csv(self.store, tmp):
                        z.write(csv_path, csv_path.name)
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="wellgtm-bi-data.zip"')
            self.end_headers()
            self.wfile.write(buf.getvalue())
        elif path == "/api/reports":
            self._send(200, json.dumps(self.store.list_reports()).encode())
        elif path.startswith("/api/reports/"):
            week = path.rsplit("/", 1)[-1]
            as_md = week.endswith(".md")
            body = self.store.get_report(week.removesuffix(".md"), markdown=as_md)
            if body is None:
                return self._send(404, b'{"error": "no such report"}')
            if as_md:
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="wellgtm-report-{week}"')
                self.end_headers()
                return self.wfile.write(body.encode())
            self._send(200, json.dumps(body, default=str).encode())
        elif path == "/api/trends":
            self._send(200, json.dumps(trends_state(self.store), default=str).encode())
        elif path == "/api/state":
            self._send(200, json.dumps(state(self.store) | {"running": sorted(self.running)}, default=str).encode())
        else:
            self._send(404, b'{"error": "not found"}')

    def _post(self) -> None:
        url = urlparse(self.path)
        if url.path == "/api/report":
            return self._send(201, json.dumps(self._report(), default=str).encode())
        source = (parse_qs(url.query).get("source") or [""])[0]
        if url.path != "/api/run" or source not in SOURCES:
            return self._send(400, b'{"error": "unknown source"}')
        with self.lock:
            if source in self.running:
                return self._send(409, b'{"error": "already running"}')
            self.running.add(source)
        threading.Thread(target=self._run, args=(source,), daemon=True).start()
        self._send(202, json.dumps({"started": source}).encode())

    def _report(self) -> dict:
        from pipeline.run import _weekly_report

        _weekly_report(self.store, "manual", None)
        latest = self.store.list_reports()
        return latest[0] if latest else {}

    def _run(self, source: str) -> None:
        try:
            run_sources([SOURCES[source]()], self.store, Http(), trigger="manual", raw_store=LocalRawStore("data"))
        finally:
            with self.lock:
                self.running.discard(source)

    def log_message(self, *args):  # keep the terminal quiet
        pass


def make_server(store: Store, port: int, username: str, password_hash: str) -> ThreadingHTTPServer:
    handler = type(
        "Handler",
        (_Handler,),
        {
            "store": store,
            "running": set(),
            "username": username,
            "password_hash": password_hash,
            "sessions": Sessions(),
            "throttle": LoginThrottle(),
        },
    )
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main(port: int = 8765, env=None) -> int:
    env = os.environ if env is None else env
    username, password_hash = env.get("DASHBOARD_USERNAME"), env.get("DASHBOARD_PASSWORD_HASH")
    if not (username and password_hash):
        print(
            "No dashboard login is set. Create one with:\n\n    .venv/bin/python -m pipeline.auth set\n\n"
            "then load .env (set -a; . ./.env; set +a) and start the dashboard again."
        )
        return 2
    url = env.get("DATABASE_URL", "sqlite:///data/local.db")
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    store = Store(url)
    if url.startswith("sqlite"):
        store.create_all()
    server = make_server(store, port, username, password_hash)
    print(
        f"WellGTM dashboard on http://localhost:{server.server_address[1]}  (database: {url.split('@')[-1]}; "
        f"sign in as {username})"
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 8765))
