"""Smoke-test the dashboard page script: render the Overview and trend chart from real state data in Node,
with a minimal DOM stand-in, for every category, preset, chart mode and custom weights. Catches runtime errors
(e.g. reading a field the state doesn't have) that a syntax check cannot."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from test_preview import store_with_last_week

from pipeline.preview import state

PAGE = Path(__file__).resolve().parents[1] / "pipeline"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node")

HARNESS = r"""
const vm = require("vm"), fs = require("fs");
const st = JSON.parse(fs.readFileSync(0, "utf8"));
const els = {};
const el = id => els[id] ??= { id, innerHTML: "", textContent: "", hidden: false, dataset: {}, style: {},
  setAttribute() {}, removeAttribute() {}, getAttribute() { return null; }, addEventListener() {},
  querySelector() { return el("q"); }, querySelectorAll() { return []; }, closest() { return el("c"); },
  appendChild() {}, after() {}, focus() {}, getBoundingClientRect() { return { left: 0, bottom: 0 }; },
  createSVGPoint() { return { matrixTransform: () => ({ x: 0 }) }; }, getScreenCTM() { return { inverse() {} }; } };
const document = { getElementById: el, querySelector: () => el("q"), querySelectorAll: () => [], addEventListener() {}, title: "" };
const ctx = { console, document, st, process, location: { hash: "#/overview", replace() {} }, innerWidth: 1200, innerHeight: 800,
  setInterval() {}, addEventListener() {}, fetch: () => new Promise(() => {}), Date, Math, JSON, Number, String,
  Object, Array, Set, Map, Promise, Error };
ctx.window = ctx; ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2], "utf8"), ctx);  // argv: node, harness, score.js, page script
vm.runInContext(process.argv[3], ctx);
vm.runInContext(`
  const out = {};
  for (const c of Object.keys(CATEGORIES)) {
    category = c;
    for (const p of Object.keys(st.presets)) {
      preset = p; weights = null;
      renderOverview(st);
      out[c + "/" + p] = { names: document.getElementById("answer-names").textContent,
                           cards: (document.getElementById("top3").innerHTML.match(/<article/g) || []).length };
    }
    for (const m of ["rank", "score"]) { trendMode = m; renderTrend(st, true); }
  }
  category = "all"; preset = "default"; weights = null;
  changeView = "month"; renderOverview(st); out.monthTable = document.getElementById("ranking").innerHTML;
  out.compare = document.getElementById("compare").innerHTML;
  changeView = "year"; renderOverview(st); out.yearTable = document.getElementById("ranking").innerHTML;
  changeView = null; renderOverview(st);
  weights = { "Market growth": 1, "Market size": 0, "K-momentum (trade)": 0, "Entry ease": 0 };
  renderOverview(st);
  out.custom = { summary: document.getElementById("ctrl-summary").textContent,
                 table: document.getElementById("ranking").innerHTML };
  out.kpis = document.getElementById("ov-kpis").innerHTML;
  category = "all"; trendMode = "rank"; renderTrend(st, true);
  out.trend = document.getElementById("trend-chart").innerHTML.slice(0, 200);
  process.stdout.write(JSON.stringify(out));
`, ctx);
"""


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    html = (PAGE / "preview.html").read_text()
    script = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)[-1]
    # the page's start-up lines fetch from the server; the harness calls the render functions itself
    script = script.split('fetch("/api/me")')[0]
    path = tmp_path_factory.mktemp("js") / "harness.js"
    path.write_text(HARNESS)
    st = state(store_with_last_week()) | {"running": []}
    out = subprocess.run(
        ["node", str(path), str(PAGE / "score.js"), script],
        input=json.dumps(st, default=str),
        capture_output=True,
        text=True,
        check=False,  # a failure is reported below with Node's stderr
    )
    assert out.returncode == 0, out.stderr[-2000:]
    return json.loads(out.stdout)


def test_overview_renders_three_top3_cards_for_every_category_and_preset(rendered):
    for key, view in rendered.items():
        if "/" in key:
            assert view["cards"] == 3 and view["names"].count("·") == 2, key


def test_the_answer_names_the_current_top3(rendered):
    assert rendered["all/default"]["names"] == "United States · China · Philippines"


def test_custom_weights_re_rank_and_say_so(rendered):
    assert "your own weights" in rendered["custom"]["summary"] and "market growth 100%" in rendered["custom"]["summary"]
    assert "vs default" in rendered["custom"]["table"]


def test_kpi_row_shows_exports_stability_alerts_and_data(rendered):
    for label in ("K-food exports, latest month", "TOP3 stability", "Alerts this week", "Data"):
        assert label in rendered["kpis"]


def test_trend_chart_renders_in_rank_mode(rendered):
    assert rendered["trend"].startswith("<svg") and "ranks" in rendered["trend"]


def test_change_column_follows_the_month_or_year_toggle(rendered):
    assert "Change (Sep → Oct 2026 data)" in rendered["monthTable"]
    assert "Change (2024 → 2025 data" in rendered["yearTable"]
    assert 'data-compare="month"' in rendered["compare"] and 'data-compare="year"' in rendered["compare"]


def test_rank_changes_are_coloured_by_direction(rendered):
    assert 'class="chg up"' in rendered["monthTable"] and 'class="chg down"' in rendered["monthTable"]
