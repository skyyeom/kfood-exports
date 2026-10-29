"""Exploratory market & data analysis for WellGTM (feeds docs/pm/03_data_analysis.md).

Usage: .venv/bin/python analysis/analyze.py
Inputs: analysis/data/*.csv (from collect.py)
Outputs: analysis/output/*.csv|md, docs/pm/figures/*.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "data"
OUT = ROOT / "analysis" / "output"
FIG = ROOT / "docs" / "pm" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

HS_LABEL = {"1704": "Sugar confectionery", "1806": "Chocolate", "1905": "Bakery & biscuits", "2105": "Ice cream"}
HUBS = {"HKG", "SGP", "NLD", "ARE"}  # re-export hubs: imports overstate local consumption
SANCTIONED = {"RUS"}

im = pd.read_csv(DATA / "comtrade_imports.csv", dtype={"hs": str})
ex = pd.read_csv(DATA / "comtrade_kr_exports.csv", dtype={"hs": str})
wdi = pd.read_csv(DATA / "wdi.csv")


def cagr(first: float, last: float, years: int) -> float:
    if first is None or last is None or first <= 0 or last <= 0 or years <= 0:
        return np.nan
    return (last / first) ** (1 / years) - 1


def md(df: pd.DataFrame, name: str, floatfmt: str = ",.1f") -> None:
    df.to_csv(OUT / f"{name}.csv")
    (OUT / f"{name}.md").write_text(df.to_markdown(floatfmt=floatfmt))


# ---------- 1. Korea's exports (Korea-reported, FOB) ----------
kr_world = ex[ex.iso3 == "WLD"].pivot(index="year", columns="hs", values="value_usd") / 1e6
kr_world["Total"] = kr_world.sum(axis=1)
md(kr_world.rename(columns=HS_LABEL), "t1_korea_exports_world_musd")

ax = kr_world[list(HS_LABEL)].rename(columns=HS_LABEL).plot.area(figsize=(9, 4.5), alpha=0.85)
ax.set_title("Korea exports by category, HS 1704/1806/1905/2105 (US$ M, Korea-reported)")
ax.set_ylabel("US$ M")
ax.set_xlabel("")
ax.legend(title=None, loc="upper left")
plt.tight_layout()
plt.savefig(FIG / "fig1_korea_exports_by_category.png", dpi=150)
plt.close()

kr = ex[ex.iso3 != "WLD"].copy()
kr_tot = kr.groupby(["iso3", "year"]).value_usd.sum().unstack()
LAST = 2025
kr_country = pd.DataFrame({
    "kr_exports_2025_musd": kr_tot[LAST] / 1e6,
    "kr_exports_2020_musd": kr_tot[2020] / 1e6,
})
kr_country["kr_export_cagr_20_25"] = [cagr(a, b, 5) for a, b in zip(kr_tot[2020], kr_tot[LAST], strict=True)]
kr_country["share_of_kr_exports"] = kr_tot[LAST] / kr_world.loc[LAST, "Total"] / 1e6
by_hs = kr[kr.year == LAST].pivot_table(index="iso3", columns="hs", values="value_usd", aggfunc="sum") / 1e6
by_hs.columns = [f"kr25_{HS_LABEL[c]}" for c in by_hs.columns]
kr_country = kr_country.join(by_hs).sort_values("kr_exports_2025_musd", ascending=False)
md(kr_country, "t2_korea_exports_by_destination")

top = kr_country.head(15)[[c for c in kr_country.columns if c.startswith("kr25_")]]
ax = top.rename(columns=lambda c: c.replace("kr25_", "")).iloc[::-1].plot.barh(stacked=True, figsize=(9, 6))
ax.set_title("Top 15 destinations of Korean confectionery/bakery/ice-cream exports, 2025 (US$ M)")
ax.set_xlabel("US$ M")
plt.tight_layout()
plt.savefig(FIG / "fig2_top_destinations_2025.png", dpi=150)
plt.close()

# ---------- 2. Destination market size & growth (partner-reported imports, CIF) ----------
wld = im[im.partner == "WLD"].groupby(["iso3", "year"]).value_usd.sum().unstack()
kor = im[im.partner == "KOR"].groupby(["iso3", "year"]).value_usd.sum().unstack()
n_hs = im[im.partner == "WLD"].groupby(["iso3", "year"]).hs.nunique().unstack()
complete = n_hs.eq(4)


def latest_complete(iso: str) -> int | None:
    yrs = [y for y in complete.columns if complete.loc[iso, y]]
    return max(yrs) if yrs else None


rows = []
for iso in wld.index:
    ly = latest_complete(iso)
    if ly is None:
        continue
    base = ly - 5
    rows.append({
        "iso3": iso,
        "latest_year": ly,
        "imports_latest_musd": wld.loc[iso, ly] / 1e6,
        "import_cagr_5y": cagr(wld.loc[iso].get(base), wld.loc[iso, ly], 5),
        "imports_from_kr_musd": kor.loc[iso, ly] / 1e6 if iso in kor.index and not np.isnan(kor.loc[iso].get(ly, np.nan)) else np.nan,
    })
mkt = pd.DataFrame(rows).set_index("iso3")
mkt["kr_market_share"] = mkt.imports_from_kr_musd / mkt.imports_latest_musd
by_hs_m = (
    im[(im.partner == "WLD")]
    .merge(mkt.latest_year.rename("ly"), left_on="iso3", right_index=True)
    .query("year == ly")
    .pivot_table(index="iso3", columns="hs", values="value_usd", aggfunc="sum")
    / 1e6
)
by_hs_m.columns = [f"imp_{HS_LABEL[c]}" for c in by_hs_m.columns]
mkt = mkt.join(by_hs_m)
mkt["hub"] = mkt.index.isin(HUBS)
md(mkt.sort_values("imports_latest_musd", ascending=False), "t3_destination_markets", floatfmt=",.3f")

# ---------- 3. Data quality: coverage + mirror discrepancy ----------
cov = n_hs.reindex(columns=range(2015, 2026)).fillna(0).astype(int)
md(cov, "t4_coverage_hs_count", floatfmt=".0f")
mirror = []
for iso in mkt.index:
    y = int(mkt.loc[iso, "latest_year"])
    kr_reported = kr_tot.loc[iso, y] if iso in kr_tot.index else np.nan
    partner_reported = kor.loc[iso, y] if iso in kor.index else np.nan
    mirror.append({"iso3": iso, "year": y, "kr_reported_exports_musd": kr_reported / 1e6,
                   "partner_reported_imports_from_kr_musd": partner_reported / 1e6,
                   "ratio_partner_to_kr": partner_reported / kr_reported if kr_reported else np.nan})
mirror = pd.DataFrame(mirror).set_index("iso3").sort_values("ratio_partner_to_kr")
md(mirror, "t5_mirror_discrepancy", floatfmt=",.2f")

# ---------- 4. Macro ----------
def wdi_latest(ind: str) -> pd.Series:
    d = wdi[wdi.indicator == ind].sort_values("year").groupby("iso3").last()
    return d.value


macro = pd.DataFrame({
    "gdp_pc_usd": wdi_latest("gdp_per_capita_usd"),
    "population_m": wdi_latest("population") / 1e6,
    "urban_pct": wdi_latest("urban_pct"),
    "lpi_score": wdi_latest("lpi_score"),
    "inflation_pct": wdi_latest("inflation_pct"),
})
g = wdi[(wdi.indicator == "gdp_growth_pct") & (wdi.year.between(2021, 2025))]
macro["gdp_growth_avg_21_25"] = g.groupby("iso3").value.mean()
hc = wdi[wdi.indicator == "hh_consumption_pc_const_usd"].pivot(index="iso3", columns="year", values="value")
macro["hh_cons_pc_cagr_19_24"] = [cagr(hc.loc[i].get(2019), hc.loc[i].get(2024), 5) if i in hc.index else np.nan
                                  for i in macro.index]
md(macro.sort_values("gdp_pc_usd", ascending=False), "t6_macro", floatfmt=",.2f")

# ---------- 5. Preliminary screening (hypothesis generation only) ----------
f = mkt.join(kr_country[["kr_exports_2025_musd", "kr_export_cagr_20_25"]], how="outer").join(macro, how="left")
f = f[~f.index.isin(SANCTIONED)]
f.loc["TWN", "imports_latest_musd"] = np.nan  # Taiwan not a Comtrade reporter; only Korea-reported data
features = {
    # pillar -> [(column, direction, transform)]
    "Market growth": [("import_cagr_5y", 1, None), ("gdp_growth_avg_21_25", 1, None), ("hh_cons_pc_cagr_19_24", 1, None)],
    "Market size": [("imports_latest_musd", 1, np.log1p), ("population_m", 1, np.log1p), ("gdp_pc_usd", 1, np.log1p)],
    "K-momentum (trade)": [("kr_export_cagr_20_25", 1, None), ("kr_exports_2025_musd", 1, np.log1p)],
    "Entry ease": [("lpi_score", 1, None)],
}


def norm(s: pd.Series, direction: int, transform) -> pd.Series:
    x = transform(s) if transform else s
    lo, hi = x.quantile(0.05), x.quantile(0.95)  # winsorise outliers before min-max
    x = x.clip(lo, hi)
    n = (x - lo) / (hi - lo) if hi > lo else x * 0
    return n if direction > 0 else 1 - n


pillars = pd.DataFrame(index=f.index)
for p, cols in features.items():
    pillars[p] = pd.concat([norm(f[c], d, t) for c, d, t in cols], axis=1).mean(axis=1, skipna=True)
pillars = pillars.dropna(thresh=3)
pillars = pillars.fillna(pillars.median())
W0 = pd.Series({"Market growth": 0.30, "Market size": 0.25, "K-momentum (trade)": 0.30, "Entry ease": 0.15})
pillars["score"] = (pillars[W0.index] * W0).sum(axis=1) * 100

rng = np.random.default_rng(42)
N = 5000
top3_counts = pd.Series(0, index=pillars.index, dtype=float)
for _ in range(N):
    w = W0 * rng.uniform(0.8, 1.2, size=len(W0))  # +/-20% perturbation
    w = w / w.sum()
    s = (pillars[W0.index] * w).sum(axis=1)
    top3_counts[s.nlargest(3).index] += 1
pillars["top3_probability"] = top3_counts / N
# wider check: Dirichlet-random weights (any weighting a user might pick)
top3_any = pd.Series(0, index=pillars.index, dtype=float)
for w in rng.dirichlet(np.ones(len(W0)), size=N):
    s = (pillars[W0.index] * w).sum(axis=1)
    top3_any[s.nlargest(3).index] += 1
pillars["top3_prob_random_weights"] = top3_any / N
pillars["hub"] = pillars.index.isin(HUBS)
pillars = pillars.sort_values("score", ascending=False)
md(pillars, "t7_preliminary_screening", floatfmt=".3f")



g4 = kr_country[kr_country.kr_exports_2025_musd >= 5].sort_values("kr_export_cagr_20_25")
ax = (g4.kr_export_cagr_20_25 * 100).plot.barh(figsize=(8, 7), color="tab:orange")
ax.set_title("Korea export CAGR 2020-2025 by destination (destinations ≥ US$5M in 2025)")
ax.set_xlabel("%")
plt.tight_layout()
plt.savefig(FIG / "fig4_korea_export_growth.png", dpi=150)
plt.close()

# HS-level growth of Korea exports by destination (for category-market fit)
hs_cagr = []
for (iso, hs), grp in kr.groupby(["iso3", "hs"]):
    s = grp.set_index("year").value_usd
    hs_cagr.append({"iso3": iso, "hs": HS_LABEL[hs], "v2025_musd": s.get(LAST, np.nan) / 1e6,
                    "cagr_20_25": cagr(s.get(2020), s.get(LAST), 5)})
hs_cagr = pd.DataFrame(hs_cagr)
fit = hs_cagr[hs_cagr.v2025_musd >= 3].sort_values("cagr_20_25", ascending=False).head(25).set_index(["iso3", "hs"])
md(fit, "t8_fastest_growing_country_category", floatfmt=",.3f")

# ---------- 6. Price vs volume: is import growth real demand or price inflation? ----------
vol = im[(im.partner == "WLD")].groupby(["iso3", "year"]).agg(v=("value_usd", "sum"), kg=("net_kg", "sum"),
                                                                n=("net_kg", "count")).reset_index()
pv = []
for iso in mkt.index:
    ly = int(mkt.loc[iso, "latest_year"])
    a = vol[(vol.iso3 == iso) & (vol.year == ly - 5)]
    b2 = vol[(vol.iso3 == iso) & (vol.year == ly)]
    if a.empty or b2.empty or a.n.iloc[0] < 4 or b2.n.iloc[0] < 4:
        continue
    vc = cagr(a.v.iloc[0], b2.v.iloc[0], 5)
    kc = cagr(a.kg.iloc[0], b2.kg.iloc[0], 5)
    pv.append({"iso3": iso, "value_cagr_5y": vc, "volume_cagr_5y": kc,
               "unit_price_cagr_5y": (1 + vc) / (1 + kc) - 1 if not np.isnan(kc) else np.nan})
pv = pd.DataFrame(pv).set_index("iso3").sort_values("volume_cagr_5y", ascending=False)
md(pv, "t9_price_vs_volume", floatfmt=".3f")

b = f.join(pv[["volume_cagr_5y"]]).dropna(subset=["imports_latest_musd", "volume_cagr_5y"])
b = b[~b.index.isin(["MMR"])]
fig, ax = plt.subplots(figsize=(10, 6.5))
sc = ax.scatter(b.imports_latest_musd, b.volume_cagr_5y * 100, s=20 + b.kr_exports_2025_musd.fillna(0) * 3,
                c=b.kr_market_share.fillna(0) * 100, cmap="viridis", alpha=0.75, edgecolor="k")
for iso, r in b.iterrows():
    ax.annotate(iso + ("*" if iso in HUBS else ""), (r.imports_latest_musd, r.volume_cagr_5y * 100),
                fontsize=8, xytext=(4, 2), textcoords="offset points")
ax.set_xscale("log")
ax.axhline(b.volume_cagr_5y.median() * 100, ls="--", c="grey", lw=0.8)
ax.axvline(b.imports_latest_musd.median(), ls="--", c="grey", lw=0.8)
ax.set_xlabel("Category import market size, latest year (US$ M, log scale)")
ax.set_ylabel("Import VOLUME CAGR, 5 years (%)")
ax.set_title("Market size vs real (volume) growth\nbubble = Korea exports 2025, colour = Korea import share; * = re-export hub; MMR omitted")
plt.colorbar(sc, label="Korea share of imports (%)")
plt.tight_layout()
plt.savefig(FIG / "fig3_market_size_vs_volume_growth.png", dpi=150)
plt.close()
hs_pv = []
for hs, grp in im[im.partner == "WLD"].groupby("hs"):
    t = grp[grp.iso3.isin([i for i in mkt.index if mkt.loc[i, "latest_year"] == 2025])]
    t = t.groupby("year").agg(v=("value_usd", "sum"), kg=("net_kg", "sum"))
    hs_pv.append({"hs": HS_LABEL[hs], "value_cagr_20_25": cagr(t.v[2020], t.v[2025], 5),
                  "volume_cagr_20_25": cagr(t.kg[2020], t.kg[2025], 5),
                  "value_yoy_25": t.v[2025] / t.v[2024] - 1, "volume_yoy_25": t.kg[2025] / t.kg[2024] - 1})
md(pd.DataFrame(hs_pv).set_index("hs"), "t10_category_price_vs_volume", floatfmt=".3f")

# ---------- 7. Robustness variant: volume growth, hubs excluded ----------
f2 = f.join(pv[["volume_cagr_5y"]])
f2 = f2[~f2.index.isin(HUBS)]
features2 = dict(features)
features2["Market growth"] = [("volume_cagr_5y", 1, None), ("gdp_growth_avg_21_25", 1, None),
                              ("hh_cons_pc_cagr_19_24", 1, None)]
p2 = pd.DataFrame(index=f2.index)
for p, cols in features2.items():
    p2[p] = pd.concat([norm(f2[c], d, t) for c, d, t in cols], axis=1).mean(axis=1, skipna=True)
p2 = p2.dropna(thresh=3).fillna(p2.median())
p2["score"] = (p2[W0.index] * W0).sum(axis=1) * 100
t3a = pd.Series(0, index=p2.index, dtype=float)
for w in rng.dirichlet(np.ones(len(W0)), size=N):
    t3a[((p2[W0.index] * w).sum(axis=1)).nlargest(3).index] += 1
p2["top3_prob_random_weights"] = t3a / N
t3b = pd.Series(0, index=p2.index, dtype=float)
for _ in range(N):
    w = W0 * rng.uniform(0.8, 1.2, size=len(W0))
    t3b[((p2[W0.index] * (w / w.sum())).sum(axis=1)).nlargest(3).index] += 1
p2["top3_probability"] = t3b / N
p2 = p2.sort_values("score", ascending=False)
md(p2, "t11_screening_volume_no_hubs", floatfmt=".3f")

cmp = pd.DataFrame({
    "Naive (nominal US$, hubs kept)": pillars.top3_prob_random_weights,
    "Corrected (volume, hubs excluded)": p2.top3_prob_random_weights,
}).fillna(0)
cmp = cmp[(cmp > 0.02).any(axis=1)].sort_values("Corrected (volume, hubs excluded)")
ax = cmp.plot.barh(figsize=(8, 5.5))
ax.set_title("P(TOP3) under random weights: naive vs corrected data treatment")
ax.set_xlabel("probability of ranking in TOP3 (5,000 Dirichlet weight draws)")
ax.set_ylabel("")
plt.tight_layout()
plt.savefig(FIG / "fig5_top3_sensitivity.png", dpi=150)
plt.close()
print("done")
