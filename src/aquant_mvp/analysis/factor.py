from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FactorAnalysisResult:
    ic_summary: pd.DataFrame
    ic_series: pd.DataFrame
    quantile_returns: pd.DataFrame
    coverage: pd.DataFrame


def analyze_factors(
    factors: pd.DataFrame,
    labels: pd.DataFrame,
    factor_columns: list[str],
    label_column: str,
    quantiles: int = 5,
) -> FactorAnalysisResult:
    joined = factors[factor_columns].join(labels[[label_column]], how="inner")
    ic_series = _build_ic_series(joined, factor_columns, label_column)
    quantile_returns = _build_quantile_returns(joined, factor_columns, label_column, quantiles)
    ic_rows = _summarize_ic(ic_series, factor_columns)
    coverage_rows = _build_coverage(joined, factor_columns, label_column)

    return FactorAnalysisResult(
        ic_summary=pd.DataFrame(ic_rows),
        ic_series=ic_series,
        quantile_returns=quantile_returns,
        coverage=pd.DataFrame(coverage_rows),
    )


def _build_ic_series(joined: pd.DataFrame, factor_columns: list[str], label_column: str) -> pd.DataFrame:
    wide = joined.reset_index()
    long = wide.melt(
        id_vars=["date", "symbol", label_column],
        value_vars=factor_columns,
        var_name="factor",
        value_name="value",
    ).dropna(subset=["value", label_column])
    if long.empty:
        return pd.DataFrame(columns=["date", "factor", "ic", "rank_ic"])

    ic = _grouped_corr(long, "value", label_column).rename("ic")
    long["value_rank"] = long.groupby(["date", "factor"], sort=False)["value"].rank(method="average")
    long["label_rank"] = long.groupby(["date", "factor"], sort=False)[label_column].rank(method="average")
    rank_ic = _grouped_corr(long, "value_rank", "label_rank").rename("rank_ic")
    out = pd.concat([ic, rank_ic], axis=1).replace([np.inf, -np.inf], np.nan).dropna().reset_index()
    return out[["date", "factor", "ic", "rank_ic"]]


def _grouped_corr(frame: pd.DataFrame, x_column: str, y_column: str) -> pd.Series:
    work = frame[["date", "factor", x_column, y_column]].copy()
    work["xy"] = work[x_column] * work[y_column]
    work["x2"] = work[x_column] * work[x_column]
    work["y2"] = work[y_column] * work[y_column]
    grouped = work.groupby(["date", "factor"], sort=False).agg(
        n=(x_column, "size"),
        sx=(x_column, "sum"),
        sy=(y_column, "sum"),
        sxy=("xy", "sum"),
        sx2=("x2", "sum"),
        sy2=("y2", "sum"),
    )
    numerator = grouped["n"] * grouped["sxy"] - grouped["sx"] * grouped["sy"]
    x_var_term = (grouped["n"] * grouped["sx2"] - grouped["sx"] * grouped["sx"]).clip(lower=0)
    y_var_term = (grouped["n"] * grouped["sy2"] - grouped["sy"] * grouped["sy"]).clip(lower=0)
    denominator = np.sqrt(x_var_term * y_var_term)
    return (numerator / denominator.where(denominator != 0)).dropna()


def _build_quantile_returns(
    joined: pd.DataFrame,
    factor_columns: list[str],
    label_column: str,
    quantiles: int,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for date, daily in joined.groupby(level="date", sort=True):
        daily = daily.droplevel("date")
        label = daily[label_column].dropna()
        if label.empty:
            continue

        values = daily.loc[label.index, factor_columns]
        counts = values.count()
        usable_columns = counts[counts >= 2].index
        if len(usable_columns) == 0:
            continue

        ranked = values[usable_columns].rank(method="first")
        buckets = np.floor((ranked - 1).div(counts[usable_columns], axis=1) * quantiles) + 1
        buckets = buckets.clip(lower=1, upper=quantiles)
        long = buckets.stack().rename("quantile").reset_index()
        if long.empty:
            continue
        long.columns = ["symbol", "factor", "quantile"]
        long["mean_forward_return"] = long["symbol"].map(label)
        grouped = (
            long.dropna(subset=["mean_forward_return"])
            .groupby(["factor", "quantile"], sort=False)["mean_forward_return"]
            .mean()
            .reset_index()
        )
        grouped["date"] = date
        rows.append(grouped[["date", "factor", "quantile", "mean_forward_return"]])
    if not rows:
        return pd.DataFrame(columns=["date", "factor", "quantile", "mean_forward_return"])
    out = pd.concat(rows, ignore_index=True)
    out["quantile"] = out["quantile"].astype(int)
    return out


def _summarize_ic(ic_series: pd.DataFrame, factor_columns: list[str]) -> list[dict[str, object]]:
    if ic_series.empty:
        return [{"factor": factor, "ic_mean": 0.0, "rank_ic_mean": 0.0, "ic_ir": 0.0, "observations": 0} for factor in factor_columns]

    grouped = ic_series.groupby("factor", sort=False)
    summary = grouped.agg(ic_mean=("ic", "mean"), rank_ic_mean=("rank_ic", "mean"), observations=("ic", "size"))
    ic_std = grouped["ic"].std(ddof=0)
    summary["ic_ir"] = (summary["ic_mean"] / ic_std.replace(0, np.nan)).fillna(0.0)

    rows = []
    for factor in factor_columns:
        if factor not in summary.index:
            rows.append({"factor": factor, "ic_mean": 0.0, "rank_ic_mean": 0.0, "ic_ir": 0.0, "observations": 0})
        else:
            item = summary.loc[factor]
            rows.append(
                {
                    "factor": factor,
                    "ic_mean": float(item["ic_mean"]),
                    "rank_ic_mean": float(item["rank_ic_mean"]),
                    "ic_ir": float(item["ic_ir"]),
                    "observations": int(item["observations"]),
                }
            )
    return rows


def _build_coverage(joined: pd.DataFrame, factor_columns: list[str], label_column: str) -> list[dict[str, object]]:
    denominator = max(1, len(joined))
    label_valid = joined[label_column].notna()
    valid_counts = joined[factor_columns].notna().where(label_valid, False).sum()
    return [{"factor": factor, "coverage": float(valid_counts.get(factor, 0) / denominator)} for factor in factor_columns]


def _safe_qcut(values: pd.Series, quantiles: int) -> pd.Series | None:
    try:
        return pd.qcut(values.rank(method="first"), quantiles, labels=False, duplicates="drop") + 1
    except ValueError:
        return None

