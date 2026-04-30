from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import PipelineConfig
from src.pipeline import run_pipeline


def main() -> None:
    config = PipelineConfig.from_yaml(Path("config.yaml"))
    run_pipeline(config)


if __name__ == "__main__":
    main()
