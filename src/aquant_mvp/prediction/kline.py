from __future__ import annotations

from dataclasses import dataclass
import base64
import json
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd

from aquant_mvp.prediction.stock import StockForecastResult, build_stock_forecast


@dataclass(frozen=True)
class KLineForecastResult:
    forecast: pd.DataFrame
    history: pd.DataFrame
    stock_forecast: StockForecastResult
    summary: dict[str, object]
    markdown: str


def build_kline_forecast(
    bars_by_symbol: dict[str, pd.DataFrame],
    symbol: str,
    horizons: list[int],
    source: str,
    model_type: str = "ensemble",
    days: int = 20,
    history_days: int = 120,
    embargo_days: int = 5,
    allow_sample: bool = False,
    event_factors: pd.DataFrame | None = None,
    model_registry_dir: Path | None = None,
) -> KLineForecastResult:
    """Build probabilistic future OHLC scenarios from the stock forecast table."""
    symbol = symbol.zfill(6)
    if days < 1:
        raise ValueError("K-line forecast requires days >= 1.")
    if symbol not in bars_by_symbol:
        raise ValueError(f"Symbol {symbol} is not loaded in the current universe.")

    forecast_horizons = sorted({1, 5, 20, 60, days, *[int(horizon) for horizon in horizons if int(horizon) > 0]})
    stock_forecast = build_stock_forecast(
        bars_by_symbol,
        symbol,
        forecast_horizons,
        source=source,
        model_type=model_type,
        embargo_days=embargo_days,
        allow_sample=allow_sample,
        event_factors=event_factors,
        model_registry_dir=model_registry_dir,
    )
    bars = bars_by_symbol[symbol].sort_values("date").copy()
    bars["date"] = pd.to_datetime(bars["date"])
    latest_bar = bars.iloc[-1]
    latest_close = float(latest_bar["close"])
    latest_date = pd.Timestamp(latest_bar["date"])
    history = bars.tail(max(history_days, 1)).copy()

    daily_path = _interpolated_path(stock_forecast.forecast, days)
    risk_scale = _daily_range_scale(bars)
    future_dates = pd.bdate_range(latest_date + pd.offsets.BDay(1), periods=days)
    scenario_specs = [
        ("bearish", "p10_close", 0.85),
        ("base", "p50_close", 1.00),
        ("bullish", "p90_close", 1.15),
    ]
    previous_close = {name: latest_close for name, _column, _scale in scenario_specs}
    rows: list[dict[str, object]] = []
    for idx, date in enumerate(future_dates, start=1):
        path_row = daily_path.iloc[idx - 1].to_dict()
        p10_close = latest_close * (1 + float(path_row["return_p10"]))
        p50_close = latest_close * (1 + float(path_row["return_p50"]))
        p90_close = latest_close * (1 + float(path_row["return_p90"]))
        ordered = sorted([p10_close, p50_close, p90_close])
        p10_close, p50_close, p90_close = ordered
        for scenario, close_column, intraday_scale in scenario_specs:
            open_price = previous_close[scenario]
            close_price = {"p10_close": p10_close, "p50_close": p50_close, "p90_close": p90_close}[close_column]
            band_width = max(risk_scale * intraday_scale, abs(close_price / max(open_price, 1e-12) - 1) * 0.35, 0.0025)
            high = max(open_price, close_price) * (1 + band_width)
            low = min(open_price, close_price) * (1 - band_width)
            previous_close[scenario] = close_price
            nearest = _nearest_forecast_row(stock_forecast.forecast, idx)
            rows.append(
                {
                    "date": date.date().isoformat(),
                    "symbol": symbol,
                    "day_index": idx,
                    "scenario": scenario,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close_price,
                    "p10_close": p10_close,
                    "p50_close": p50_close,
                    "p90_close": p90_close,
                    "prob_up": float(path_row["prob_up"]),
                    "expected_return": float(path_row["expected_return"]),
                    "expected_excess_return": float(path_row["expected_excess_return"]),
                    "return_p10": float(path_row["return_p10"]),
                    "return_p50": float(path_row["return_p50"]),
                    "return_p90": float(path_row["return_p90"]),
                    "direction": nearest.get("direction", ""),
                    "trend_label": nearest.get("trend_label", ""),
                    "confidence": float(path_row["confidence"]),
                    "risk_flags": str(nearest.get("risk_flags", "")),
                    "trust_status": str(nearest.get("trust_status", "")),
                    "model_id": str(nearest.get("model_id", "")),
                    "model_type": model_type,
                    "data_version": str(nearest.get("data_version", "")),
                    "is_forecast": True,
                    "note": "Probabilistic scenario path only; not guaranteed price movement or investment advice.",
                }
            )
    forecast = pd.DataFrame(rows)
    markdown = _build_markdown(symbol, latest_close, latest_date, stock_forecast.forecast, forecast, source, model_type)
    summary = {
        "symbol": symbol,
        "source": source,
        "model_type": model_type,
        "days": int(days),
        "history_days": int(history_days),
        "latest_date": latest_date.date().isoformat(),
        "latest_close": latest_close,
        "forecast_rows": int(len(forecast)),
        "scenarios": ["bearish", "base", "bullish"],
        "horizons": forecast_horizons,
        "data_version": str(stock_forecast.forecast["data_version"].iloc[0]) if not stock_forecast.forecast.empty else "",
        "trust_status_set": sorted(forecast["trust_status"].dropna().astype(str).unique().tolist()),
        "note": "Predicted K-line is a probability scenario chart, not a deterministic forecast.",
    }
    return KLineForecastResult(
        forecast=forecast,
        history=history,
        stock_forecast=stock_forecast,
        summary=summary,
        markdown=markdown,
    )


