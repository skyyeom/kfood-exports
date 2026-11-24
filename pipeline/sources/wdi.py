"""World Bank WDI indicators, including the Logistics Performance Index (keyless)."""

import json

import pandas as pd

from pipeline.config import CANDIDATES, NOT_IN_WORLD_BANK, WDI

URL = "https://api.worldbank.org/v2/country/{countries}/indicator/{code}"


class WdiSource:
    name, table = "wdi", "country_indicators"

    def __init__(
        self, countries: list[str] | None = None, indicators: dict[str, str] | None = None, years: str = "2012:2030"
    ):
        self.countries = countries or [c for c in CANDIDATES if c not in NOT_IN_WORLD_BANK]
        self.indicators = indicators or {code: name for code, (name, _) in WDI.items()}
        self.years = years

    def fetch(self, http) -> pd.DataFrame:
        rows = []
        for code, indicator in self.indicators.items():
            url = URL.format(countries=";".join(self.countries), code=code)
            meta, data = json.loads(http.get(url, params={"format": "json", "date": self.years, "per_page": 20000}))
            if meta["pages"] > 1:
                raise RuntimeError(f"WDI {code}: more than one page; raise per_page")
            rows += [
                {
                    "source": self.name,
                    "iso3": d["countryiso3code"],
                    "indicator": indicator,
                    "year": int(d["date"]),
                    "value": d["value"],
                    "unit": WDI.get(code, (None, None))[1],
                    "source_code": code,
                    "imputed": False,
                }
                for d in data or []
                if d["value"] is not None
            ]
        return pd.DataFrame(rows)
