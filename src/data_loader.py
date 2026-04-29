from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from .config import PipelineConfig


REQUIRED_COLUMNS = ["datetime", "author", "group", "comment"]


def _validate_columns(columns: list[str]) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {missing}")


def load_csv(config: PipelineConfig) -> Iterator[pd.DataFrame]:
    """Read the input CSV in chunks and validate the schema."""
    input_path = Path(config.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    total_rows = 0
    reader = pd.read_csv(
        input_path,
        chunksize=config.chunk_size,
        dtype={"author": "string", "group": "string", "comment": "string"},
        keep_default_na=True,
        encoding="utf-8",
        on_bad_lines="skip",
    )

    for chunk in reader:
        _validate_columns(list(chunk.columns))
        if config.max_rows is not None:
            remaining = config.max_rows - total_rows
            if remaining <= 0:
                break
            chunk = chunk.head(remaining)
        total_rows += len(chunk)
        yield chunk[REQUIRED_COLUMNS].copy()

