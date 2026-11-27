"""The exploratory analysis' raw pulls (analysis/data/), reshaped into the pipeline's tables."""

from pathlib import Path

import pandas as pd

ANALYSIS = Path(__file__).resolve().parents[1] / "analysis"


def load_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    imports = pd.read_csv(ANALYSIS / "data/comtrade_imports.csv", dtype={"hs": str})
    exports = pd.read_csv(ANALYSIS / "data/comtrade_kr_exports.csv", dtype={"hs": str})
    both = pd.concat([imports, exports], ignore_index=True)
    trade = pd.DataFrame(
        {
            "source": "comtrade",
            "reporter_iso3": pd.concat([imports.iso3, pd.Series("KOR", index=exports.index)], ignore_index=True),
            "partner_iso3": pd.concat([imports.partner, exports.iso3], ignore_index=True),
            "flow": ["M"] * len(imports) + ["X"] * len(exports),
            "hs": both.hs,
            "freq": "A",
            "period": both.year.astype(str),
            "value_usd": both.value_usd,
            "net_kg": both.net_kg,
            "imputed": False,
        }
    )
    wdi = pd.read_csv(ANALYSIS / "data/wdi.csv")
    indicators = pd.DataFrame(
        {
            "source": "wdi",
            "iso3": wdi.iso3,
            "indicator": wdi.indicator,
            "year": wdi.year,
            "value": wdi.value,
            "source_code": wdi.wdi_code,
            "imputed": False,
        }
    )
    return trade, indicators
