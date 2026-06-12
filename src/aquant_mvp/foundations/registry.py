from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
import os
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class FoundationCapability:
    foundation_id: str
    category: str
    role: str
    priority: int
    python_modules: tuple[str, ...]
    package_hint: str
    license_mode: str
    integration_status: str
    domestic_install_hint: str
    notes: str


FOUNDATION_REGISTRY: tuple[FoundationCapability, ...] = (
    FoundationCapability(
        "qlib",
        "research_platform",
        "institution-style alpha research, dataset handler, model workflow",
        1,
        ("qlib",),
        "pyqlib",
        "open_source",
        "candidate_adapter",
        "pip install pyqlib -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Good base for factor/model research, but A-share data still needs a local provider.",
    ),
    FoundationCapability(
        "backtrader",
        "backtest_engine",
        "event-driven strategy backtest and broker simulation",
        2,
        ("backtrader",),
        "backtrader",
        "open_source",
        "candidate_adapter",
        "pip install backtrader -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Useful for event-driven testing; current native engine remains the default for A-share rules.",
    ),
    FoundationCapability(
        "vectorbt",
        "backtest_engine",
        "vectorized factor portfolio experiments",
        3,
        ("vectorbt",),
        "vectorbt",
        "open_source",
        "candidate_adapter",
        "pip install vectorbt -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Useful for fast research sweeps; execution realism still handled by native engine/QMT paper path.",
    ),
    FoundationCapability(
        "vnpy",
        "execution_platform",
        "multi-asset event engine and trading gateway ecosystem",
        4,
        ("vnpy",),
        "vnpy",
        "open_source_plus_gateway_auth",
        "candidate_adapter",
        "pip install vnpy -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Optional later path; QMT/XtQuant remains the default A-share personal execution route.",
    ),
    FoundationCapability(
        "rqalpha",
        "research_platform",
        "domestic event-driven backtest framework",
        5,
        ("rqalpha",),
        "rqalpha",
        "open_source",
        "candidate_adapter",
        "pip install rqalpha -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Useful as a domestic-style backtest comparison base.",
    ),
    FoundationCapability(
        "lightgbm",
        "model_base",
        "gradient boosting classifier/regressor/ranker",
        1,
        ("lightgbm",),
        "lightgbm",
        "open_source",
        "native_supported",
        "pip install lightgbm -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Primary tabular model; current code auto-falls back when unavailable.",
    ),
    FoundationCapability(
        "xgboost",
        "model_base",
        "gradient boosting baseline and robustness comparison",
        2,
        ("xgboost",),
        "xgboost",
        "open_source",
        "candidate_model",
        "pip install xgboost -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Candidate challenger for LightGBM.",
    ),
    FoundationCapability(
        "catboost",
        "model_base",
        "categorical-friendly gradient boosting baseline",
        3,
        ("catboost",),
        "catboost",
        "open_source",
        "candidate_model",
        "pip install catboost -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Candidate model for industry/theme categorical features.",
    ),
    FoundationCapability(
        "scikit_learn",
        "model_base",
        "linear/logistic baselines, calibration, metrics",
        1,
        ("sklearn",),
        "scikit-learn",
        "open_source",
        "candidate_model",
        "pip install scikit-learn -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Useful for probability calibration and transparent baselines.",
    ),
    FoundationCapability(
        "pytorch",
        "deep_learning_base",
        "TabNet/TFT/graph model future base",
        6,
        ("torch",),
        "torch",
        "open_source",
        "future_candidate",
        "pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Do not lead with deep models until PIT data and walk-forward proof are stable.",
    ),
    FoundationCapability(
        "shap",
        "explainability",
        "tree model feature contribution and local explanation",
        2,
        ("shap",),
        "shap",
        "open_source",
        "candidate_explainer",
        "pip install shap -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Candidate upgrade for current z-score contributor explanation.",
    ),
    FoundationCapability(
        "ta_lib",
        "factor_engine",
        "technical indicator engine for momentum, volatility, trend and candlestick factors",
        1,
        ("talib",),
        "ta-lib",
        "open_source",
        "candidate_factor_engine",
        "pip install ta-lib -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Installed as part of the vn.py stack; useful for expanding technical factors beyond native pandas formulas.",
    ),
    FoundationCapability(
        "optuna",
        "model_ops",
        "walk-forward hyperparameter optimization",
        4,
        ("optuna",),
        "optuna",
        "open_source",
        "candidate_model_ops",
        "pip install optuna -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Use after baseline stability, with strict time splits.",
    ),
    FoundationCapability(
        "akshare",
        "free_data",
        "public A-share quote, money-flow, sector and free data access",
        1,
        ("akshare",),
        "akshare",
        "free_public",
        "native_supported",
        "pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Primary free public data source; free endpoints can change without notice.",
    ),
    FoundationCapability(
        "baostock",
        "free_data",
        "A-share daily bars, adjustment and stock list cross-check",
        1,
        ("baostock",),
        "baostock",
        "free_public",
        "native_supported",
        "pip install baostock -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Important free fallback and all-A discovery source.",
    ),
    FoundationCapability(
        "tushare_free",
        "free_data",
        "token-gated free data supplement",
        2,
        ("tushare",),
        "tushare",
        "free_token_limited",
        "native_supported",
        "pip install tushare -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Requires TUSHARE_TOKEN; free quota and fields are limited.",
    ),
    FoundationCapability(
        "rqdata",
        "paid_data",
        "RiceQuant professional data supplement",
        5,
        ("rqdatac",),
        "rqdatac",
        "paid_or_authorized",
        "future_adapter",
        "Follow RiceQuant official install docs or domestic package mirror.",
        "Professional data route when authorized; not required for free mode.",
    ),
    FoundationCapability(
        "windpy",
        "paid_data",
        "Wind professional A-share data",
        5,
        ("WindPy",),
        "WindPy",
        "paid_or_authorized",
        "future_adapter",
        "Use Wind terminal installer and licensed Python SDK.",
        "Institutional data route; depends on local Wind authorization.",
    ),
    FoundationCapability(
        "ifind",
        "paid_data",
        "iFinD professional A-share data",
        5,
        ("iFinDPy",),
        "iFinDPy",
        "paid_or_authorized",
        "future_adapter",
        "Use iFinD terminal installer and licensed Python SDK.",
        "Institutional data route; depends on local iFinD authorization.",
    ),
    FoundationCapability(
        "duckdb_parquet",
        "storage_base",
        "local analytical warehouse and parquet acceleration",
        1,
        ("duckdb", "pyarrow"),
        "duckdb pyarrow",
        "open_source",
        "native_supported",
        "pip install duckdb pyarrow -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Current warehouse falls back to CSV when parquet engine is unavailable.",
    ),
    FoundationCapability(
        "qmt_xtquant",
        "broker_base",
        "QMT/XtQuant read-only and future guarded execution",
        1,
        ("xtquant",),
        "xtquant",
        "broker_authorized",
        "read_only_supported_live_blocked",
        "Install from the local QMT/MiniQMT client package.",
        "Live order submission remains intentionally blocked by default.",
    ),
)


