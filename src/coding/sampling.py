from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_annotation_sample(
    input_path: str,
    output_path: str,
    sample_size: int,
    strategy: str,
    random_state: int = 42,
    filters: dict | None = None,
) -> pd.DataFrame:
    frame = _read_table(input_path)
    frame = _apply_filters(frame, filters or {})
    if frame.empty:
        sample = frame.copy()
    else:
        sample = _sample_by_strategy(frame, sample_size, strategy, random_state, filters or {})
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    _write_table(sample, out)
    return sample


def _sample_by_strategy(frame: pd.DataFrame, n: int, strategy: str, seed: int, filters: dict) -> pd.DataFrame:
    if strategy == "random":
        return frame.sample(n=min(n, len(frame)), random_state=seed).reset_index(drop=True)
    if strategy == "by_toponym":
        top = str(filters.get("toponym", "")).strip()
        if top:
            mask = frame["toponyms"].map(lambda value: top in _as_list(value))
            frame = frame.loc[mask]
        return frame.sample(n=min(n, len(frame)), random_state=seed).reset_index(drop=True)
    if strategy == "by_period":
        group_col = "period"
    elif strategy == "by_group":
        group_col = "group"
    elif strategy == "by_topic":
        group_col = "topic_id"
    elif strategy == "stratified_toponym_period":
        return _stratified_sample(frame, n, ["toponym_primary", "period"], seed)
    elif strategy == "stratified_toponym_topic":
        return _stratified_sample(frame, n, ["toponym_primary", "topic_id"], seed)
    else:
        raise ValueError(f"Unknown sampling strategy: {strategy}")

    grouped = frame.groupby(group_col, dropna=False)
    parts = []
    per_group = max(1, n // max(1, len(grouped)))
    for _, chunk in grouped:
        parts.append(chunk.sample(n=min(per_group, len(chunk)), random_state=seed))
    result = pd.concat(parts, ignore_index=True) if parts else frame.head(0)
    if len(result) < n and len(result) < len(frame):
        missing = n - len(result)
        extra = frame.drop(result.index, errors="ignore")
        if not extra.empty:
            result = pd.concat([result, extra.sample(n=min(missing, len(extra)), random_state=seed)], ignore_index=True)
    return result.head(n).reset_index(drop=True)


def _stratified_sample(frame: pd.DataFrame, n: int, columns: list[str], seed: int) -> pd.DataFrame:
    data = frame.copy()
    data["toponym_primary"] = data["toponyms"].map(_primary_toponym)
    groups = data.groupby(columns, dropna=False)
    parts = []
    per_group = max(1, n // max(1, len(groups)))
    for _, chunk in groups:
        parts.append(chunk.sample(n=min(per_group, len(chunk)), random_state=seed))
    result = pd.concat(parts, ignore_index=True) if parts else data.head(0)
    if len(result) < n and len(result) < len(data):
        remaining = data.drop(result.index, errors="ignore")
        if not remaining.empty:
            result = pd.concat(
                [result, remaining.sample(n=min(n - len(result), len(remaining)), random_state=seed)],
                ignore_index=True,
            )
    return result.head(n).reset_index(drop=True)


def _apply_filters(frame: pd.DataFrame, filters: dict) -> pd.DataFrame:
    result = frame.copy()
    for column in ["group", "period", "topic_id"]:
        if filters.get(column):
            result = result[result[column].astype(str) == str(filters[column])]
    return result


def _read_table(path: str) -> pd.DataFrame:
    file = Path(path)
    if file.suffix.lower() == ".parquet":
        frame = pd.read_parquet(file)
    else:
        frame = pd.read_csv(file)
    _require_columns(frame, ["doc_id", "group", "period", "window_start", "text"])
    if "toponyms" not in frame.columns:
        frame["toponyms"] = ""
    if "topic_id" not in frame.columns:
        frame["topic_id"] = ""
    if "sentiment" not in frame.columns:
        frame["sentiment"] = ""
    return frame


def _write_table(frame: pd.DataFrame, path: Path) -> None:
    if path.suffix.lower() == ".xlsx":
        frame.to_excel(path, index=False)
    else:
        frame.to_csv(path, index=False, encoding="utf-8")


def _require_columns(frame: pd.DataFrame, required: list[str]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _as_list(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    if ";" in text:
        return [item.strip() for item in text.split(";") if item.strip()]
    return [text]


def _primary_toponym(value: object) -> str:
    items = _as_list(value)
    return items[0] if items else "unknown"

