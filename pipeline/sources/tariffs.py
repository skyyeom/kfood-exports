"""Tariffs: WITS/TRAINS MFN simple averages per HS6 line, plus dated overrides from tariff_overrides.yaml.

Preferential (FTA) and additional duties come from the override file; WITS has no Korea-specific rows.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import yaml

from pipeline.config import CANDIDATES, HS6, wits_code
from pipeline.http import NotFound

URL = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/{code}/partner/000/product/{products}/year/{years}/datatype/reported"
OVERRIDES = Path(__file__).resolve().parents[1] / "tariff_overrides.yaml"


class TariffSource:
    name, table = "tariffs", "tariffs"

    def __init__(
        self, countries: list[str] | None = None, years: list[int] | None = None, overrides_file: Path = OVERRIDES
    ):
        self.countries = list(CANDIDATES) if countries is None else countries
        self.years = years or [2025, 2024, 2023, 2022]
        self.overrides_file = Path(overrides_file)

    def fetch(self, http) -> pd.DataFrame:
        products = ";".join(p for lines in HS6.values() for p in lines)
        rows = []
        for iso in self.countries:
            url = URL.format(code=f"{wits_code(iso):03d}", products=products, years=";".join(map(str, self.years)))
            try:
                body = http.get(url)
            except NotFound:  # WITS answers 404 for a reporter with no data in these years
                continue
            rows += self._latest_mfn(iso, url, body)
        return pd.DataFrame(rows + self._overrides())

    def _latest_mfn(self, iso: str, url: str, body: bytes) -> list[dict]:
        if body.lstrip().startswith(b"Not Found"):
            return []
        latest: dict[str, tuple[int, float]] = {}
        for series in ET.fromstring(body).iter():
            if not series.tag.endswith("Series"):
                continue
            hs = series.get("PRODUCTCODE")
            for obs in series:
                if obs.get("TARIFFTYPE") == "MFN" and obs.get("OBS_VALUE"):
                    year = int(obs.get("TIME_PERIOD"))
                    if hs not in latest or year > latest[hs][0]:
                        latest[hs] = (year, float(obs.get("OBS_VALUE")))
        return [
            {
                "source": "wits",
                "importer_iso3": iso,
                "hs": hs,
                "rate_type": "mfn",
                "agreement": "",
                "effective_from": f"{year}-01-01",
                "effective_to": None,
                "rate_pct": rate,
                "source_url": url,
            }
            for hs, (year, rate) in sorted(latest.items())
        ]

    def _overrides(self) -> list[dict]:
        if not self.overrides_file.exists():
            return []
        return [
            {
                "source": "override",
                "importer_iso3": o["importer_iso3"],
                "hs": hs,
                "rate_type": o["rate_type"],
                "agreement": o.get("agreement", ""),
                "effective_from": str(o["effective_from"]),
                "effective_to": str(o["effective_to"]) if o.get("effective_to") else None,
                "rate_pct": float(o["rate_pct"]),
                "source_url": o.get("source_url"),
            }
            for o in yaml.safe_load(self.overrides_file.read_text()) or []
            for hs in o["hs"]
        ]
