from __future__ import annotations

import argparse

from src.config import PipelineConfig
from src.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Digital Migration analysis pipeline.")
    parser.add_argument("--config", required=True, help="Path to YAML configuration file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = PipelineConfig.from_yaml(args.config)
    run_pipeline(config)


if __name__ == "__main__":
    main()

