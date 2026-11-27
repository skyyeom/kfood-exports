"""Daily USD exchange rates from open.er-api.com (keyless; attribution required in the UI)."""

import json
from datetime import UTC, datetime

import pandas as pd

URL = "https://open.er-api.com/v6/latest/USD"


class FxSource:
    name, table = "fx", "fx_rates"

    def fetch(self, http) -> pd.DataFrame:
        body = json.loads(http.get(URL))
        if body.get("result") != "success":
            raise RuntimeError(f"open.er-api: {body.get('error-type', body.get('result'))}")
        day = datetime.fromtimestamp(body["time_last_update_unix"], UTC).date().isoformat()
        return pd.DataFrame(
            [
                {"source": self.name, "date": day, "base": body["base_code"], "quote": q, "rate": r}
                for q, r in body["rates"].items()
            ]
        )
