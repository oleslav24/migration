from src.config import PipelineConfig


def test_config_loads():
    config = PipelineConfig.from_yaml("config.yaml")

    assert config.input_path == "data/telegram_comments_12.25.csv"
    assert config.language_detection["backend"] == "rule-based"
    assert config.sentiment["backend"] == "rule-based"
    assert config.topic_model["backend"] == "kmeans"
