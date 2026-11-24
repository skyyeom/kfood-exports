"""Country indicators and the multi-criteria screen (docs/pm/03_data_analysis.md §3, engineering plan §8).

Ported from analysis/analyze.py, reading the pipeline's trade_flows and country_indicators tables.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.config import HS, HUBS, NOT_IN_WORLD_BANK, SANCTIONED

WEIGHTS = pd.Series({"Market growth": 0.30, "Market size": 0.25, "K-momentum (trade)": 0.30, "Entry ease": 0.15})
DRAWS = 5000


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


def build_features(trade: pd.DataFrame, indicators: pd.DataFrame) -> pd.DataFrame:
    """One row per candidate country with every indicator the screen uses."""
    t = trade[trade.freq == "A"].assign(year=lambda d: d.period.astype(int))
    imports = t[(t.flow == "M") & (t.partner_iso3 == "WLD")]
    from_kr = t[(t.flow == "M") & (t.partner_iso3 == "KOR")]
    kr = t[(t.flow == "X") & (t.reporter_iso3 == "KOR")]

    # Korea-reported exports by destination
    kr_tot = kr[kr.partner_iso3 != "WLD"].groupby(["partner_iso3", "year"]).value_usd.sum().unstack()
    last = int(kr.year.max())
    f = pd.DataFrame({"kr_exports_latest_musd": kr_tot[last] / 1e6})
    f["kr_export_cagr_5y"] = [cagr(a, b, 5) for a, b in zip(kr_tot.get(last - 5), kr_tot[last], strict=True)]
    f["kr_export_growth_loglinear"] = kr_tot.loc[:, last - 6 : last].apply(loglinear_growth, axis=1)

    # Destination market size and growth, at each country's latest year with all four HS codes reported
    wld = imports.groupby(["reporter_iso3", "year"]).value_usd.sum().unstack()
    kor = from_kr.groupby(["reporter_iso3", "year"]).value_usd.sum().unstack()
    complete = imports.groupby(["reporter_iso3", "year"]).hs.nunique().unstack().eq(len(HS))
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
        }
        a, b = vol.loc[(iso, ly - 5)] if (iso, ly - 5) in vol.index else None, vol.loc[(iso, ly)]
        if a is not None and a.n >= len(HS) and b.n >= len(HS):
            row["volume_cagr_5y"] = cagr(a.kg, b.kg, 5)
        mkt.append(row)
    mkt = pd.DataFrame(mkt).set_index("iso3")
    mkt["kr_market_share"] = mkt.imports_from_kr_musd / mkt.imports_latest_musd

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
    g = indicators[(indicators.indicator == "gdp_growth_pct") & indicators.year.between(last - 4, last)]
    macro["gdp_growth_avg_5y"] = g.groupby("iso3").value.mean()
    hc = indicators[indicators.indicator == "hh_consumption_pc_const_usd"].pivot(
        index="iso3", columns="year", values="value"
    )
    macro["hh_cons_pc_cagr_5y"] = [
        cagr(hc.loc[i].get(last - 6), hc.loc[i].get(last - 1), 5) if i in hc.index else np.nan for i in macro.index
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


def top3_share(pillars: pd.DataFrame, weight_draws: np.ndarray) -> pd.Series:
    """Share of weight draws in which each country ranks in the TOP3."""
    scores = pillars[WEIGHTS.index].to_numpy() @ weight_draws.T  # countries x draws
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
    p["imputed_pillars"] = [list(missing.columns[row]) for row in missing.to_numpy()]
    p["score"] = (p[weights.index] * weights).sum(axis=1) * 100

    rng = np.random.default_rng(seed)
    perturbed = weights.to_numpy() * rng.uniform(0.8, 1.2, size=(draws, len(weights)))
    p["top3_probability"] = top3_share(p, perturbed / perturbed.sum(axis=1, keepdims=True))
    p["top3_prob_random_weights"] = top3_share(p, rng.dirichlet(np.ones(len(weights)), size=draws))
    p["hub"] = f.hub.reindex(p.index)
    return p.sort_values("score", ascending=False)
