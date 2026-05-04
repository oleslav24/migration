from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig


REQUIRED_COLUMNS = ["datetime", "author", "group", "comment"]
OUTPUT_COLUMNS = [*REQUIRED_COLUMNS, "source"]


def _validate_columns(columns: list[str]) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {missing}")


def load_csv(config: PipelineConfig) -> Iterator[pd.DataFrame]:
    """Read configured CSV inputs in chunks and normalize them to the pipeline schema."""
    total_rows = 0
    for item in _configured_inputs(config):
        input_path = _resolve_input_path(Path(item["path"]))
        source = item["source"]
        for chunk in _load_one_csv(input_path, source, config.chunk_size):
            if config.max_rows is not None:
                remaining = config.max_rows - total_rows
                if remaining <= 0:
                    return
                chunk = chunk.head(remaining)
            total_rows += len(chunk)
            yield chunk[OUTPUT_COLUMNS].copy()


def _load_one_csv(input_path: Path, source: str, chunk_size: int) -> Iterator[pd.DataFrame]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    if _needs_line_parser(input_path):
        yield from _load_line_parsed_csv(input_path, source, chunk_size)
        return

    reader = pd.read_csv(
        input_path,
        chunksize=chunk_size,
        dtype={"author": "string", "group": "string", "comment": "string"},
        keep_default_na=True,
        encoding="utf-8",
        on_bad_lines="skip",
    )
    for chunk in reader:
        _validate_columns(list(chunk.columns))
        chunk = chunk[REQUIRED_COLUMNS].copy()
        chunk["source"] = source
        yield chunk


def _load_line_parsed_csv(input_path: Path, source: str, chunk_size: int) -> Iterator[pd.DataFrame]:
    rows: list[dict[str, str]] = []
    with input_path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        header = handle.readline()
        _validate_columns(next(csv.reader([header.strip()])))
        for line in handle:
            parsed = _parse_malformed_csv_line(line)
            if parsed is None:
                continue
            parsed["source"] = source
            rows.append(parsed)
            if len(rows) >= chunk_size:
                yield pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
                rows = []
    if rows:
        yield pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def _parse_malformed_csv_line(line: str) -> dict[str, str] | None:
    raw = line.strip()
    if not raw:
        return None
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1].replace('""', '"')
    row = next(csv.reader([raw]))
    if len(row) < 4:
        return None
    if len(row) > 4:
        row = [row[0], row[1], row[2], ",".join(row[3:])]
    return dict(zip(REQUIRED_COLUMNS, row, strict=True))


def _needs_line_parser(input_path: Path) -> bool:
    return input_path.name.lower().startswith("youtube_")


def _configured_inputs(config: PipelineConfig) -> list[dict[str, Any]]:
    if config.input_paths:
        result = []
        for item in config.input_paths:
            if isinstance(item, str):
                result.append({"path": item, "source": _source_from_path(item)})
            else:
                result.append({"path": item["path"], "source": item.get("source", _source_from_path(item["path"]))})
        return result
    return [{"path": config.input_path, "source": _source_from_path(config.input_path)}]


def _source_from_path(path: str) -> str:
    name = Path(path).name.lower()
    if "youtube" in name:
        return "youtube"
    if "telegram" in name:
        return "telegram"
    return "unknown"


def _resolve_input_path(path: Path) -> Path:
    if path.exists():
        return path
    fallback = Path("DS") / path.name
    if fallback.exists():
        return fallback
    return path
