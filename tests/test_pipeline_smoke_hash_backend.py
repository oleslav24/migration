from pathlib import Path
from uuid import uuid4

from src.config import PipelineConfig
from src.pipeline import run_pipeline


def test_pipeline_smoke_hash_backend_exports_driver_tables():
    config = PipelineConfig.from_yaml("tests/fixtures/config_smoke.yaml")
    run_id = uuid4().hex
    config.output_dir = str(Path("tmp_write_check") / run_id / "output")
    config.interim_dir = str(Path("tmp_write_check") / run_id / "interim")
    result = run_pipeline(config)
    output_dir = Path(config.output_dir)

    assert config.embedding_backend == "hash"
    assert not result["documents"].empty
    assert (output_dir / "migration_driver_distribution.csv").exists()
    assert (output_dir / "driver_temporal_dynamics.csv").exists()
    assert (output_dir / "driver_by_group.csv").exists()
