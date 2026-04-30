from pathlib import Path
from uuid import uuid4

from src.config import PipelineConfig
from src.pipeline import run_pipeline


def test_smoke_pipeline_exports_results():
    config = PipelineConfig.from_yaml("tests/fixtures/config_smoke.yaml")
    run_id = uuid4().hex
    config.output_dir = str(Path("tmp_write_check") / run_id / "output")
    config.interim_dir = str(Path("tmp_write_check") / run_id / "interim")
    result = run_pipeline(config)
    output_dir = Path(config.output_dir)

    assert len(result["documents"]) > 0
    assert (output_dir / "documents_enriched.csv").exists()
    assert (output_dir / "topic_distribution.csv").exists()
    assert (output_dir / "temporal_dynamics.csv").exists()
    assert (output_dir / "group_comparison.csv").exists()
    assert (output_dir / "migration_driver_distribution.csv").exists()
    assert (output_dir / "driver_temporal_dynamics.csv").exists()
    assert (output_dir / "driver_by_group.csv").exists()
    assert (output_dir / "toponym_frequency.csv").exists()
    assert (output_dir / "top_10_toponyms.csv").exists()
    assert (output_dir / "city_level_stats.csv").exists()
    assert (output_dir / "district_level_stats.csv").exists()
    assert (output_dir / "topics_per_toponym.csv").exists()
    assert (output_dir / "sentiment_per_toponym.csv").exists()
    assert (output_dir / "random_samples_per_toponym.csv").exists()
    assert (output_dir / "texts_by_toponym").exists()
    assert (output_dir / "metrics.json").exists()
    assert (output_dir / "topic_labels.json").exists()
    assert {"topic_id", "sentiment", "period", "migration_driver", "toponyms"}.issubset(
        result["documents"].columns
    )
