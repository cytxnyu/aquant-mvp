from __future__ import annotations

import pandas as pd

from aquant_mvp.config import StrategyConfig


def score_factors(factor_panel: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Rank-normalize factors cross-sectionally and combine them into scores."""
    known = [name for name in weights if name in factor_panel.columns]
    if not known:
        raise ValueError("No configured factor exists in the factor panel")

    scores = []
    for date, daily in factor_panel.groupby(level="date", sort=True):
        daily_symbols = daily.droplevel("date")
        score = pd.Series(0.0, index=daily_symbols.index, name="score")
        for name in known:
            ranked = daily_symbols[name].rank(pct=True, method="average")
            score = score.add(ranked.fillna(0.0) * float(weights[name]), fill_value=0.0)
        daily_score = pd.DataFrame({"score": score, "close": daily_symbols["close"], "amount": daily_symbols["amount"]})
        daily_score["date"] = date
        scores.append(daily_score.reset_index())

    out = pd.concat(scores, ignore_index=True)
    return out.set_index(["date", "symbol"]).sort_index()


def build_rebalance_targets(scores: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    """Select top-N stocks on each rebalance date and assign equal target weights."""
    dates = pd.DatetimeIndex(scores.index.get_level_values("date").unique()).sort_values()
    if dates.empty:
        raise ValueError("Score panel has no dates")

    calendar = pd.Series(dates, index=dates)
    rebalance_dates = calendar.resample(config.rebalance).last().dropna().tolist()
    target_rows: list[pd.Series] = []
    previous = pd.Series(0.0, index=scores.index.get_level_values("symbol").unique())
    for date in rebalance_dates:
        try:
            daily = scores.xs(date, level="date").copy()
        except KeyError:
            continue
        daily = daily.dropna(subset=["score"])
        if config.min_amount > 0:
            daily = daily[daily["amount"] >= config.min_amount]
        if daily.empty:
            continue
        picked = daily.sort_values("score", ascending=False).head(config.top_n)
        weight = min(1.0 / len(picked), config.max_single_weight)
        target = pd.Series(0.0, index=previous.index)
        for symbol in picked.index.astype(str):
            target.loc[symbol.zfill(6)] = weight
        turnover = float((target - previous).abs().sum())
        if 0 < config.max_turnover < turnover:
            scale = config.max_turnover / turnover
            target = previous + (target - previous) * scale
        target.name = date
        target_rows.append(target)
        previous = target

    if not target_rows:
        raise ValueError("No rebalance target generated. Try a longer period or lower filters.")

    return pd.DataFrame(target_rows).fillna(0.0).sort_index()
