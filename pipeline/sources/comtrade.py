"""UN Comtrade annual trade: candidate imports (from World, from Korea) and Korea-reported exports.

Keyless preview API by default (500-row cap per call). Set COMTRADE_API_KEY for the free-key endpoint.
"""

import json
import os
from datetime import date

import pandas as pd

from pipeline.config import CANDIDATES, HS, KOREA_M49, NOT_IN_WORLD_BANK

PREVIEW = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
KEYED = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
PREVIEW_ROW_CAP = 500


class ComtradeSource:
    name, table = "comtrade", "trade_flows"

    def __init__(
        self,
        countries: list[str] | None = None,
        years: list[int] | None = None,
        hs: list[str] | None = None,
        api_key: str | None = None,
    ):
        self.countries = countries or list(CANDIDATES)
        self.years = years or list(range(2015, date.today().year))
        self.hs = hs or HS
        self.api_key = api_key if api_key is not None else os.environ.get("COMTRADE_API_KEY")

    def _get(self, http, params: dict) -> list[dict]:
        url, headers = (KEYED, {"Ocp-Apim-Subscription-Key": self.api_key}) if self.api_key else (PREVIEW, None)
        body = json.loads(http.get(url, params=params, headers=headers))
        if body.get("error"):
            raise RuntimeError(f"Comtrade {params}: {body['error']}")
        rows = body.get("data") or []
        if not self.api_key and len(rows) >= PREVIEW_ROW_CAP:
            raise RuntimeError(f"Comtrade preview row cap hit, split the query: {params}")
        return rows

    def fetch(self, http) -> pd.DataFrame:
        m49_to_iso = {m49: iso for iso, (m49, _) in CANDIDATES.items()}
        reporters = ",".join(str(CANDIDATES[c][0]) for c in self.countries if c not in NOT_IN_WORLD_BANK)
        partners = ",".join(str(CANDIDATES[c][0]) for c in self.countries)
        cmd = ",".join(self.hs)
        out = []
        for year in self.years:
            for r in self._get(
                http,
                {
                    "reporterCode": reporters,
                    "period": year,
                    "partnerCode": f"0,{KOREA_M49}",
                    "cmdCode": cmd,
                    "flowCode": "M",
                },
            ):
                out.append(self._row(r, m49_to_iso[r["reporterCode"]], "WLD" if r["partnerCode"] == 0 else "KOR"))
            for r in self._get(
                http,
                {
                    "reporterCode": KOREA_M49,
                    "period": year,
                    "partnerCode": f"0,{partners}",
                    "cmdCode": cmd,
                    "flowCode": "X",
                },
            ):
                partner = "WLD" if r["partnerCode"] == 0 else m49_to_iso.get(r["partnerCode"], str(r["partnerCode"]))
                out.append(self._row(r, "KOR", partner))
        return pd.DataFrame(out)

    def _row(self, r: dict, reporter: str, partner: str) -> dict:
        return {
            "source": self.name,
            "reporter_iso3": reporter,
            "partner_iso3": partner,
            "flow": r["flowCode"],
            "hs": r["cmdCode"],
            "freq": "A",
            "period": str(r["refYear"]),
            "value_usd": r["primaryValue"],
            "net_kg": r.get("netWgt"),
            "imputed": False,
        }
