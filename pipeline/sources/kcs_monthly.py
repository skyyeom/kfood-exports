"""관세청 monthly Korea exports by HS × country, via data.go.kr (free key in KCS_API_KEY).

The response parser is written once a real response has been recorded as a test fixture; until then a run with
a key fails loudly rather than guessing the format.
"""

import os

import pandas as pd

from pipeline.sources.base import SkipSource


class KcsMonthlySource:
    name, table = "kcs_monthly", "trade_flows"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else os.environ.get("KCS_API_KEY", "")

    def fetch(self, http) -> pd.DataFrame:
        if not self.api_key:
            raise SkipSource("KCS_API_KEY is not set; register for the 관세청 API on data.go.kr")
        raise NotImplementedError("Record a data.go.kr response as a fixture, then implement the parser")
