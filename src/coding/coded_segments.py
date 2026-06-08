from __future__ import annotations

import json

import pandas as pd


def get_coded_segments(
    annotations: pd.DataFrame,
    code: str,
    field: str | None = None,
) -> pd.DataFrame:
    data = annotations.copy()
    if field:
        if field not in data.columns:
            raise ValueError(f"Field not found: {field}")
        mask = data[field].map(lambda value: code in _as_list(value))
    else:
        candidate_fields = [column for column in data.columns if column not in {"annotation_id", "doc_id", "text", "memo"}]
        mask = pd.Series(False, index=data.index)
        for column in candidate_fields:
            mask = mask | data[column].map(lambda value: code in _as_list(value))
    return data.loc[mask].reset_index(drop=True)


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
    return [item.strip() for item in text.split(";") if item.strip()]

