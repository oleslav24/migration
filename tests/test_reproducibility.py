from pathlib import Path
from uuid import uuid4

from src.config import PipelineConfig
from src.pipeline import run_pipeline


def test_same_random_state_gives_same_topics():
    config = PipelineConfig.from_yaml("tests/fixtures/config_smoke.yaml")
    run_id = uuid4().hex
    config.output_dir = str(Path("tmp_write_check") / run_id / "output")
    config.interim_dir = str(Path("tmp_write_check") / run_id / "interim")
    first = run_pipeline(config)["documents"]["topic_id"].tolist()
    second = run_pipeline(config)["documents"]["topic_id"].tolist()
    assert first == second
