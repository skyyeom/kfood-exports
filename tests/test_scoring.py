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


def test_presets_reproduce_the_two_strategy_lenses_in_the_analysis(features):
    # 03 §3: "Canada wins if size and stability matter more; India wins if growth matters most"
    from pipeline.indicators import PRESETS

    scale = screen(features, weights=pd.Series(PRESETS["scale"]["weights"]), draws=200)
    growth = screen(features, weights=pd.Series(PRESETS["growth"]["weights"]), draws=200)

    assert list(scale.index[:3]) == ["USA", "CHN", "CAN"] and "JPN" in scale.index[:6]
    assert "IND" in growth.index[:3] and {"PHL", "MYS", "VNM"} <= set(growth.index[:6])


def test_every_preset_has_a_label_and_weights_that_sum_to_one():
    from pipeline.indicators import PRESETS, WEIGHTS

    assert PRESETS["default"]["weights"] == WEIGHTS.to_dict()
    for p in PRESETS.values():
        assert p["label"] and abs(sum(p["weights"].values()) - 1) < 1e-9 and set(p["weights"]) == set(PILLARS)


def kcs_month_rows(months, partner, hs6, value):
    return pd.DataFrame(
        [
            {
                "source": "kcs_monthly",
                "reporter_iso3": "KOR",
                "partner_iso3": partner,
                "flow": "X",
                "hs": hs6,
                "freq": "M",
                "period": p,
                "value_usd": value,
                "net_kg": 1.0,
                "imputed": False,
            }
            for p in months
        ]
    )


def months_between(start, end):
    y, m, out = int(start[:4]), int(start[4:]), []
    while f"{y}{m:02d}" <= end:
        out.append(f"{y}{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def test_provisional_year_adds_the_latest_12_months_of_korean_exports_as_the_next_year():
    from pipeline.indicators import with_provisional_year

    trade, _ = load_tables()  # annual Korea-reported exports through 2025
    monthly = kcs_month_rows(months_between("202501", "202610"), "USA", "190590", 1.0e6)

    out, meta = with_provisional_year(pd.concat([trade, monthly], ignore_index=True))

    added = out[(out.source == "kcs_ttm") & (out.partner_iso3 == "USA")]
    assert meta == {"year": 2026, "through": "2026-10", "window": "2025-11 to 2026-10"}
    assert added[["reporter_iso3", "flow", "hs", "freq", "period"]].values.tolist() == [
        ["KOR", "X", "1905", "A", "2026"]
    ]
    assert added.value_usd.iloc[0] == 12 * 1.0e6  # November 2025 to October 2026


def test_no_provisional_year_without_12_months_beyond_the_annual_data():
    from pipeline.indicators import with_provisional_year

    trade, _ = load_tables()
    monthly = kcs_month_rows(months_between("202501", "202512"), "USA", "190590", 1.0e6)

    out, meta = with_provisional_year(pd.concat([trade, monthly], ignore_index=True))

    assert meta is None and len(out) == len(trade) + 12


def test_the_provisional_year_drives_korean_momentum_and_keeps_other_pillars():
    from pipeline.indicators import with_provisional_year

    trade, indicators = load_tables()
    monthly = kcs_month_rows(months_between("202501", "202610"), "USA", "190590", 3.0e7)

    f = build_features(with_provisional_year(pd.concat([trade, monthly], ignore_index=True))[0], indicators)

    assert f.loc["USA", "kr_latest_year"] == 2026 and f.loc["USA", "kr_exports_latest_musd"] == 360.0
    assert f.loc["USA", "latest_year"] == 2025  # partner imports: no 2026 data yet


def test_provisional_year_can_end_at_an_earlier_month_for_month_on_month_comparison():
    from pipeline.indicators import with_provisional_year

    trade, _ = load_tables()
    monthly = pd.concat(
        [
            kcs_month_rows(months_between("202501", "202609"), "USA", "190590", 1.0e6),
            kcs_month_rows(["202610"], "USA", "190590", 5.0e6),
        ],
        ignore_index=True,
    )

    latest, meta = with_provisional_year(pd.concat([trade, monthly], ignore_index=True))
    earlier, meta_prev = with_provisional_year(pd.concat([trade, monthly], ignore_index=True), through="202609")

    usa = lambda t: t[(t.source == "kcs_ttm") & (t.partner_iso3 == "USA")].value_usd.iloc[0]
    assert (usa(earlier), meta_prev["through"]) == (12 * 1.0e6, "2026-09")
    assert (usa(latest), meta["through"]) == (11 * 1.0e6 + 5.0e6, "2026-10")
