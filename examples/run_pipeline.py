from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aquant_mvp.config import load_config
from aquant_mvp.pipeline import run_pipeline


if __name__ == "__main__":
    config = load_config(ROOT / "configs" / "mvp.json")
    run_pipeline(config, source="sample")

