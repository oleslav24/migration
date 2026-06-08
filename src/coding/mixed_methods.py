from __future__ import annotations

import json

import pandas as pd


def code_matrix(
    annotations: pd.DataFrame,
    rows: str,
    columns: str,
    normalize: str | None = None,
) -> pd.DataFrame:
    table = _explode_field(annotations, rows)
    table = _explode_field(table, columns)
    result = pd.crosstab(table[rows], table[columns], dropna=False)
    if normalize is None:
        return result.reset_index()
    norm = normalize.lower()
    if norm == "row":
        result = result.div(result.sum(axis=1), axis=0).fillna(0)
    elif norm == "column":
        result = result.div(result.sum(axis=0), axis=1).fillna(0)
    elif norm == "all":
        total = result.to_numpy().sum()
        result = result / total if total else result
    else:
        raise ValueError("normalize must be one of: None|row|column|all")
    return result.reset_index()


def _explode_field(frame: pd.DataFrame, field: str) -> pd.DataFrame:
    if field not in frame.columns:
        raise ValueError(f"Column not found: {field}")
    data = frame.copy()
    data[field] = data[field].map(_as_list_or_scalar)
    return data.explode(field, ignore_index=True)


def _as_list_or_scalar(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ["unknown"]
    if isinstance(value, list):
        normalized = [str(item).strip() for item in value if str(item).strip()]
        return normalized or ["unknown"]
    text = str(value).strip()
    if not text:
        return ["unknown"]
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                normalized = [str(item).strip() for item in parsed if str(item).strip()]
                return normalized or ["unknown"]
        except Exception:
            pass
    if ";" in text:
        normalized = [item.strip() for item in text.split(";") if item.strip()]
        return normalized or ["unknown"]
    return [text]

