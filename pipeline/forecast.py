"""Score history and forecasts (engineering plan §8).

- history: score each past year using only the data known by then, so the trend shows how the ranking moved.
- forecast_series: per series, three simple models compete ("no change", "drift" = straight-line trend,
  "compound growth" = log-linear); the one with the lowest rolling-origin backtest error wins. With ~10 annual
  points per series, richer models would overfit (decision D19).
- project: forecast each country's score from its own score history with the winning model; Monte Carlo draws of
  each country's backtest error give P(TOP3) per future year.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from pipeline.config import HS
from pipeline.indicators import build_features, screen

MODELS = ("no change", "drift", "damped drift", "compound growth")  # tie → the earlier (simpler) model wins
SCORE_MODELS = ("no change", "drift", "damped drift")  # scores are a bounded 0-100 index: no compounding
DAMPING = 0.8  # damped drift: each further year adds 80% of the previous year's trend
Z80 = 1.2816  # 80% interval
DEFAULT_SIGMA = 0.2  # log-scale error assumed for series too short to backtest


def _predict(model: str, years: list[int], values: list[float], targets: list[int]) -> list[float] | None:
    last_y, last_v = years[-1], values[-1]
    if model == "no change":
        return [last_v] * len(targets)
    if model in ("drift", "damped drift"):
        slope = (values[-1] - values[0]) / (years[-1] - years[0])
        if model == "drift":
            return [max(0.0, last_v + slope * (t - last_y)) for t in targets]
        return [max(0.0, last_v + slope * sum(DAMPING**k for k in range(1, t - last_y + 1))) for t in targets]
    window = [(y, v) for y, v in zip(years, values, strict=True)][-6:]
    if len(window) < 3 or any(v <= 0 for _, v in window):
        return None  # compound growth needs positive values
    b1, b0 = np.polyfit([y for y, _ in window], np.log([v for _, v in window]), 1)
    return [float(math.exp(b0 + b1 * t)) for t in targets]


def _log_error(pred: float, actual: float) -> float:
    return math.log((max(pred, 0.0) + 1.0) / (actual + 1.0))


def forecast_series(
    years: list[int], values: list[float], targets: list[int], models: tuple[str, ...] = MODELS
) -> dict:
    """Forecast one annual series: the model with the lowest backtest error, with an 80% interval."""
    years, values = list(map(int, years)), list(map(float, values))
    errors = {m: [] for m in models}
    for origin in range(3, len(values)):  # rolling origin: fit on [:origin], test up to 3 years ahead
        for step in range(origin, min(origin + 3, len(values))):
            for m in models:
                pred = _predict(m, years[:origin], values[:origin], [years[step]])
                if pred is not None:
                    errors[m].append(_log_error(pred[0], values[step]))
    scored = {m: float(np.mean(np.abs(e))) for m, e in errors.items() if e}
    model = min(scored, key=lambda m: (round(scored[m], 12), models.index(m))) if scored else models[0]
    point = _predict(model, years, values, targets) or _predict("no change", years, values, targets)
    sigma = float(np.sqrt(np.mean(np.square(errors[model])))) if errors[model] else DEFAULT_SIGMA
    steps = [t - years[-1] for t in targets]
    return {
        "model": model,
        "point": point,
        "low": [p * math.exp(-Z80 * sigma * math.sqrt(h)) for p, h in zip(point, steps, strict=True)],
        "high": [p * math.exp(Z80 * sigma * math.sqrt(h)) for p, h in zip(point, steps, strict=True)],
        "sigma": sigma,
        "backtest_error": scored.get(model),
        "naive_error": scored.get("no change"),
    }


def _as_of(trade: pd.DataFrame, indicators: pd.DataFrame, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    annual = trade[trade.freq == "A"]
    return annual[annual.period.astype(int) <= year], indicators[indicators.year <= year]


def history(trade: pd.DataFrame, indicators: pd.DataFrame, years: list[int], hs: list[str] = HS) -> pd.DataFrame:
    """Score and rank for each past year, each computed only from data up to that year."""
    out = []
    for year in years:
        ranked = screen(build_features(*_as_of(trade, indicators, year), hs=hs), draws=1)
        out.append(
            pd.DataFrame(
                {
                    "year": year,
                    "iso3": ranked.index,
                    "score": ranked.score.to_numpy(),
                    "rank": range(1, len(ranked) + 1),
                }
            )
        )
    return pd.concat(out, ignore_index=True)


def _past(trade: pd.DataFrame, indicators: pd.DataFrame, hs: list[str] = HS) -> pd.DataFrame:
    """Score history for the latest 6 years."""
    last = int(trade[trade.freq == "A"].period.astype(int).max())
    return history(trade, indicators, list(range(last - 5, last + 1)), hs=hs)


def _score_forecasts(past: pd.DataFrame, years: list[int]) -> dict:
    """Forecast each currently scored country's score from its own score history."""
    current = past[past.year == past.year.max()].iso3
    forecasts = {}
    for iso in current:
        mine = past[past.iso3 == iso].sort_values("year")
        forecasts[iso] = forecast_series(mine.year.tolist(), mine.score.tolist(), years, models=SCORE_MODELS)
    return forecasts


