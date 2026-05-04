from pathlib import Path
from uuid import uuid4

from src.config import PipelineConfig
from src.data_loader import load_csv
from src.preprocess import preprocess_chunk


def test_youtube_malformed_csv_loads_and_preprocesses():
    work_dir = Path("tmp_write_check") / uuid4().hex
    path = work_dir / "youtube_comments_12.25.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "datetime,author,group,comment\n"
        '"2025-12-07T08:08:22Z,@author,video123,""Comment, with comma and quotes"""\n'
        "2025-12-05T09:43:59Z,@author2,video123,Plain comment\n",
        encoding="utf-8",
    )
    config = PipelineConfig(
        input_path=str(path),
        input_paths=[{"path": str(path), "source": "youtube"}],
        chunk_size=10,
        save_interim_parquet=False,
    )

    chunk = next(load_csv(config))
    clean = preprocess_chunk(chunk, min_text_length=5, anonymization_salt="salt")

    assert len(chunk) == 2
    assert chunk.loc[0, "comment"] == "Comment, with comma and quotes"
    assert clean["source"].unique().tolist() == ["youtube"]
    assert clean["datetime"].notna().all()