def discover_foundations() -> pd.DataFrame:
    rows = []
    for item in FOUNDATION_REGISTRY:
        installed_modules = [module for module in item.python_modules if _module_available(module)]
        missing_modules = [module for module in item.python_modules if module not in installed_modules]
        rows.append(
            {
                **asdict(item),
                "python_modules": ",".join(item.python_modules),
                "installed": not missing_modules,
                "installed_modules": ",".join(installed_modules),
                "missing_modules": ",".join(missing_modules),
                "credential_ready": _credential_ready(item.foundation_id),
            }
        )
    return pd.DataFrame(rows).sort_values(["category", "priority", "foundation_id"]).reset_index(drop=True)


def write_foundation_report(output_dir: Path, frame: pd.DataFrame | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = discover_foundations() if frame is None else frame
    csv_path = output_dir / "foundation_registry.csv"
    md_path = output_dir / "foundation_registry.md"
    data.to_csv(csv_path, index=False)
    lines = [
        "# Foundation Registry",
        "",
        "This registry records which external quant bases can be used by AQuant, whether they are installed, and how they fit into the system.",
        "",
        f"- total: {len(data)}",
        f"- installed: {int(data['installed'].sum()) if not data.empty else 0}",
        f"- native_supported: {int(data['integration_status'].astype(str).str.contains('native_supported').sum()) if not data.empty else 0}",
        "",
        "| foundation | category | status | installed | license | package |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in data.itertuples():
        lines.append(
            f"| {row.foundation_id} | {row.category} | {row.integration_status} | {row.installed} | {row.license_mode} | {row.package_hint} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _credential_ready(foundation_id: str) -> bool:
    if foundation_id == "tushare_free":
        return bool(os.getenv("TUSHARE_TOKEN"))
    if foundation_id == "windpy":
        return _module_available("WindPy")
    if foundation_id == "ifind":
        return _module_available("iFinDPy")
    if foundation_id == "qmt_xtquant":
        return _module_available("xtquant")
    return True
