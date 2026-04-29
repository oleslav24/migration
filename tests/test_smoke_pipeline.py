from pathlib import Path

from src.config import PipelineConfig
from src.pipeline import run_pipeline


def test_smoke_pipeline_exports_results():
    config = PipelineConfig.from_yaml("tests/fixtures/config_smoke.yaml")
    result = run_pipeline(config)
    output_dir = Path(config.output_dir)

    assert len(result["documents"]) > 0
    assert (output_dir / "documents_enriched.csv").exists()
    assert (output_dir / "topic_distribution.csv").exists()
    assert (output_dir / "temporal_dynamics.csv").exists()
    assert (output_dir / "group_comparison.csv").exists()
    assert (output_dir / "metrics.json").exists()
    assert (output_dir / "topic_labels.json").exists()
    assert {"topic_id", "sentiment", "period"}.issubset(result["documents"].columns)