def save_kline_forecast_outputs(result: KLineForecastResult, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "stock_forecast": output_dir / "stock_forecast.csv",
        "stock_forecast_json": output_dir / "stock_forecast.json",
        "forecast_kline": output_dir / "forecast_kline.csv",
        "forecast_kline_json": output_dir / "forecast_kline.json",
        "history_kline": output_dir / "history_kline.csv",
        "forecast_kline_png": output_dir / "forecast_kline.png",
        "forecast_kline_html": output_dir / "forecast_kline.html",
        "stock_prediction_report": output_dir / "stock_prediction_report.md",
    }
    result.stock_forecast.forecast.to_csv(paths["stock_forecast"], index=False)
    paths["stock_forecast_json"].write_text(
        json.dumps(result.stock_forecast.summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    result.forecast.to_csv(paths["forecast_kline"], index=False)
    paths["forecast_kline_json"].write_text(json.dumps(result.summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    result.history.to_csv(paths["history_kline"], index=False)
    save_kline_chart(result, paths["forecast_kline_png"])
    write_kline_html(result, paths["forecast_kline_html"], paths["forecast_kline_png"])
    paths["stock_prediction_report"].write_text(result.markdown, encoding="utf-8")
    return paths


def save_kline_chart(result: KLineForecastResult, path: Path) -> None:
    plt = _get_pyplot()
    if plt is None:
        return
    from matplotlib.patches import Rectangle

    history = result.history.sort_values("date").copy()
    history["date"] = pd.to_datetime(history["date"])
    base = result.forecast[result.forecast["scenario"] == "base"].copy()
    base["date"] = pd.to_datetime(base["date"])
    n_hist = len(history)
    hist_x = np.arange(n_hist)
    fut_x = np.arange(n_hist, n_hist + len(base))

    fig, ax = plt.subplots(figsize=(13, 6.2))
    _draw_candles(ax, hist_x, history, width=0.62, alpha=0.90, forecast=False, Rectangle=Rectangle)
    _draw_candles(ax, fut_x, base, width=0.52, alpha=0.45, forecast=True, Rectangle=Rectangle)
    if not base.empty:
        ax.fill_between(
            fut_x,
            base["p10_close"].astype(float).to_numpy(),
            base["p90_close"].astype(float).to_numpy(),
            color="#6f8fd6",
            alpha=0.18,
            label="p10-p90 band",
        )
        ax.plot(fut_x, base["p50_close"].astype(float), color="#355cc9", linewidth=1.6, linestyle="--", label="p50 path")
        ax.axvline(n_hist - 0.5, color="#222222", linewidth=1.0, linestyle=":", alpha=0.7)
        last = base.iloc[-1]
        ax.annotate(
            f"prob_up={float(last['prob_up']):.2f}\nexp={float(last['expected_return']):.2%}\ntrust={last['trust_status']}",
            xy=(fut_x[-1], float(last["close"])),
            xytext=(-90, 35),
            textcoords="offset points",
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": "#999999", "alpha": 0.85},
            arrowprops={"arrowstyle": "->", "color": "#666666"},
        )
    labels = _axis_labels(history, base)
    ticks = np.linspace(0, max(1, n_hist + len(base) - 1), num=min(10, max(2, n_hist + len(base))), dtype=int)
    ax.set_xticks(ticks)
    ax.set_xticklabels([labels[idx] if idx < len(labels) else "" for idx in ticks], rotation=35, ha="right")
    symbol = str(result.summary.get("symbol", ""))
    ax.set_title(f"AQuant probabilistic K-line forecast: {symbol}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.grid(True, alpha=0.22)
    ax.legend(loc="best")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_kline_html(result: KLineForecastResult, path: Path, png_path: Path) -> None:
    image_data = ""
    if png_path.exists():
        image_data = base64.b64encode(png_path.read_bytes()).decode("ascii")
    base = result.forecast[result.forecast["scenario"] == "base"].copy()
    columns = ["day_index", "date", "close", "p10_close", "p50_close", "p90_close", "prob_up", "expected_return", "trust_status"]
    preview = base[columns].head(60).copy() if not base.empty else pd.DataFrame(columns=columns)
    table_rows = []
    for row in preview.itertuples(index=False):
        table_rows.append(
            "<tr>"
            + "".join(
                f"<td>{escape(_format_html_value(value))}</td>"
                for value in row
            )
            + "</tr>"
        )
    header = "".join(f"<th>{escape(column)}</th>" for column in columns)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>AQuant K-line Forecast {escape(str(result.summary.get("symbol", "")))}</title>
  <style>
    body {{ font-family: Arial, "Microsoft YaHei", sans-serif; margin: 28px; color: #20242a; }}
    h1 {{ font-size: 24px; margin-bottom: 8px; }}
    .note {{ color: #8a4b00; background: #fff7e6; border: 1px solid #ffd591; padding: 10px 12px; }}
    img {{ max-width: 100%; border: 1px solid #ddd; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 18px; font-size: 13px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: right; }}
    th {{ background: #f4f6f8; }}
    td:nth-child(2), th:nth-child(2), td:nth-child(9), th:nth-child(9) {{ text-align: left; }}
  </style>
</head>
<body>
  <h1>AQuant 预测 K 线走势图：{escape(str(result.summary.get("symbol", "")))}</h1>
  <p class="note">这是概率化研究情景图，不保证涨跌，不构成投资建议；真实交易必须经过样本外验证、模拟盘和风控。</p>
  <p>Source: <b>{escape(str(result.summary.get("source", "")))}</b> |
     Model: <b>{escape(str(result.summary.get("model_type", "")))}</b> |
     Days: <b>{escape(str(result.summary.get("days", "")))}</b> |
     Data version: <b>{escape(str(result.summary.get("data_version", "")))}</b></p>
  {"<img src=\"data:image/png;base64," + image_data + "\" alt=\"forecast kline\">" if image_data else "<p>PNG chart was not generated because matplotlib is unavailable.</p>"}
  <h2>Base Scenario Preview</h2>
  <table><thead><tr>{header}</tr></thead><tbody>{"".join(table_rows)}</tbody></table>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _interpolated_path(forecast: pd.DataFrame, days: int) -> pd.DataFrame:
    ordered = forecast.sort_values("horizon_days").drop_duplicates("horizon_days", keep="last").copy()
    anchors = np.r_[0, ordered["horizon_days"].astype(float).to_numpy()]
    rows: dict[str, np.ndarray] = {}
    future_days = np.arange(1, days + 1, dtype=float)
    for column in ["expected_return", "expected_excess_return", "return_p10", "return_p50", "return_p90", "prob_up", "confidence"]:
        values = ordered[column].astype(float).to_numpy()
        start = 0.5 if column == "prob_up" else 0.0
        rows[column] = np.interp(future_days, anchors, np.r_[start, values], left=start, right=values[-1] if len(values) else start)
    out = pd.DataFrame(rows)
    out["day_index"] = future_days.astype(int)
    ordered_returns = np.sort(out[["return_p10", "return_p50", "return_p90"]].to_numpy(dtype=float), axis=1)
    out["return_p10"] = ordered_returns[:, 0]
    out["return_p50"] = ordered_returns[:, 1]
    out["return_p90"] = ordered_returns[:, 2]
    return out


def _nearest_forecast_row(forecast: pd.DataFrame, day_index: int) -> dict[str, object]:
    if forecast.empty:
        return {}
    distances = (forecast["horizon_days"].astype(int) - int(day_index)).abs()
    return forecast.loc[distances.idxmin()].to_dict()


def _daily_range_scale(bars: pd.DataFrame) -> float:
    df = bars.sort_values("date").copy()
    prev_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_pct = (true_range / df["close"].replace(0, np.nan)).tail(20).median()
    ret_vol = df["close"].pct_change().tail(20).std()
    candidates = [float(value) for value in [atr_pct, ret_vol] if pd.notna(value) and value > 0]
    return float(np.clip(np.median(candidates) if candidates else 0.02, 0.003, 0.08))


def _draw_candles(ax, xs: np.ndarray, frame: pd.DataFrame, width: float, alpha: float, forecast: bool, Rectangle) -> None:
    if frame.empty:
        return
    up_color = "#d94a3a" if not forecast else "#4d73d9"
    down_color = "#2f8f5b" if not forecast else "#8b93a7"
    edge = "#4d73d9" if forecast else "#333333"
    for x, row in zip(xs, frame.itertuples(index=False), strict=False):
        open_price = float(getattr(row, "open"))
        high = float(getattr(row, "high"))
        low = float(getattr(row, "low"))
        close = float(getattr(row, "close"))
        color = up_color if close >= open_price else down_color
        ax.vlines(x, low, high, color=edge if forecast else color, linewidth=0.9, alpha=alpha)
        body_low = min(open_price, close)
        body_height = max(abs(close - open_price), max(close, open_price) * 0.001)
        ax.add_patch(
            Rectangle(
                (x - width / 2, body_low),
                width,
                body_height,
                facecolor=color,
                edgecolor=edge if forecast else color,
                linewidth=0.8,
                alpha=alpha,
                linestyle="--" if forecast else "-",
            )
        )


def _axis_labels(history: pd.DataFrame, base: pd.DataFrame) -> list[str]:
    hist_labels = pd.to_datetime(history["date"]).dt.strftime("%Y-%m-%d").tolist() if not history.empty else []
    future_labels = pd.to_datetime(base["date"]).dt.strftime("%Y-%m-%d").tolist() if not base.empty else []
    return [*hist_labels, *future_labels]


def _build_markdown(
    symbol: str,
    latest_close: float,
    latest_date: pd.Timestamp,
    stock_forecast: pd.DataFrame,
    kline: pd.DataFrame,
    source: str,
    model_type: str,
) -> str:
    lines = [
        f"# AQuant 个股预测报告：{symbol}",
        "",
        "## 核心结论",
        "",
        f"- 最新交易日：`{latest_date.date().isoformat()}`",
        f"- 最新收盘价：`{latest_close:.4f}`",
        f"- 数据源：`{source}`",
        f"- 模型：`{model_type}`",
        "- 结论性质：概率化研究信号，不保证涨跌，不构成投资建议。",
        "",
        "## 多周期预测",
        "",
    ]
    for row in stock_forecast.sort_values("horizon_days").itertuples(index=False):
        lines.append(
            f"- `{row.horizon_days}d`: direction=`{row.direction}`, prob_up=`{row.prob_up:.3f}`, "
            f"expected_return=`{row.expected_return:.3%}`, p10/p50/p90=`{row.return_p10:.3%}/{row.return_p50:.3%}/{row.return_p90:.3%}`, "
            f"trust=`{row.trust_status}`"
        )
    lines.extend(["", "## 预测 K 线说明", ""])
    base = kline[kline["scenario"] == "base"].copy()
    if base.empty:
        lines.append("- K 线路径生成失败或无可用预测。")
    else:
        last = base.iloc[-1]
        lines.append(
            f"- Base 情景第 {int(last['day_index'])} 日收盘：`{float(last['close']):.4f}`；"
            f"p10/p50/p90 收盘带：`{float(last['p10_close']):.4f}/{float(last['p50_close']):.4f}/{float(last['p90_close']):.4f}`。"
        )
        lines.append(
            f"- 最近风险标记：`{last['risk_flags']}`；趋势标签：`{last['trend_label']}`；置信度：`{float(last['confidence']):.3f}`。"
        )
    lines.extend(
        [
            "",
            "## 输出文件",
            "",
            "- `stock_forecast.csv/json`: 多周期个股预测。",
            "- `forecast_kline.csv/json`: 未来 OHLC 概率情景。",
            "- `forecast_kline.png/html`: 历史 + 未来预测 K 线图。",
            "- `history_kline.csv`: 图表使用的历史 K 线。",
            "",
            "## 风险声明",
            "",
            "免费数据源存在缺口和延迟；预测必须通过大样本 walk-forward、单票回测、模拟盘和风控后才可讨论实盘。真实下单在当前项目中仍然强制关闭。",
        ]
    )
    return "\n".join(lines)


def _format_html_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _get_pyplot():
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
    except Exception:
        return None
    return plt
