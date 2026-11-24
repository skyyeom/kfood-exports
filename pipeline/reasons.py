"""Reason packs: why a country ranks where it does, in plain language, with every number traceable (PRD FR-1.9).

Built from the screen's own inputs, never written by an LLM, so the dashboard and the agent can quote them safely.
"""

from __future__ import annotations

import math

import pandas as pd

from pipeline.config import CANDIDATES

PLAIN = {
    "Market growth": "market growth",
    "Market size": "market size",
    "K-momentum (trade)": "Korean export momentum",
    "Entry ease": "ease of entry",
}
LOTTE_LOCAL_PRODUCTION = {"IND", "KAZ", "RUS", "PAK", "MMR"}  # 03 F7, decision D7
NEEDS_THE = {"USA", "GBR", "NLD", "PHL", "ARE"}  # names read with "the" in a sentence
COMTRADE_IMPORTS = "UN Comtrade, partner-reported imports (CIF)"
COMTRADE_KOREA = "UN Comtrade, Korea-reported exports (FOB)"
WDI = "World Bank WDI"


def _num(v) -> float | None:
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def _facts(pillar: str, f: pd.Series) -> list[dict]:
    """The indicators behind a pillar, each with its value, unit, period and source."""
    ly, kr = f.get("latest_year"), f.get("kr_latest_year")

    def span(end) -> str | None:
        return f"{int(end) - 5}–{int(end)}" if _num(end) is not None else None

    spec = {
        "Market growth": [
            ("volume_cagr_5y", "Category import volume growth", "%/yr", span(ly), COMTRADE_IMPORTS),
            ("gdp_growth_avg_5y", "Average real GDP growth", "%", f.get("gdp_growth_window"), WDI),
            ("hh_cons_pc_cagr_5y", "Household consumption per person, growth", "%/yr", f.get("hh_cons_window"), WDI),
        ],
        "Market size": [
            ("imports_latest_musd", "Category imports", "US$ M", str(int(ly)) if _num(ly) else None, COMTRADE_IMPORTS),
            ("population_m", "Population", "million", None, WDI),
            ("gdp_pc_usd", "GDP per person", "US$", None, WDI),
        ],
        "K-momentum (trade)": [
            (
                "kr_exports_latest_musd",
                "Korean exports to this market",
                "US$ M",
                str(int(kr)) if _num(kr) else None,
                COMTRADE_KOREA,
            ),
            ("kr_export_cagr_5y", "Korean export growth", "%/yr", span(kr), COMTRADE_KOREA),
        ],
        "Entry ease": [
            (
                "lpi_score",
                "Logistics Performance Index (1–5)",
                "score",
                str(int(f["lpi_year"])) if _num(f.get("lpi_year")) else None,
                "World Bank LPI",
            ),
        ],
    }[pillar]
    return [
        {"key": k, "label": label, "value": _num(f.get(k)), "unit": unit, "period": period, "source": src}
        for k, label, unit, period, src in spec
        if _num(f.get(k)) is not None
    ]


def _fmt(fact: dict) -> str:
    v, unit = fact["value"], fact["unit"]
    text = {
        "%/yr": f"{v * 100:+.1f}%/yr",
        "%": f"{v:.1f}%",
        "US$ M": f"US${v:,.1f}M",
        "US$": f"US${v:,.0f}",
        "million": f"{v:,.0f}M",
        "score": f"{v:.2f}",
    }[unit]
    label = fact["label"] if fact["label"].startswith("Korean") else fact["label"][0].lower() + fact["label"][1:]
    return f"{label} {text}" + (f" ({fact['period']})" if fact["period"] else "")


def _confidence(p20: float, p_any: float) -> dict:
    if p20 >= 0.9 and p_any >= 0.5:
        level, text = "robust", "stays in the TOP3 under almost any weighting"
    elif p20 >= 0.5:
        level, text = (
            "depends on priorities",
            "holds with the default weights but often drops out under other weightings",
        )
    else:
        level, text = "fragile", "drops out of the TOP3 with small changes to the weights"
    return {
        "level": level,
        "p_top3": p20,
        "p_top3_any_weights": p_any,
        "text": f"{text}: TOP3 in {p20:.0%} of ±20% weight variations and {p_any:.0%} of random weightings.",
    }


def reason_pack(iso: str, ranked: pd.DataFrame, features: pd.DataFrame) -> dict:
    """Strengths, weakest factor, confidence and caveats for one country in a screen's output."""
    pillars = list(PLAIN)
    ranks = ranked[pillars].rank(ascending=False, method="min")
    row, f = ranked.loc[iso], features.loc[iso]
    # strongest = best rank, ties broken by the higher pillar value; weakest = worst rank, ties by the lower value
    order = sorted(pillars, key=lambda p: (ranks.at[iso, p], -row[p]))

    def entry(p: str) -> dict:
        return {
            "pillar": p,
            "name": PLAIN[p],
            "rank": int(ranks.at[iso, p]),
            "of": len(ranked),
            "value": float(row[p]),
            "facts": _facts(p, f),
        }

    strengths = [entry(p) for p in order[:2]]
    weakest = entry(min(pillars, key=lambda p: (-ranks.at[iso, p], row[p])))

    name = CANDIDATES[iso][1]
    the = f"The {name}" if iso in NEEDS_THE else name
    position = int(ranked.index.get_loc(iso)) + 1

    def part(e: dict) -> str:
        lead = e["facts"][0] if e["facts"] else None
        return f"{e['name']} (#{e['rank']} of {e['of']}{'; ' + _fmt(lead) if lead else ''})"

    summary = (
        f"{the} ranks #{position} with a score of {row['score']:.1f}. "
        f"Strongest on {part(strengths[0])} and {part(strengths[1])}. "
        f"Its weakest pillar, compared with other markets, is {part(weakest)}."
    )

    caveats = []
    ratio = _num(f.get("mirror_ratio"))
    if ratio is not None and abs(ratio - 1) > 0.3:
        caveats.append(
            f"{the} reports imports from Korea of {ratio:.0%} of what Korea says it shipped "
            f"({int(f['latest_year'])}); Korea-reported exports are used for momentum."
        )
    if iso in LOTTE_LOCAL_PRODUCTION:
        caveats.append("Lotte produces locally here, so Korean export figures understate the business.")
    if row.get("hub"):
        caveats.append("Re-export hub: imports overstate local consumption.")
    if row.get("imputed_pillars"):
        caveats.append(
            f"Not enough data for {', '.join(PLAIN[p] for p in row['imputed_pillars'])}; "
            "the median of all countries was used."
        )
    if row.get("missing_indicators"):
        caveats.append(f"{len(row['missing_indicators'])} indicator(s) missing; pillars use the indicators available.")

    return {
        "iso3": iso,
        "name": name,
        "rank": position,
        "summary": summary,
        "strengths": strengths,
        "weakest": weakest,
        "confidence": _confidence(row["top3_probability"], row["top3_prob_random_weights"]),
        "caveats": caveats,
    }
