from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


DEFAULT_FACTOR_WEIGHTS = {
    "momentum_20": 0.30,
    "momentum_60": 0.20,
    "reversal_5": 0.15,
    "reversal_10": 0.10,
    "volatility_20": -0.15,
    "volatility_60": -0.10,
    "amount_mean_20": 0.10,
    "turnover_mean_20": 0.08,
    "volume_ratio_5_20": 0.08,
    "price_position_60": 0.08,
    "ma_bias_20": 0.06,
    "max_drawdown_60": -0.10,
    "downside_volatility_20": -0.08,
}


@dataclass(frozen=True)
class DataConfig:
    source: str = "sample"
    symbols: list[str] = field(default_factory=list)
    start_date: str = "2022-01-01"
    end_date: str = "2025-12-31"
    adjust: str = "qfq"
    cache_dir: Path = Path("data/cache/daily")


@dataclass(frozen=True)
class UniverseConfig:
    min_history_days: int = 120
    min_amount: float = 0.0
    max_missing_ratio: float = 0.20
    exclude_symbols: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StrategyConfig:
    rebalance: str = "W-FRI"
    top_n: int = 5
    min_amount: float = 0.0
    max_single_weight: float = 0.30
    max_turnover: float = 1.0
    factor_weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_FACTOR_WEIGHTS))


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 1_000_000.0
    fee_rate: float = 0.0003
    tax_rate: float = 0.001
    slippage_rate: float = 0.0005
    lot_size: int = 100
    min_trade_value: float = 1000.0


@dataclass(frozen=True)
class ReportConfig:
    output_dir: Path = Path("reports")


@dataclass(frozen=True)
class AnalysisConfig:
    label_horizons: list[int] = field(default_factory=lambda: [5, 20])
    quantiles: int = 5


@dataclass(frozen=True)
class AppConfig:
    data: DataConfig = field(default_factory=DataConfig)
    universe: UniverseConfig = field(default_factory=UniverseConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    report: ReportConfig = field(default_factory=ReportConfig)


def _load_raw_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("YAML config requires PyYAML. Use JSON or install PyYAML.") from exc
        return yaml.safe_load(text) or {}
    return json.loads(text)


def load_config(path: str | Path) -> AppConfig:
    raw = _load_raw_config(Path(path))
    data_raw = raw.get("data", {})
    universe_raw = raw.get("universe", {})
    strategy_raw = raw.get("strategy", {})
    backtest_raw = raw.get("backtest", {})
    analysis_raw = raw.get("analysis", {})
    report_raw = raw.get("report", {})

    return AppConfig(
        data=DataConfig(
            source=data_raw.get("source", "sample"),
            symbols=[str(symbol).zfill(6) for symbol in data_raw.get("symbols", [])],
            start_date=data_raw.get("start_date", "2022-01-01"),
            end_date=data_raw.get("end_date", "2025-12-31"),
            adjust=data_raw.get("adjust", "qfq"),
            cache_dir=Path(data_raw.get("cache_dir", "data/cache/daily")),
        ),
        universe=UniverseConfig(
            min_history_days=int(universe_raw.get("min_history_days", 120)),
            min_amount=float(universe_raw.get("min_amount", 0.0)),
            max_missing_ratio=float(universe_raw.get("max_missing_ratio", 0.20)),
            exclude_symbols=[str(symbol).zfill(6) for symbol in universe_raw.get("exclude_symbols", [])],
        ),
        strategy=StrategyConfig(
            rebalance=strategy_raw.get("rebalance", "W-FRI"),
            top_n=int(strategy_raw.get("top_n", 5)),
            min_amount=float(strategy_raw.get("min_amount", 0.0)),
            max_single_weight=float(strategy_raw.get("max_single_weight", 0.30)),
            max_turnover=float(strategy_raw.get("max_turnover", 1.0)),
            factor_weights={
                str(name): float(weight)
                for name, weight in strategy_raw.get("factor_weights", DEFAULT_FACTOR_WEIGHTS).items()
            },
        ),
        backtest=BacktestConfig(
            initial_cash=float(backtest_raw.get("initial_cash", 1_000_000.0)),
            fee_rate=float(backtest_raw.get("fee_rate", 0.0003)),
            tax_rate=float(backtest_raw.get("tax_rate", 0.001)),
            slippage_rate=float(backtest_raw.get("slippage_rate", 0.0005)),
            lot_size=int(backtest_raw.get("lot_size", 100)),
            min_trade_value=float(backtest_raw.get("min_trade_value", 1000.0)),
        ),
        analysis=AnalysisConfig(
            label_horizons=[int(horizon) for horizon in analysis_raw.get("label_horizons", [5, 20])],
            quantiles=int(analysis_raw.get("quantiles", 5)),
        ),
        report=ReportConfig(output_dir=Path(report_raw.get("output_dir", "reports"))),
    )
