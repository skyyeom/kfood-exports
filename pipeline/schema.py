"""Row-level validation for each data table (see docs/data_dictionary.md). Rows that fail are dropped and counted."""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

from pipeline.db import DATA_TABLES

ISO3 = pa.Check.str_matches(r"^[A-Z]{3}$")
ISO_DATE = pa.Check.str_matches(r"^\d{4}-\d{2}-\d{2}$")
HS_CODE = pa.Check.str_matches(r"^\d{4}(\d{2})?(\d{4})?$")


def _key(*checks: pa.Check) -> pa.Column:
    return pa.Column(None, checks=list(checks), nullable=False, coerce=False)


def _value(*checks: pa.Check, nullable: bool = True) -> pa.Column:
    return pa.Column(None, checks=list(checks), nullable=nullable, required=False)


NON_NEGATIVE = pa.Check.ge(0)
POSITIVE = pa.Check.gt(0)

SCHEMAS = {
    "trade_flows": pa.DataFrameSchema(
        {
            "source": _key(),
            "reporter_iso3": _key(ISO3),
            "partner_iso3": _key(ISO3),
            "flow": _key(pa.Check.isin(["M", "X"])),
            "hs": _key(HS_CODE),
            "freq": _key(pa.Check.isin(["A", "M"])),
            "period": _key(pa.Check.str_matches(r"^\d{4}(\d{2})?$")),
            "value_usd": _value(NON_NEGATIVE, nullable=False),
            "net_kg": _value(NON_NEGATIVE),
        }
    ),
    "country_indicators": pa.DataFrameSchema(
        {
            "source": _key(),
            "iso3": _key(ISO3),
            "indicator": _key(),
            "year": _key(pa.Check.in_range(1960, 2100)),
            "value": _value(nullable=False),
        }
    ),
    "tariffs": pa.DataFrameSchema(
        {
            "source": _key(),
            "importer_iso3": _key(ISO3),
            "hs": _key(HS_CODE),
            "rate_type": _key(pa.Check.isin(["mfn", "pref", "additional"])),
            "agreement": _key(),
            "effective_from": _key(ISO_DATE),
            "effective_to": _value(ISO_DATE),
            "rate_pct": _value(pa.Check.in_range(0, 1000), nullable=False),
        }
    ),
    "fx_rates": pa.DataFrameSchema(
        {
            "source": _key(),
            "date": _key(ISO_DATE),
            "base": _key(ISO3),
            "quote": _key(ISO3),
            "rate": _value(POSITIVE, nullable=False),
        }
    ),
    "commodity_prices": pa.DataFrameSchema(
        {
            "source": _key(),
            "commodity": _key(),
            "month": _key(pa.Check.str_matches(r"^\d{4}-\d{2}$")),
            "price": _value(POSITIVE, nullable=False),
        }
    ),
}


def _cast(value, to: type):
    """Cast to the column's Python type; leave the value as is when it can't be cast, so a check rejects the row."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return to(value)
    except (TypeError, ValueError):
        return value


def coerce(table: str, df: pd.DataFrame) -> pd.DataFrame:
    t = DATA_TABLES[table]
    return pd.DataFrame(
        {c: [_cast(v, t.c[c].type.python_type) for v in df[c]] if c in t.c else df[c] for c in df.columns},
        index=df.index,
    )


def validate(table: str, df: pd.DataFrame) -> tuple[pd.DataFrame, int, list[str]]:
    """Return (valid rows, number of invalid rows, up to 5 example problems).

    Raises ValueError when the payload as a whole is unusable (e.g. a key column is missing).
    """
    if df.empty:
        return df, 0, []
    df = coerce(table, df)
    try:
        SCHEMAS[table].validate(df, lazy=True)
        return df, 0, []
    except pa.errors.SchemaErrors as e:
        cases = e.failure_cases
        if cases["index"].isna().any():
            whole = cases[cases["index"].isna()]
            raise ValueError(f"{table} payload rejected: {whole[['column', 'check']].to_dict(orient='records')}") from e
        bad = sorted(set(cases["index"].astype(int)))
        examples = [f"row {r.index}: {r.column} {r.check} (got {r.failure_case!r})" for r in cases.head(5).itertuples()]
        return df.drop(index=bad), len(bad), examples
