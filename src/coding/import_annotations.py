from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from .codebook import get_codes_by_group, load_codebook


def import_annotation_file(
    path: str,
    schema_path: str,
    codebook_path: str,
) -> pd.DataFrame:
    frame = _read_table(path)
    schema = _load_schema(schema_path)
    codebook = load_codebook(codebook_path)
    _validate_required_columns(frame, schema)
    _validate_rows(frame, schema, codebook)
    return frame


def _read_table(path: str) -> pd.DataFrame:
    file = Path(path)
    if file.suffix.lower() == ".xlsx":
        return pd.read_excel(file, sheet_name="annotations")
    return pd.read_csv(file)


def _load_schema(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("Schema must be a YAML mapping.")
    return data


def _validate_required_columns(frame: pd.DataFrame, schema: dict) -> None:
    required = [field["name"] for field in schema.get("fields", []) if field.get("required")]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required annotation columns: {missing}")


def _validate_rows(frame: pd.DataFrame, schema: dict, codebook: dict) -> None:
    field_map = {field["name"]: field for field in schema.get("fields", []) if field.get("name")}
    if "doc_id" in frame.columns and frame["doc_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Column doc_id contains empty values.")
    if "coder_id" in frame.columns and frame["coder_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Column coder_id contains empty values.")

    for name, field in field_map.items():
        if name not in frame.columns:
            continue
        required = bool(field.get("required"))
        field_type = str(field.get("type") or "")
        allowed_group = str(field.get("allowed_codes_group") or "")
        allowed_codes = set(get_codes_by_group(codebook, allowed_group)) if allowed_group else set()
        for idx, value in frame[name].items():
            if _is_empty(value):
                if required:
                    raise ValueError(f"Required field '{name}' is empty at row {idx}.")
                continue
            if field_type == "multi_category":
                items = _split_multi(value)
                if allowed_codes:
                    unknown = [item for item in items if item not in allowed_codes]
                    if unknown:
                        raise ValueError(f"Unknown code(s) in field '{name}' at row {idx}: {unknown}")
            elif field_type == "category":
                item = str(value).strip()
                if allowed_codes and item not in allowed_codes:
                    raise ValueError(f"Unknown code in field '{name}' at row {idx}: {item}")


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return str(value).strip() == ""


def _split_multi(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    return [item.strip() for item in text.split(";") if item.strip()]

