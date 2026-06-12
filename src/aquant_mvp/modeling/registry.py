from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any


@dataclass
class ModelRegistry:
    root_dir: Path

    @property
    def path(self) -> Path:
        return self.root_dir / "model_registry.json"

    def append(self, metadata: dict[str, Any]) -> dict[str, Any]:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        record = dict(metadata)
        record.setdefault("registered_at", datetime.now().isoformat(timespec="seconds"))
        records = self.records()
        records.append(record)
        self.path.write_text(json.dumps(records, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return record

    def records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))


def register_model(registry_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    return ModelRegistry(registry_dir).append(metadata)
