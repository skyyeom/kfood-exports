"""The pipeline's scoring must reproduce the exploratory screen in docs/pm/03_data_analysis.md §3."""

import pandas as pd
import pytest
from analysis_data import ANALYSIS, load_tables

from pipeline.indicators import build_features, screen

PILLARS = ["Market growth", "Market size", "K-momentum (trade)", "Entry ease"]


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


def test_short_export_history_gives_no_growth_rate_instead_of_crashing():
    trade, indicators = load_tables()
    recent = trade[trade.period.astype(int) >= 2022]

    got = build_features(recent, indicators)

    assert got.kr_export_cagr_5y.isna().all()
    assert got.loc["USA", "kr_exports_latest_musd"] > 0


def test_fewer_than_three_countries_are_all_in_the_top3():
    two = build_features(*load_tables()).loc[["USA", "PHL"]]

    got = screen(two, variant="corrected")

    assert got.top3_probability.tolist() == [1.0, 1.0]


def test_macro_windows_follow_the_macro_data_not_the_latest_export_year():
    trade, indicators = load_tables()
    extra = trade[(trade.flow == "X") & (trade.period == "2025")].assign(period="2026")
    before = build_features(trade, indicators)

    after = build_features(pd.concat([trade, extra]), indicators)

    for col in ("gdp_growth_avg_5y", "hh_cons_pc_cagr_5y"):
        pd.testing.assert_series_equal(after[col], before[col])


def test_screen_flags_indicators_missing_inside_a_pillar(features):
    trade, indicators = load_tables()
    without = indicators[~((indicators.iso3 == "KHM") & (indicators.indicator == "gdp_growth_pct"))]

    got = screen(build_features(trade, without), variant="corrected")

    assert got.loc["KHM", "missing_indicators"] == ["gdp_growth_avg_5y"]
    assert got.loc["USA", "missing_indicators"] == []


def test_custom_weights_drive_the_top3_probabilities(features):
    growth_only = pd.Series({"Market growth": 1.0, "Market size": 0.0, "K-momentum (trade)": 0.0, "Entry ease": 0.0})

    got = screen(features, variant="corrected", weights=growth_only)

    assert set(got.index[:3]) == set(got.top3_probability.nlargest(3).index)
