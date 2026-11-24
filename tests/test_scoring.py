"""The pipeline's scoring must reproduce the exploratory screen in docs/pm/03_data_analysis.md §3."""

from pathlib import Path

import pandas as pd
import pytest

from pipeline.indicators import build_features, screen

ANALYSIS = Path(__file__).resolve().parents[1] / "analysis"
PILLARS = ["Market growth", "Market size", "K-momentum (trade)", "Entry ease"]


def load_tables():
    """The analysis' raw pulls, reshaped into the pipeline's trade_flows / country_indicators tables."""
    imports = pd.read_csv(ANALYSIS / "data/comtrade_imports.csv", dtype={"hs": str})
    exports = pd.read_csv(ANALYSIS / "data/comtrade_kr_exports.csv", dtype={"hs": str})
    trade = pd.concat(
        [
            pd.DataFrame({"reporter_iso3": imports.iso3, "partner_iso3": imports.partner, "flow": "M"}),
            pd.DataFrame({"reporter_iso3": "KOR", "partner_iso3": exports.iso3, "flow": "X"}),
        ],
        ignore_index=True,
    )
    both = pd.concat([imports, exports], ignore_index=True)
    trade = trade.assign(
        hs=both.hs, freq="A", period=both.year.astype(str), value_usd=both.value_usd, net_kg=both.net_kg
    )
    wdi = pd.read_csv(ANALYSIS / "data/wdi.csv")
    return trade, wdi[["iso3", "indicator", "year", "value"]]


@pytest.fixture(scope="module")
def features():
    return build_features(*load_tables())


def reference(name):
    return pd.read_csv(ANALYSIS / f"output/{name}.csv", index_col="iso3")


@pytest.mark.parametrize(
    "variant,table", [("naive", "t7_preliminary_screening"), ("corrected", "t11_screening_volume_no_hubs")]
)
def test_screen_reproduces_the_exploratory_scores_and_ranking(features, variant, table):
    expected = reference(table)

    got = screen(features, variant=variant)

    assert list(got.index) == list(expected.index)
    pd.testing.assert_series_equal(got.score, expected.score, rtol=0.01, check_names=False)
    pd.testing.assert_frame_equal(got[PILLARS], expected[PILLARS], rtol=0.01)


@pytest.mark.parametrize(
    "variant,table", [("naive", "t7_preliminary_screening"), ("corrected", "t11_screening_volume_no_hubs")]
)
def test_screen_reproduces_top3_probabilities_within_monte_carlo_noise(features, variant, table):
    expected = reference(table)

    got = screen(features, variant=variant)

    for col in ("top3_probability", "top3_prob_random_weights"):
        assert (got[col] - expected[col]).abs().max() <= 0.03, col


def test_a_country_missing_a_whole_pillar_is_scored_with_the_median_and_flagged():
    trade, indicators = load_tables()
    without_khm_lpi = indicators[~((indicators.iso3 == "KHM") & (indicators.indicator == "lpi_score"))]

    got = screen(build_features(trade, without_khm_lpi), variant="corrected")

    assert got.loc["KHM", "imputed_pillars"] == ["Entry ease"]
    assert got.drop(index="KHM").imputed_pillars.map(len).sum() == 0
