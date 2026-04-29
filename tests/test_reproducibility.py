from src.config import PipelineConfig
from src.pipeline import run_pipeline


def test_same_random_state_gives_same_topics():
    config = PipelineConfig.from_yaml("tests/fixtures/config_smoke.yaml")
    first = run_pipeline(config)["documents"]["topic_id"].tolist()
    second = run_pipeline(config)["documents"]["topic_id"].tolist()
    assert first == second

