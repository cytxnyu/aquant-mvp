from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


WAREHOUSE_TABLES = {
    "daily_bar",
    "minute_bar",
    "adj_factor",
    "limit_price",
    "suspension",
    "st_flag",
    "delist",
    "ipo",
    "trade_calendar",
    "industry",
    "index_member",
    "financial",
    "valuation",
    "announcement",
    "raw_events",
    "event_store",
    "event_factor",
    "factor_registry",
    "factor_trust_audit",
    "moneyflow",
    "northbound",
    "margin",
    "block_trade",
    "dragon_tiger",
    "concept",
    "feature_store",
    "universe",
    "model_registry",
    "stock_forecast",
    "forecast_kline",
    "backtest_result",
    "paper_trade",
    "source_audit",
    "cross_source_diff_report",
}


@dataclass(frozen=True)
class WarehouseWriteResult:
    table: str
    path: Path
    rows: int
    file_format: str


@dataclass
class LocalWarehouse:
    root_dir: Path
    file_format: str = "auto"

    def write_table(self, table: str, frame: pd.DataFrame) -> WarehouseWriteResult:
        _validate_table(table)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        fmt = self._resolve_format()
        path = self._table_path(table, fmt)
        if fmt == "parquet":
            frame.to_parquet(path, index=False)
        else:
            frame.to_csv(path, index=False)
        self._write_manifest(table, path, len(frame), fmt)
        return WarehouseWriteResult(table=table, path=path, rows=int(len(frame)), file_format=fmt)

    def read_table(self, table: str) -> pd.DataFrame:
        _validate_table(table)
        parquet_path = self._table_path(table, "parquet")
        csv_path = self._table_path(table, "csv")
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        if csv_path.exists():
            return pd.read_csv(csv_path)
        raise FileNotFoundError(f"Warehouse table not found: {table}")

    def _resolve_format(self) -> str:
        if self.file_format in {"csv", "parquet"}:
            return self.file_format
        try:
            import pyarrow  # noqa: F401  # type: ignore

            return "parquet"
        except ImportError:
            return "csv"

    def _table_path(self, table: str, fmt: str) -> Path:
        return self.root_dir / f"{table}.{fmt}"

    def _write_manifest(self, table: str, path: Path, rows: int, fmt: str) -> None:
        manifest = self.root_dir / "_manifest.csv"
        row = pd.DataFrame([{"table": table, "path": str(path), "rows": rows, "file_format": fmt}])
        if manifest.exists():
            existing = pd.read_csv(manifest)
            existing = existing[existing["table"] != table]
            row = pd.concat([existing, row], ignore_index=True)
        row.to_csv(manifest, index=False)


def _validate_table(table: str) -> None:
    if table not in WAREHOUSE_TABLES:
        raise ValueError(f"Unsupported warehouse table: {table}")
