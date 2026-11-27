"""Country indicators and the multi-criteria screen (docs/pm/03_data_analysis.md §3, engineering plan §8).

Ported from analysis/analyze.py, reading the pipeline's trade_flows and country_indicators tables.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.config import HS, HUBS, NOT_IN_WORLD_BANK, SANCTIONED

WEIGHTS = pd.Series({"Market growth": 0.30, "Market size": 0.25, "K-momentum (trade)": 0.30, "Entry ease": 0.15})
DRAWS = 5000

# Strategy lenses from docs/pm/03_data_analysis.md §3 (FR-1.2); users can also set their own weights
PRESETS = {
    "default": {"label": "Balanced (default)", "weights": WEIGHTS.to_dict()},
    "scale": {
        "label": "Scale markets",
        "weights": {"Market growth": 0.10, "Market size": 0.40, "K-momentum (trade)": 0.35, "Entry ease": 0.15},
    },
    "growth": {
        "label": "Growth / entry markets",
        "weights": {"Market growth": 0.45, "Market size": 0.10, "K-momentum (trade)": 0.25, "Entry ease": 0.20},
    },
}


def cagr(first: float, last: float, years: int) -> float:
    if first is None or last is None or first <= 0 or last <= 0 or years <= 0:
        return np.nan
    return (last / first) ** (1 / years) - 1


def loglinear_growth(values: pd.Series) -> float:
    """Annual growth from a least-squares fit of log(value) on year: less sensitive to one odd base year than CAGR."""
    s = values[values > 0].dropna()
    if len(s) < 3:
        return np.nan
    slope = np.polyfit(s.index.astype(float), np.log(s.to_numpy(dtype=float)), 1)[0]
    return float(np.exp(slope) - 1)


def covered_until(rows: pd.DataFrame, share: float = 0.9) -> int | None:
    """Latest year reported by at least `share` of the countries that report the indicator at all."""
    if rows.empty:
        return None
    per_year = rows.groupby("year").iso3.nunique()
    return int(per_year[per_year >= share * rows.iso3.nunique()].index.max())


def with_provisional_year(trade: pd.DataFrame, through: str | None = None) -> tuple[pd.DataFrame, dict | None]:
    """Add the latest 12 months of 관세청 Korean exports as a provisional annual year.

    Annual (Comtrade) data ends at year Y; 관세청 monthly data runs months beyond it. When 12 months ending after Y
    exist, their sums by destination and HS4 are added as year Y+1 (source "kcs_ttm"), so Korean export momentum
    uses the freshest data while pillars without newer data keep their latest year. `through` (YYYYMM) ends the
    window at an earlier month, for month-on-month comparison. 관세청 and Comtrade agree exactly on annual totals.
    """
    annual_kr = trade[
        (trade.freq == "A") & (trade.flow == "X") & (trade.reporter_iso3 == "KOR") & (trade.source != "kcs_ttm")
    ]
    monthly = trade[(trade.source == "kcs_monthly") & (trade.flow == "X") & (trade.freq == "M")]
    if annual_kr.empty or monthly.empty:
        return trade, None
    last_annual = int(annual_kr.period.astype(int).max())
    months = sorted(p for p in monthly.period.unique() if through is None or p <= through)
    if not months or int(months[-1][:4]) <= last_annual:
        return trade, None
    window = months[-12:]
    if (
        len(window) < 12
        or int(window[-1][:4]) * 12 + int(window[-1][4:]) - (int(window[0][:4]) * 12 + int(window[0][4:])) != 11
    ):
        return trade, None  # 12 consecutive months are needed
    ttm = (
        monthly[monthly.period.isin(window)]
        .assign(hs=lambda d: d.hs.str[:4])
        .groupby(["partner_iso3", "hs"], as_index=False)[["value_usd", "net_kg"]]
        .sum()
    )
    year = last_annual + 1
    rows = ttm.assign(source="kcs_ttm", reporter_iso3="KOR", flow="X", freq="A", period=str(year), imputed=False)
    meta = {
        "year": year,
        "through": f"{window[-1][:4]}-{window[-1][4:]}",
        "window": f"{window[0][:4]}-{window[0][4:]} to {window[-1][:4]}-{window[-1][4:]}",
    }
    return pd.concat([trade, rows[trade.columns.intersection(rows.columns)]], ignore_index=True), meta


class InsufficientData(Exception):
    """Not enough data yet to score (e.g. trade loaded but no Korea-reported exports)."""


def build_features(trade: pd.DataFrame, indicators: pd.DataFrame, hs: list[str] = HS) -> pd.DataFrame:
    """One row per candidate country with every indicator the screen uses, for the given HS category codes."""
    t = trade[(trade.freq == "A") & trade.hs.isin(hs)].assign(year=lambda d: d.period.astype(int))
    imports = t[(t.flow == "M") & (t.partner_iso3 == "WLD")]
    from_kr = t[(t.flow == "M") & (t.partner_iso3 == "KOR")]
    kr = t[(t.flow == "X") & (t.reporter_iso3 == "KOR") & (t.partner_iso3 != "WLD")]
    if kr.empty or imports.empty or indicators.empty:
        raise InsufficientData("needs partner imports, Korea-reported exports and macro indicators")

    # Korea-reported exports by destination
    kr_tot = kr.groupby(["partner_iso3", "year"]).value_usd.sum().unstack()
    last = int(kr.year.max())
    base = kr_tot.get(last - 5, pd.Series(np.nan, index=kr_tot.index))
    f = pd.DataFrame({"kr_exports_latest_musd": kr_tot[last] / 1e6})
    f["kr_export_cagr_5y"] = [cagr(a, b, 5) for a, b in zip(base, kr_tot[last], strict=True)]
    f["kr_latest_year"] = last
    f["kr_export_growth_loglinear"] = kr_tot.loc[:, last - 6 : last].apply(loglinear_growth, axis=1)

    # Destination market size and growth, at each country's latest year with all four HS codes reported
    wld = imports.groupby(["reporter_iso3", "year"]).value_usd.sum().unstack()
    kor = from_kr.groupby(["reporter_iso3", "year"]).value_usd.sum().unstack()
    complete = imports.groupby(["reporter_iso3", "year"]).hs.nunique().unstack().eq(len(hs))
    vol = imports.groupby(["reporter_iso3", "year"]).agg(
        v=("value_usd", "sum"), kg=("net_kg", "sum"), n=("net_kg", "count")
    )
    mkt = []
    for iso in wld.index:
        years = [y for y in complete.columns if complete.loc[iso, y]]
        if not years:
            continue
        ly = max(years)
        row = {
            "iso3": iso,
            "latest_year": ly,
            "imports_latest_musd": wld.loc[iso, ly] / 1e6,
            "import_cagr_5y": cagr(wld.loc[iso].get(ly - 5), wld.loc[iso, ly], 5),
            "imports_from_kr_musd": kor.loc[iso].get(ly, np.nan) / 1e6 if iso in kor.index else np.nan,
            "kr_exports_at_import_year_musd": kr_tot.loc[iso].get(ly, np.nan) / 1e6 if iso in kr_tot.index else np.nan,
        }
        a, b = vol.loc[(iso, ly - 5)] if (iso, ly - 5) in vol.index else None, vol.loc[(iso, ly)]
        if a is not None and a.n >= len(hs) and b.n >= len(hs):
            row["volume_cagr_5y"] = cagr(a.kg, b.kg, 5)
        mkt.append(row)
    mkt = pd.DataFrame(mkt).set_index("iso3")
    mkt["kr_market_share"] = mkt.imports_from_kr_musd / mkt.imports_latest_musd
    mkt["mirror_ratio"] = mkt.imports_from_kr_musd / mkt.kr_exports_at_import_year_musd  # partner / Korea-reported

    # Macro
    def latest(ind: str) -> pd.Series:
        return indicators[indicators.indicator == ind].sort_values("year").groupby("iso3").value.last()

    macro = pd.DataFrame(
        {
            "gdp_pc_usd": latest("gdp_per_capita_usd"),
            "population_m": latest("population") / 1e6,
            "lpi_score": latest("lpi_score"),
        }
    )
    # Each window ends at the indicator's latest year with broad coverage, independent of the trade data's year
    gdp = indicators[indicators.indicator == "gdp_growth_pct"]
    g_end = covered_until(gdp)
    macro["gdp_growth_window"] = f"{g_end - 4}–{g_end}" if g_end else None
    macro["gdp_growth_avg_5y"] = (
        gdp[gdp.year.between(g_end - 4, g_end)].groupby("iso3").value.mean() if g_end else np.nan
    )
    hh = indicators[indicators.indicator == "hh_consumption_pc_const_usd"]
    hc = hh.pivot(index="iso3", columns="year", values="value")
    h_end = covered_until(hh)
    macro["hh_cons_window"] = f"{h_end - 5}–{h_end}" if h_end else None
    lpi = indicators[indicators.indicator == "lpi_score"].sort_values("year").groupby("iso3").year.last()
    macro["lpi_year"] = lpi
    macro["hh_cons_pc_cagr_5y"] = [
        cagr(hc.loc[i].get(h_end - 5), hc.loc[i].get(h_end), 5) if h_end and i in hc.index else np.nan
        for i in macro.index
    ]

    out = mkt.join(f, how="outer").join(macro, how="left")
    out.loc[out.index.isin(NOT_IN_WORLD_BANK), "imports_latest_musd"] = np.nan
    out["hub"] = out.index.isin(HUBS)
    return out


PILLARS = {
    # pillar -> [(column, transform)]; every indicator counts positively
    "Market growth": [("import_cagr_5y", None), ("gdp_growth_avg_5y", None), ("hh_cons_pc_cagr_5y", None)],
    "Market size": [("imports_latest_musd", np.log1p), ("population_m", np.log1p), ("gdp_pc_usd", np.log1p)],
    "K-momentum (trade)": [("kr_export_cagr_5y", None), ("kr_exports_latest_musd", np.log1p)],
    "Entry ease": [("lpi_score", None)],
}


def norm(s: pd.Series, transform=None) -> pd.Series:
    """Min-max scaling after winsorising at the 5th/95th percentiles (bounds relative to the candidate set)."""
    x = transform(s) if transform else s
    lo, hi = x.quantile(0.05), x.quantile(0.95)
    x = x.clip(lo, hi)
    return (x - lo) / (hi - lo) if hi > lo else x * 0


def top3_share(pillars: pd.DataFrame, columns: pd.Index, weight_draws: np.ndarray) -> pd.Series:
    """Share of weight draws in which each country ranks in the TOP3 (everyone, if there are 3 or fewer)."""
    if len(pillars) <= 3:
        return pd.Series(1.0, index=pillars.index)
    scores = pillars[columns].to_numpy() @ weight_draws.T  # countries x draws
    top3 = np.argpartition(-scores, 2, axis=0)[:3]
    return pd.Series(np.bincount(top3.ravel(), minlength=len(pillars)) / len(weight_draws), index=pillars.index)


def screen(
    features: pd.DataFrame, variant: str = "corrected", weights: pd.Series = WEIGHTS, draws: int = DRAWS, seed: int = 42
) -> pd.DataFrame:
    """Score and rank candidates. "corrected" (default, DR-1/DR-2) uses volume growth and excludes hubs;
    "naive" uses nominal growth and keeps hubs. Sanctioned markets are always excluded."""
    f = features[~features.index.isin(SANCTIONED)]
    spec = dict(PILLARS)
    if variant == "corrected":
        f = f[~f.hub]
        spec["Market growth"] = [("volume_cagr_5y", None)] + PILLARS["Market growth"][1:]
    elif variant != "naive":
        raise ValueError(f"unknown variant {variant!r}")

    p = pd.DataFrame(
        {
            name: pd.concat([norm(f[c], t) for c, t in cols], axis=1).mean(axis=1, skipna=True)
            for name, cols in spec.items()
        }
    )
    p = p.dropna(thresh=3)  # too little data to score
    missing = p.isna()
    p = p.fillna(p.median())
    columns = [c for cols in spec.values() for c, _ in cols]
    p["missing_indicators"] = [[c for c in columns if pd.isna(f.at[iso, c])] for iso in p.index]
    p["imputed_pillars"] = [list(missing.columns[row]) for row in missing.to_numpy()]
    p["latest_year"] = f.latest_year.reindex(p.index)
    p["score"] = (p[weights.index] * weights).sum(axis=1) * 100

    rng = np.random.default_rng(seed)
    perturbed = weights.to_numpy() * rng.uniform(0.8, 1.2, size=(draws, len(weights)))
    p["top3_probability"] = top3_share(p, weights.index, perturbed / perturbed.sum(axis=1, keepdims=True))
    p["top3_prob_random_weights"] = top3_share(p, weights.index, rng.dirichlet(np.ones(len(weights)), size=draws))
    p["hub"] = f.hub.reindex(p.index)
    return p.sort_values("score", ascending=False)


CATEGORIES = {"all": HS, **{code: [code] for code in HS}}


def rankings(trade: pd.DataFrame, indicators: pd.DataFrame) -> dict[str, list[dict]]:
    """Default-weight corrected ranking per category, as JSON-ready rows ordered by rank."""
    out = {}
    from pipeline.reasons import reason_pack

    for category, codes in CATEGORIES.items():
        features = build_features(trade, indicators, hs=codes)
        ranked = screen(features)
        rows = ranked.reset_index(names="iso3").assign(rank=lambda d: range(1, len(d) + 1))
        out[category] = [
            {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()}
            | {"reasons": reason_pack(r["iso3"], ranked, features)}
            for r in rows.astype(object).to_dict(orient="records")
        ]
    return out
