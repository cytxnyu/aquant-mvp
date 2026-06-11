from __future__ import annotations

from dataclasses import dataclass

import math

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
    ic_rows: list[dict[str, object]] = []
    quantile_rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []

    for factor in factor_columns:
        daily_ic = []
        for date, daily in joined[[factor, label_column]].dropna().groupby(level="date"):
            if daily[factor].nunique() < 2 or daily[label_column].nunique() < 2:
                continue
            ic = daily[factor].corr(daily[label_column], method="pearson")
            rank_ic = daily[factor].corr(daily[label_column], method="spearman")
            if not math.isnan(ic) and not math.isnan(rank_ic):
                daily_ic.append({"date": date, "factor": factor, "ic": ic, "rank_ic": rank_ic})
            q = _safe_qcut(daily[factor], quantiles)
            if q is not None:
                daily_with_quantile = daily.assign(quantile=q)
                grouped = daily_with_quantile.groupby("quantile")[label_column].mean()
                for quantile, value in grouped.items():
                    quantile_rows.append(
                        {"date": date, "factor": factor, "quantile": int(quantile), "mean_forward_return": float(value)}
                    )

        factor_series = pd.DataFrame(daily_ic)
        if factor_series.empty:
            ic_rows.append({"factor": factor, "ic_mean": 0.0, "rank_ic_mean": 0.0, "ic_ir": 0.0, "observations": 0})
        else:
            ic_std = factor_series["ic"].std(ddof=0)
            ic_rows.append(
                {
                    "factor": factor,
                    "ic_mean": float(factor_series["ic"].mean()),
                    "rank_ic_mean": float(factor_series["rank_ic"].mean()),
                    "ic_ir": float(factor_series["ic"].mean() / ic_std) if ic_std and ic_std > 0 else 0.0,
                    "observations": int(len(factor_series)),
                }
            )
        valid = joined[[factor, label_column]].dropna()
        coverage_rows.append({"factor": factor, "coverage": float(len(valid) / max(1, len(joined)))})

    return FactorAnalysisResult(
        ic_summary=pd.DataFrame(ic_rows),
        ic_series=_build_ic_series(joined, factor_columns, label_column),
        quantile_returns=pd.DataFrame(quantile_rows),
        coverage=pd.DataFrame(coverage_rows),
    )


def _build_ic_series(joined: pd.DataFrame, factor_columns: list[str], label_column: str) -> pd.DataFrame:
    rows = []
    for factor in factor_columns:
        for date, daily in joined[[factor, label_column]].dropna().groupby(level="date"):
            if daily[factor].nunique() < 2 or daily[label_column].nunique() < 2:
                continue
            rows.append(
                {
                    "date": date,
                    "factor": factor,
                    "ic": float(daily[factor].corr(daily[label_column], method="pearson")),
                    "rank_ic": float(daily[factor].corr(daily[label_column], method="spearman")),
                }
            )
    return pd.DataFrame(rows, columns=["date", "factor", "ic", "rank_ic"])


def _safe_qcut(values: pd.Series, quantiles: int) -> pd.Series | None:
    try:
        return pd.qcut(values.rank(method="first"), quantiles, labels=False, duplicates="drop") + 1
    except ValueError:
        return None

