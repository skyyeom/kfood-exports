"""World Bank commodity prices (Pink Sheet), monthly. The workbook URL changes with each release, so it is
discovered from the commodity-markets page on every run."""

import io
import re

import openpyxl
import pandas as pd

PAGE = "https://www.worldbank.org/en/research/commodity-markets"
WORKBOOK_LINK = re.compile(rb'https://thedocs\.worldbank\.org/[^"\']*CMO-Historical-Data-Monthly\.xlsx')
SHEET = "Monthly Prices"
COMMODITIES = {"Cocoa": "cocoa", "Sugar, world": "sugar_world", "Wheat, US HRW": "wheat_us_hrw", "Palm oil": "palm_oil"}


class PinkSheetSource:
    name, table = "pinksheet", "commodity_prices"

    def fetch(self, http) -> pd.DataFrame:
        link = WORKBOOK_LINK.search(http.get(PAGE))
        if not link:
            raise RuntimeError(f"No monthly Pink Sheet workbook link found on {PAGE}")
        ws = openpyxl.load_workbook(io.BytesIO(http.get(link.group().decode())), read_only=True, data_only=True)[SHEET]
        rows = list(ws.iter_rows(values_only=True))
        header = next(i for i, r in enumerate(rows) if any(isinstance(c, str) and c.strip() == "Cocoa" for c in r))
        names = [n.strip() if isinstance(n, str) else n for n in rows[header]]
        units = [str(u or "").strip().strip("()").replace("$", "USD") or None for u in rows[header + 1]]
        cols = {COMMODITIES[n]: (j, units[j]) for j, n in enumerate(names) if n in COMMODITIES}
        if len(cols) < len(COMMODITIES):
            raise RuntimeError(f"Pink Sheet columns missing: {set(COMMODITIES.values()) - set(cols)}")
        out = []
        for r in rows[header + 2 :]:
            if not (isinstance(r[0], str) and re.fullmatch(r"\d{4}M\d{2}", r[0])):
                continue
            month = f"{r[0][:4]}-{r[0][5:]}"
            out += [
                {"source": self.name, "commodity": c, "month": month, "price": float(r[j]), "unit": unit}
                for c, (j, unit) in cols.items()
                if isinstance(r[j], int | float)
            ]
        return pd.DataFrame(out)