def project(
    trade: pd.DataFrame,
    indicators: pd.DataFrame,
    years: list[int],
    draws: int = 2000,
    seed: int = 42,
    past: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Projected score (with 80% interval) and rank per future year, and P(TOP3) across forecast-error draws.

    Scores, not raw data, are forecast: re-scoring forecast data would shift the 5-year CAGR base years and move
    markets by many places without any new information.
    """
    fc = _score_forecasts(_past(trade, indicators) if past is None else past, years)
    isos = list(fc)
    point = np.array([[min(100.0, fc[i]["point"][k]) for k in range(len(years))] for i in isos])
    if not isos:
        return pd.DataFrame(columns=["year", "iso3", "score", "low", "high", "rank", "p_top3", "model"])
    sigma = np.array([fc[i]["sigma"] for i in isos])[:, None]
    steps = np.array(years)[None, :] - (min(years) - 1)
    rng = np.random.default_rng(seed)
    draws_scores = point[None] * np.exp(rng.normal(size=(draws, *point.shape)) * sigma[None] * np.sqrt(steps)[None])
    top3 = np.argsort(-draws_scores, axis=1)[:, :3, :]  # draws x 3 x years
    p_top3 = np.stack(
        [np.bincount(top3[:, :, k].ravel(), minlength=len(isos)) / draws for k in range(len(years))], axis=1
    )
    out = []
    for k, year in enumerate(years):
        order = np.argsort(-point[:, k], kind="stable")
        out.append(
            pd.DataFrame(
                {
                    "year": year,
                    "iso3": [isos[j] for j in order],
                    "score": point[order, k],
                    "low": [fc[isos[j]]["low"][k] for j in order],
                    "high": [min(100.0, fc[isos[j]]["high"][k]) for j in order],
                    "rank": range(1, len(isos) + 1),
                    "p_top3": p_top3[order, k],
                    "model": [fc[isos[j]]["model"] for j in order],
                }
            )
        )
    return pd.concat(out, ignore_index=True)


def holdout_check(trade: pd.DataFrame, indicators: pd.DataFrame, past: pd.DataFrame | None = None) -> dict:
    """Out-of-sample test: forecast the latest year using only the five years before it, then compare."""
    past = _past(trade, indicators) if past is None else past
    last = int(past.year.max())
    train, actual = past[past.year < last], past[past.year == last].set_index("iso3").score
    predicted, naive = {}, {}
    for iso in actual.index:
        mine = train[train.iso3 == iso].sort_values("year")
        if len(mine):
            f = forecast_series(mine.year.tolist(), mine.score.tolist(), [last], models=SCORE_MODELS)
            predicted[iso], naive[iso] = f["point"][0], mine.score.iloc[-1]
    predicted, naive = pd.Series(predicted), pd.Series(naive)
    err = (predicted - actual[predicted.index]).abs()
    return {
        "year": last,
        "trained_on": f"{last - 5}–{last - 1}",
        "predicted_top3": predicted.nlargest(3).index.tolist(),
        "actual_top3": actual.nlargest(3).index.tolist(),
        "model_mae": float(err.mean()),
        "no_change_mae": float((naive - actual[naive.index]).abs().mean()),
    }


def model_report(
    trade: pd.DataFrame, indicators: pd.DataFrame, years: list[int], past: pd.DataFrame | None = None
) -> dict:
    """Which model each country's score forecast uses, and how forecasts did when tested on earlier years."""
    fc = _score_forecasts(_past(trade, indicators) if past is None else past, years)
    tested = [f for f in fc.values() if f["backtest_error"] is not None and f["naive_error"] is not None]
    models = pd.Series([f["model"] for f in fc.values()]).value_counts()
    return {
        "countries": len(fc),
        "models": {str(k): int(v) for k, v in models.items()},
        "median_backtest_error_pct": (
            float((np.exp(np.median([f["backtest_error"] for f in tested])) - 1) * 100) if tested else None
        ),
    }


def trends(
    trade: pd.DataFrame, indicators: pd.DataFrame, horizon: int = 3, draws: int = 2000, hs: list[str] = HS
) -> dict:
    """Score history, forecast and out-of-sample check, as one JSON-ready payload for the dashboard."""
    from pipeline.config import CANDIDATES

    last = int(trade[trade.freq == "A"].period.astype(int).max())
    future = list(range(last + 1, last + horizon + 1))

    def rows(df: pd.DataFrame) -> list[dict]:
        return [r | {"name": CANDIDATES[r["iso3"]][1]} for r in df.to_dict(orient="records")]

    past = _past(trade, indicators, hs=hs)
    return {
        "history": rows(past),
        "forecast": rows(project(trade, indicators, future, draws=draws, past=past)),
        "holdout": holdout_check(trade, indicators, past=past),
        "models": model_report(trade, indicators, future, past=past),
        "method": (
            "Each market's score is forecast from its own 6-year score history. Three models compete "
            "(no change, straight-line trend, damped trend); the one that best forecast earlier years wins. "
            f"P(TOP3) comes from {draws:,} simulations of each market's own forecast error."
        ),
    }
