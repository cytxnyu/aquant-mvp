from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from aquant_mvp.config import DataConfig


REQUIRED_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume", "amount", "turnover"]


@dataclass(frozen=True)
class LoadReport:
    source: str
    symbols_loaded: list[str]
    warnings: list[str]


def load_daily_bars(config: DataConfig) -> tuple[dict[str, pd.DataFrame], LoadReport]:
    """Load daily bars from AKShare, cache, or deterministic sample data."""
    source = config.source.lower()
    if source == "sample":
        bars = _load_sample_bars(config)
        return bars, LoadReport(source="sample", symbols_loaded=sorted(bars), warnings=[])

    if source not in {"akshare", "auto"}:
        raise ValueError(f"Unsupported data source: {config.source}")

    loaded: dict[str, pd.DataFrame] = {}
    notes: list[str] = []
    for symbol in config.symbols:
        try:
            loaded[symbol] = _load_akshare_symbol(config, symbol)
        except Exception as exc:  # noqa: BLE001 - fallback keeps the MVP runnable.
            message = f"{symbol}: AKShare load failed ({exc}); using sample data for this symbol."
            notes.append(message)
            warnings.warn(message, RuntimeWarning, stacklevel=2)
            sample_config = DataConfig(
                source="sample",
                symbols=[symbol],
                start_date=config.start_date,
                end_date=config.end_date,
                adjust=config.adjust,
                cache_dir=config.cache_dir,
            )
            loaded[symbol] = _load_sample_bars(sample_config)[symbol]

    return loaded, LoadReport(source=source, symbols_loaded=sorted(loaded), warnings=notes)


def _load_akshare_symbol(config: DataConfig, symbol: str) -> pd.DataFrame:
    cache_path = _cache_path(config.cache_dir, symbol, config.start_date, config.end_date, config.adjust)
    if cache_path.exists():
        return _read_cached(cache_path)

    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:
        raise RuntimeError("AKShare is not installed. Run `pip install -e .[data]` or use source=sample.") from exc

    raw = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=_compact_date(config.start_date),
        end_date=_compact_date(config.end_date),
        adjust=config.adjust,
    )
    frame = _normalize_akshare(raw, symbol)
    if frame.empty:
        raise RuntimeError("AKShare returned no rows")
    _write_cached(cache_path, frame)
    return frame


def _load_sample_bars(config: DataConfig) -> dict[str, pd.DataFrame]:
    cache_dir = config.cache_dir / "sample"
    result: dict[str, pd.DataFrame] = {}
    for symbol in config.symbols:
        cache_path = _cache_path(cache_dir, symbol, config.start_date, config.end_date, "sample")
        if cache_path.exists():
            result[symbol] = _read_cached(cache_path)
            continue
        frame = _make_sample_symbol(symbol, config.start_date, config.end_date)
        _write_cached(cache_path, frame)
        result[symbol] = frame
    return result


def _make_sample_symbol(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    dates = pd.bdate_range(start=start_date, end=end_date)
    if dates.empty:
        raise ValueError("No business days in sample date range")

    seed = int(symbol[-4:]) + 20260611
    rng = np.random.default_rng(seed)
    symbol_bias = (int(symbol[-2:]) - 50) / 100000
    market = rng.normal(loc=0.00025, scale=0.008, size=len(dates))
    idiosyncratic = rng.normal(loc=symbol_bias, scale=0.018, size=len(dates))
    cycle = 0.0018 * np.sin(np.linspace(0, 8 * np.pi, len(dates)) + int(symbol[-1]))
    returns = np.clip(market + idiosyncratic + cycle, -0.095, 0.095)

    base_price = 8 + (int(symbol[-3:]) % 120)
    close = base_price * np.cumprod(1 + returns)
    open_ = np.r_[close[0] / (1 + returns[0]), close[:-1]] * (1 + rng.normal(0, 0.003, len(dates)))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.018, len(dates)))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.018, len(dates)))
    volume = rng.integers(40_000, 2_500_000, len(dates)) * 100
    amount = volume * close
    turnover = rng.uniform(0.3, 8.0, len(dates))

    frame = pd.DataFrame(
        {
            "date": dates,
            "symbol": symbol,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume.astype(float),
            "amount": amount,
            "turnover": turnover,
        }
    )
    return _finalize_bars(frame)


def _normalize_akshare(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    rename_map = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "成交额": "amount",
        "换手率": "turnover",
    }
    frame = raw.rename(columns=rename_map).copy()
    frame["symbol"] = symbol
    missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    if missing:
        raise RuntimeError(f"AKShare schema missing columns: {missing}")
    return _finalize_bars(frame[REQUIRED_COLUMNS])


def _finalize_bars(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["symbol"] = out["symbol"].astype(str).str.zfill(6)
    for column in ["open", "high", "low", "close", "volume", "amount", "turnover"]:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    out = out.sort_values("date").drop_duplicates(subset=["date", "symbol"], keep="last")
    out = out.reset_index(drop=True)
    return out[REQUIRED_COLUMNS]


def _cache_path(cache_dir: Path, symbol: str, start_date: str, end_date: str, adjust: str) -> Path:
    safe_start = _compact_date(start_date)
    safe_end = _compact_date(end_date)
    return cache_dir / f"{symbol}_{adjust}_{safe_start}_{safe_end}.csv"


def _read_cached(path: Path) -> pd.DataFrame:
    return _finalize_bars(pd.read_csv(path))


def _write_cached(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _compact_date(value: str) -> str:
    return value.replace("-", "")

