"""Reason packs for ranked countries (PRD FR-1.9), checked against docs/pm/03_data_analysis.md."""

import pytest
from analysis_data import load_tables

from pipeline.indicators import build_features, screen
from pipeline.reasons import reason_pack


@pytest.fixture(scope="module")
def packs():
    features = build_features(*load_tables())
    ranked = screen(features, variant="corrected")
    return {iso: reason_pack(iso, ranked, features) for iso in ("USA", "CHN", "PHL")}


def test_strengths_and_weakest_factor_match_the_analysis(packs):
    # 03 §3: China "rests on size and existing Korean momentum, not on real market growth"
    assert [d["pillar"] for d in packs["CHN"]["strengths"]] == ["Market size", "K-momentum (trade)"]
    assert packs["CHN"]["weakest"]["pillar"] == "Market growth"
    assert [d["pillar"] for d in packs["USA"]["strengths"]] == ["Market size", "K-momentum (trade)"]
    assert packs["PHL"]["weakest"]["pillar"] == "Market size"


def test_strengths_state_the_rank_among_scored_countries(packs):
    size = packs["USA"]["strengths"][0]

    assert (size["rank"], size["of"]) == (1, 24)


def test_korean_momentum_is_backed_by_korea_reported_exports_with_source_and_year(packs):
    facts = {f["key"]: f for f in packs["USA"]["strengths"][1]["facts"]}

    assert round(facts["kr_exports_latest_musd"]["value"], 1) == 198.8  # 03 F2
    assert round(facts["kr_export_cagr_5y"]["value"] * 100, 1) == 12.5
    assert facts["kr_exports_latest_musd"]["period"] == "2025"
    assert "Korea-reported" in facts["kr_exports_latest_musd"]["source"]


def test_weakest_factor_shows_the_number_behind_it(packs):
    facts = {f["key"]: f for f in packs["CHN"]["weakest"]["facts"]}

    assert round(facts["volume_cagr_5y"]["value"] * 100, 1) == -0.8  # 03 F3: China import volume
    assert facts["volume_cagr_5y"]["period"] == "2020–2025"


def test_confidence_separates_robust_picks_from_weight_dependent_ones(packs):
    # 03 §3: USA and China are robust; "the third slot depends on business priorities"
    assert packs["USA"]["confidence"]["level"] == "robust"
    assert packs["CHN"]["confidence"]["level"] == "robust"
    assert packs["PHL"]["confidence"]["level"] == "depends on priorities"


def test_caveats_flag_the_mirror_data_gap(packs):
    # 03 F4: the Philippines reports 31% of what Korea says it shipped
    assert any("31%" in c for c in packs["PHL"]["caveats"])
    assert not any("mirror" in c.lower() or "reports" in c for c in packs["USA"]["caveats"])


def test_summary_is_one_readable_sentence_per_part(packs):
    s = packs["CHN"]["summary"]

    assert s.startswith("China ranks #2")
    assert "market size" in s and "Korean export momentum" in s and "market growth" in s


def test_country_names_read_naturally_in_sentences(packs):
    assert packs["PHL"]["summary"].startswith("The Philippines ranks #3")
    assert "Korean exports to this market" in packs["USA"]["summary"]
    assert "weakest pillar, compared with other markets, is market growth" in packs["USA"]["summary"]


def test_headline_is_a_short_why(packs):
    assert (
        packs["USA"]["headline"]
        == "Leads on market size (#1) and Korean export momentum (#1); weakest on market growth (#13)."
    )
    assert len(packs["PHL"]["headline"]) < 120


def test_pack_lists_every_pillar_with_its_facts(packs):
    pillars = packs["USA"]["pillars"]

    assert [p["pillar"] for p in pillars] == ["Market growth", "Market size", "K-momentum (trade)", "Entry ease"]
    assert pillars[3]["facts"][0]["key"] == "lpi_score"
