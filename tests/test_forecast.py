"""Score history and forecasts (engineering plan §8: simple models chosen by rolling-origin backtest)."""

import pandas as pd
import pytest
from analysis_data import ANALYSIS, load_tables

from pipeline.forecast import forecast_series, history, project

YEARS = [2020, 2021, 2022, 2023, 2024, 2025]


def test_a_steady_linear_series_is_forecast_by_its_trend_line():
    f = forecast_series(YEARS, [10, 20, 30, 40, 50, 60], [2026, 2027, 2028])

    assert f["model"] == "drift"
    assert f["point"] == pytest.approx([70, 80, 90])


def test_a_compounding_series_is_forecast_by_compound_growth():
    f = forecast_series(YEARS, [100 * 1.1**k for k in range(6)], [2026, 2027])

    assert f["model"] == "compound growth"
    assert f["point"] == pytest.approx([100 * 1.1**6, 100 * 1.1**7])


def test_a_flat_series_is_forecast_unchanged():
    assert forecast_series(YEARS, [5] * 6, [2026])["model"] == "no change"


def test_a_short_series_falls_back_to_no_change():
    f = forecast_series([2024, 2025], [3.0, 4.0], [2026])

    assert (f["model"], f["point"]) == ("no change", [4.0])


def test_uncertainty_brackets_the_forecast_and_widens_with_the_horizon():
    noisy = [100, 112, 118, 135, 140, 158]

    f = forecast_series(YEARS, noisy, [2026, 2027, 2028])

    assert all(lo <= p <= hi for lo, p, hi in zip(f["low"], f["point"], f["high"], strict=True))
    widths = [h / lo for lo, h in zip(f["low"], f["high"], strict=True)]
    assert widths == sorted(widths)


@pytest.fixture(scope="module")
def tables():
    return load_tables()


def test_history_ends_at_the_published_screen(tables):
    reference = pd.read_csv(ANALYSIS / "output/t11_screening_volume_no_hubs.csv", index_col="iso3")

    h = history(*tables, years=[2023, 2024, 2025])

    latest = h[h.year == 2025].set_index("iso3")
    pd.testing.assert_series_equal(
        latest.score.sort_index(), reference.score.sort_index(), rtol=0.01, check_names=False
    )
    assert set(h.year) == {2023, 2024, 2025}


def test_history_scores_each_year_with_data_known_by_then(tables):
    h = history(*tables, years=[2020, 2025]).set_index(["year", "iso3"])

    assert h.loc[(2020, "USA"), "score"] != h.loc[(2025, "USA"), "score"]


def test_forecast_gives_every_year_a_full_ranking_and_probabilities_that_sum_to_three(tables):
    p = project(*tables, years=[2026, 2027], draws=40, seed=1)

    for year, g in p.groupby("year"):
        assert sorted(g["rank"]) == list(range(1, len(g) + 1))
        assert g.p_top3.sum() == pytest.approx(3.0)


def test_forecast_is_reproducible_with_a_seed(tables):
    a = project(*tables, years=[2026], draws=20, seed=7)
    b = project(*tables, years=[2026], draws=20, seed=7)

    pd.testing.assert_frame_equal(a, b)


def test_forecasts_move_no_faster_than_each_markets_own_history(tables):
    # Regressions: re-scoring forecast data moved India #4 -> #13 in a year; compounding Brazil's score took it
    # from 52.5 to 89.9 by 2028. Over h years a score may move at most h x its largest past one-year change.
    past = history(*tables, years=YEARS).pivot(index="iso3", columns="year", values="score")
    biggest_step = past.diff(axis=1).abs().max(axis=1)

    future = project(*tables, years=[2026, 2027, 2028], draws=40, seed=1)

    for row in future.itertuples():
        h = row.year - 2025
        assert abs(row.score - past.loc[row.iso3, 2025]) <= h * biggest_step[row.iso3] + 1e-9, (row.iso3, row.year)


def test_forecast_scores_stay_on_the_0_to_100_scale(tables):
    future = project(*tables, years=[2026, 2027, 2028], draws=40, seed=1)

    assert future.score.between(0, 100).all() and future.low.ge(0).all() and future.high.le(100).all()


def test_a_damped_trend_slows_each_year():
    f = forecast_series(YEARS, [10, 20, 30, 40, 50, 60], [2026, 2027, 2028], models=("damped drift",))

    steps = [f["point"][0] - 60, f["point"][1] - f["point"][0], f["point"][2] - f["point"][1]]
    assert f["model"] == "damped drift" and steps == sorted(steps, reverse=True) and steps[0] < 10


def test_holdout_check_forecasts_the_latest_year_from_earlier_years_only(tables):
    from pipeline.forecast import holdout_check

    check = holdout_check(*tables)

    assert check["year"] == 2025 and check["trained_on"] == "2020–2024"
    assert check["actual_top3"] == ["USA", "CHN", "PHL"]  # docs/pm/03_data_analysis.md §3
    assert len(check["predicted_top3"]) == 3
    assert check["model_mae"] > 0 and check["no_change_mae"] > 0
