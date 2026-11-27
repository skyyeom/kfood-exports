"""The browser re-ranks with pipeline/score.js; it must agree with the Python screen (run with Node)."""

import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest
from analysis_data import load_tables

from pipeline.indicators import PRESETS, build_features, screen

SCORE_JS = Path(__file__).resolve().parents[1] / "pipeline" / "score.js"
PILLARS = ["Market growth", "Market size", "K-momentum (trade)", "Entry ease"]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node")


def run_js(rows, weights, draws=5000):
    script = (
        f"const s = require({json.dumps(str(SCORE_JS))});"
        "const {rows, weights, draws} = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "process.stdout.write(JSON.stringify(s.rerank(rows, weights, draws)));"
    )
    out = subprocess.run(
        ["node", "-e", script],
        input=json.dumps({"rows": rows, "weights": weights, "draws": draws}),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)


@pytest.fixture(scope="module")
def rows():
    ranked = screen(build_features(*load_tables()))
    return [{"iso3": iso, **{p: float(ranked.at[iso, p]) for p in PILLARS}} for iso in ranked.index]


@pytest.mark.parametrize("preset", ["default", "scale", "growth"])
def test_browser_scores_and_ranks_match_python(rows, preset):
    weights = PRESETS[preset]["weights"]
    python = screen(build_features(*load_tables()), weights=pd.Series(weights), draws=5000)

    js = run_js(rows, weights)

    assert [r["iso3"] for r in js] == list(python.index)
    for r in js:
        assert r["score"] == pytest.approx(python.at[r["iso3"], "score"], abs=1e-9)
        assert r["rank"] == list(python.index).index(r["iso3"]) + 1


def test_browser_top3_probability_matches_python_within_monte_carlo_noise(rows):
    python = screen(build_features(*load_tables()), draws=5000)

    js = {r["iso3"]: r["p_top3"] for r in run_js(rows, PRESETS["default"]["weights"])}

    assert max(abs(js[i] - python.at[i, "top3_probability"]) for i in js) <= 0.03


def test_browser_normalises_slider_weights_that_do_not_sum_to_one(rows):
    doubled = {k: v * 2 for k, v in PRESETS["default"]["weights"].items()}

    assert [r["iso3"] for r in run_js(rows, doubled)] == [
        r["iso3"] for r in run_js(rows, PRESETS["default"]["weights"])
    ]
