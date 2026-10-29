"""Collect raw data for the WellGTM market & data analysis (exploratory, not product code).

Sources (no API keys required):
- UN Comtrade public preview API: annual imports by candidate country (from World / from Korea)
  and Korea's reported exports to candidate countries, HS 1704/1806/1905/2105.
- World Bank WDI API: macro indicators + Logistics Performance Index.

Usage: .venv/bin/python analysis/collect.py
Output: analysis/data/*.csv (raw pulls with retrieval timestamp)
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

OUT = Path(__file__).parent / "data"
OUT.mkdir(parents=True, exist_ok=True)
RETRIEVED_AT = datetime.now(UTC).isoformat(timespec="seconds")

# ISO3 -> (UN M49 code used by Comtrade, name)
CANDIDATES: dict[str, tuple[int, str]] = {
    "USA": (842, "United States"),
    "CAN": (124, "Canada"),
    "MEX": (484, "Mexico"),
    "BRA": (76, "Brazil"),
    "GBR": (826, "United Kingdom"),
    "DEU": (276, "Germany"),
    "FRA": (251, "France"),
    "NLD": (528, "Netherlands"),
    "POL": (616, "Poland"),
    "CHN": (156, "China"),
    "JPN": (392, "Japan"),
    "TWN": (490, "Taiwan"),
    "HKG": (344, "Hong Kong"),
    "MNG": (496, "Mongolia"),
    "VNM": (704, "Vietnam"),
    "THA": (764, "Thailand"),
    "IDN": (360, "Indonesia"),
    "PHL": (608, "Philippines"),
    "MYS": (458, "Malaysia"),
    "SGP": (702, "Singapore"),
    "KHM": (116, "Cambodia"),
    "MMR": (104, "Myanmar"),
    "IND": (699, "India"),
    "PAK": (586, "Pakistan"),
    "KAZ": (398, "Kazakhstan"),
    "AUS": (36, "Australia"),
    "NZL": (554, "New Zealand"),
    "ARE": (784, "United Arab Emirates"),
    "SAU": (682, "Saudi Arabia"),
    "RUS": (643, "Russia"),
}
HS = ["1704", "1806", "1905", "2105"]
YEARS = list(range(2015, 2026))
KOREA = 410
COMTRADE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"


def comtrade(params: dict) -> list[dict]:
    for attempt in range(5):
        r = requests.get(COMTRADE, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
        body = r.json()
        if body.get("error"):
            raise RuntimeError(f"{params}: {body['error']}")
        rows = body.get("data", [])
        if len(rows) >= 500:
            raise RuntimeError(f"Preview row cap hit, split the query: {params}")
        return rows
    raise RuntimeError(f"Rate limited: {params}")


def collect_comtrade() -> None:
    m49_to_iso = {m49: iso for iso, (m49, _) in CANDIDATES.items()}
    reporters = ",".join(str(m) for iso, (m, _) in CANDIDATES.items() if iso != "TWN")
    partners = ",".join(str(m) for m, _ in CANDIDATES.values())
    imports, exports = [], []
    for year in YEARS:
        rows = comtrade(
            {"reporterCode": reporters, "period": year, "partnerCode": f"0,{KOREA}",
             "cmdCode": ",".join(HS), "flowCode": "M"}
        )
        for r in rows:
            imports.append({
                "iso3": m49_to_iso[r["reporterCode"]], "year": r["refYear"], "hs": r["cmdCode"],
                "partner": "WLD" if r["partnerCode"] == 0 else "KOR",
                "value_usd": r["primaryValue"], "net_kg": r.get("netWgt"),
            })
        time.sleep(1.5)
        rows = comtrade(
            {"reporterCode": KOREA, "period": year, "partnerCode": f"0,{partners}",
             "cmdCode": ",".join(HS), "flowCode": "X"}
        )
        for r in rows:
            exports.append({
                "iso3": "WLD" if r["partnerCode"] == 0 else m49_to_iso.get(r["partnerCode"], str(r["partnerCode"])),
                "year": r["refYear"], "hs": r["cmdCode"],
                "value_usd": r["primaryValue"], "net_kg": r.get("netWgt"),
            })
        print(f"comtrade {year}: imports={len(imports)} kr_exports={len(exports)}")
        time.sleep(1.5)
    for name, rows in (("imports", imports), ("kr_exports", exports)):
        df = pd.DataFrame(rows)
        df["source"] = "UN Comtrade (public preview API)"
        df["retrieved_at"] = RETRIEVED_AT
        df.to_csv(OUT / f"comtrade_{name}.csv", index=False)


WDI = {
    "NY.GDP.PCAP.CD": "gdp_per_capita_usd",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
    "SP.POP.TOTL": "population",
    "SP.URB.TOTL.IN.ZS": "urban_pct",
    "SP.POP.1564.TO.ZS": "pop_15_64_pct",
    "SP.POP.0014.TO.ZS": "pop_0_14_pct",
    "NE.CON.PRVT.PC.KD": "hh_consumption_pc_const_usd",
    "FP.CPI.TOTL.ZG": "inflation_pct",
    "LP.LPI.OVRL.XQ": "lpi_score",
}


def collect_wdi() -> None:
    isos = ";".join(i for i in CANDIDATES if i != "TWN")
    rows = []
    for code, name in WDI.items():
        url = f"https://api.worldbank.org/v2/country/{isos}/indicator/{code}"
        r = requests.get(url, params={"format": "json", "date": "2012:2025", "per_page": 2000}, timeout=60)
        r.raise_for_status()
        meta, data = r.json()
        for d in data or []:
            if d["value"] is not None:
                rows.append({"iso3": d["countryiso3code"], "year": int(d["date"]),
                             "indicator": name, "wdi_code": code, "value": d["value"]})
        print(f"wdi {code}: {len(data or [])} rows")
        time.sleep(0.5)
    df = pd.DataFrame(rows)
    df["source"] = "World Bank WDI API"
    df["retrieved_at"] = RETRIEVED_AT
    df.to_csv(OUT / "wdi.csv", index=False)


if __name__ == "__main__":
    collect_comtrade()
    collect_wdi()
