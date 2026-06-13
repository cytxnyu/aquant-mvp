from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import importlib.util
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ModelBaseCapability:
    model_base_id: str
    package: str
    role: str
    available: bool
    version: str
    train_model_supported: bool
    walk_forward_supported: bool
    fallback_policy: str
    note: str


MODEL_BASES = [
    ModelBaseCapability(
        "factor_score",
        "builtin",
        "transparent_baseline",
        True,
        "builtin",
        True,
        True,
        "none",
        "Deterministic multi-factor rank baseline; always available and never treated as external ML.",
    ),
    ModelBaseCapability(
        "sklearn_linear",
        "sklearn",
        "logistic_ridge_linear_baseline",
        False,
        "",
        True,
        True,
        "fallback_to_factor_score_with_registry_reason",
        "Logistic/Ridge/Linear challenger for interpretable probability and return baselines.",
    ),
    ModelBaseCapability(
        "lightgbm",
        "lightgbm",
        "gbdt_classifier_regressor_ranker",
        False,
        "",
        True,
        True,
        "fallback_to_sklearn_or_factor_score_with_registry_reason",
        "Main GBDT model family for direction, return, and cross-sectional rank.",
    ),
    ModelBaseCapability(
        "xgboost",
        "xgboost",
        "gbdt_challenger",
        False,
        "",
        True,
        True,
        "fallback_to_factor_score_with_registry_reason",
        "Independent boosted-tree challenger used to falsify LightGBM-only conclusions.",
    ),
    ModelBaseCapability(
        "catboost",
        "catboost",
        "gbdt_challenger",
        False,
        "",
        True,
        True,
        "fallback_to_factor_score_with_registry_reason",
        "Ordered boosting challenger; useful when categorical/industry features are expanded.",
    ),
]


def discover_model_bases() -> pd.DataFrame:
    rows = []
    for base in MODEL_BASES:
        available = base.available if base.package == "builtin" else importlib.util.find_spec(base.package) is not None
        version = base.version
        if base.package != "builtin" and available:
            try:
                version = importlib.metadata.version(base.package)
            except importlib.metadata.PackageNotFoundError:
                version = "unknown"
        rows.append(
            {
                "model_base_id": base.model_base_id,
                "package": base.package,
                "role": base.role,
                "available": bool(available),
                "version": version,
                "train_model_supported": base.train_model_supported,
                "walk_forward_supported": base.walk_forward_supported,
                "fallback_policy": base.fallback_policy,
                "note": base.note,
            }
        )
    return pd.DataFrame(rows)


def write_model_base_report(output_dir: Path, frame: pd.DataFrame | None = None) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = frame if frame is not None else discover_model_bases()
    paths = {
        "csv": output_dir / "model_base_availability.csv",
        "md": output_dir / "model_base_availability.md",
    }
    data.to_csv(paths["csv"], index=False)
    lines = [
        "# Model Base Availability",
        "",
        "This table records whether each model base is actually importable in the local environment. Missing optional packages must be reported and may only fall back with an explicit registry reason.",
        "",
        "| model_base_id | package | available | version | role | fallback_policy |",
        "|---|---|---:|---|---|---|",
    ]
    for row in data.itertuples(index=False):
        lines.append(
            f"| {row.model_base_id} | {row.package} | {row.available} | {row.version} | {row.role} | {row.fallback_policy} |"
        )
    paths["md"].write_text("\n".join(lines), encoding="utf-8")
    return paths

