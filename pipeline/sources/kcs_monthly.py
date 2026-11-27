"""관세청 monthly trade statistics via data.go.kr (free key in KCS_API_KEY). Three APIs, one key:

- kcs_monthly  품목별 국가별 수출입실적: Korea exports by HS6 line × destination, plus a world total per line
- kcs_items    품목별 수출입실적: Korea's world exports by HS10 product line (product-level fit, cross-check)
- kcs_nations  국가별 수출입실적: Korea's total exports (all goods) to each candidate, for context

Each API allows at most one calendar year per call and signals errors with HTTP 200 + resultCode != "00".
Amounts are US$ (exports FOB), weights kg. 관세청 revises earlier months around the 15th, so every run re-pulls
all years and the store records what changed.
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date

import pandas as pd

from pipeline.config import HS, ISO2
from pipeline.sources.base import SkipSource

BASE = "https://apis.data.go.kr/1220000"
MONTH = re.compile(r"^(\d{4})\.(\d{2})$")
ISO3 = {v: k for k, v in ISO2.items()}


class _KcsSource:
    name = table = ""
    path = ""

    def __init__(self, api_key: str | None = None, years: list[int] | None = None, hs: list[str] | None = None):
        self.api_key = api_key if api_key is not None else os.environ.get("KCS_API_KEY", "")
        self.years = years or list(range(2015, date.today().year + 1))
        self.hs = hs or HS

    def _year(self, http, year: int, **params) -> list[tuple[str, dict]]:
        """(YYYYMM, item) for every monthly item in one calendar year; the grand-total row (총계) is dropped."""
        if not self.api_key:
            raise SkipSource("KCS_API_KEY is not set; register for the 관세청 API on data.go.kr")
        body = http.get(
            f"{BASE}/{self.path}",
            params={"serviceKey": self.api_key, "strtYymm": f"{year}01", "endYymm": f"{year}12", **params},
        )
        root = ET.fromstring(body)
        if (code := root.findtext("header/resultCode")) != "00":
            raise RuntimeError(f"관세청 API error {code}: {root.findtext('header/resultMsg')}")
        out = []
        for item in root.iter("item"):
            fields = {child.tag: (child.text or "") for child in item}
            if month := MONTH.match(fields.get("year", "")):
                out.append((month[1] + month[2], fields))
        return out

    def _row(self, partner: str, hs: str, period: str, value: float, kg: float | None) -> dict:
        return {
            "source": self.name,
            "reporter_iso3": "KOR",
            "partner_iso3": partner,
            "flow": "X",
            "hs": hs,
            "freq": "M",
            "period": period,
            "value_usd": value,
            "net_kg": kg,
            "imputed": False,
        }


class KcsMonthlySource(_KcsSource):
    name, table, path = "kcs_monthly", "trade_flows", "nitemtrade/getNitemtradeList"

    def fetch(self, http) -> pd.DataFrame:
        rows, world = [], defaultdict(lambda: [0.0, 0.0])
        for heading in self.hs:
            for year in self.years:
                for period, item in self._year(http, year, hsSgn=heading):
                    if item.get("hsCd", "-") == "-":
                        continue
                    value, kg = float(item["expDlr"]), float(item["expWgt"])
                    world[(item["hsCd"], period)][0] += value
                    world[(item["hsCd"], period)][1] += kg
                    if item["statCd"] in ISO3:
                        rows.append(self._row(ISO3[item["statCd"]], item["hsCd"], period, value, kg))
        rows += [self._row("WLD", hs, period, v, kg) for (hs, period), (v, kg) in world.items()]
        return pd.DataFrame(rows)


class KcsItemsSource(_KcsSource):
    name, table, path = "kcs_items", "trade_flows", "Itemtrade/getItemtradeList"

    def fetch(self, http) -> pd.DataFrame:
        return pd.DataFrame(
            [
                self._row("WLD", item["hsCode"], period, float(item["expDlr"]), float(item["expWgt"]))
                for heading in self.hs
                for year in self.years
                for period, item in self._year(http, year, hsSgn=heading)
                if item.get("hsCode", "-") != "-"
            ]
        )


class KcsNationsSource(_KcsSource):
    name, table, path = "kcs_nations", "trade_flows", "nationtrade/getNationtradeList"

    def fetch(self, http) -> pd.DataFrame:
        return pd.DataFrame(
            [
                self._row(ISO3[item["statCd"]], "TOTAL", period, float(item["expDlr"]), None)
                for year in self.years
                for period, item in self._year(http, year)
                if item.get("statCd") in ISO3
            ]
        )
