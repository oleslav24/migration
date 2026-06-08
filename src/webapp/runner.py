from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from src.config import PipelineConfig
from src.literature.cli import summarize_all_tasks
from src.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = Path(os.environ.get("MIGRATION_RUNTIME_ROOT", str(ROOT / "tmp_write_check"))).resolve()
RUN_OUTPUT_ROOT = Path(os.environ.get("MIGRATION_RUN_OUTPUT_ROOT", str(RUNTIME_ROOT / "web_runs" / "outputs"))).resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Safe web UI experiment runner.")
    parser.add_argument("experiment", choices=["pipeline-full", "pipeline-smoke", "youtube-sample", "literature-summaries"])
    args = parser.parse_args()
    if args.experiment == "pipeline-full":
        run_pipeline_full()
    elif args.experiment == "pipeline-smoke":
        run_pipeline_smoke()
    elif args.experiment == "youtube-sample":
        run_youtube_sample()
    elif args.experiment == "literature-summaries":
        run_literature_summaries()


def run_pipeline_full() -> None:
    config = PipelineConfig.from_yaml(ROOT / "config.yaml")
    _set_run_dirs(config, "pipeline_full")
    config.embedding_model = "hash"
    config.embedding_backend = "hash"
    config.save_interim_parquet = False
    run_pipeline(config)


def run_pipeline_smoke() -> None:
    config = PipelineConfig.from_yaml(ROOT / "tests" / "fixtures" / "config_smoke.yaml")
    _set_run_dirs(config, "pipeline_smoke")
    run_pipeline(config)


def run_youtube_sample() -> None:
    config = PipelineConfig(
        input_path="DS/youtube_comments_12.25.csv",
        input_paths=[{"path": "DS/youtube_comments_12.25.csv", "source": "youtube"}],
        embedding_model="hash",
        embedding_backend="hash",
        n_topics=3,
        chunk_size=2000,
        max_rows=2000,
        save_interim_parquet=False,
        make_plots=False,
    )
    config.topic_model["n_topics"] = 3
    _set_run_dirs(config, "youtube_sample")
    run_pipeline(config)


def run_literature_summaries() -> None:
    config = PipelineConfig.from_yaml(ROOT / "config.yaml")
    _set_run_dirs(config, "literature_summaries")
    summaries = summarize_all_tasks(config, ROOT / "queries" / "summarization_tasks.yaml")
    print(f"Summaries written: {len(summaries)}")
    print(f"Output: {config.output_dir}")


def _set_run_dirs(config: PipelineConfig, name: str) -> None:
    run_id = f"{int(time.time())}_{name}"
    root = RUN_OUTPUT_ROOT / run_id
    config.output_dir = str(root / "output")
    config.interim_dir = str(root / "interim")


if __name__ == "__main__":
    main()
