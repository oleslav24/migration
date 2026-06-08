from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def load_codebook(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("Codebook must be a YAML mapping.")
    return data


def validate_codebook(codebook: dict) -> list[str]:
    errors: list[str] = []
    entries = _codes(codebook)
    seen: set[str] = set()
    ids = {entry.get("code_id") for entry in entries if entry.get("code_id")}
    for index, entry in enumerate(entries):
        code_id = str(entry.get("code_id") or "").strip()
        if not code_id:
            errors.append(f"codes[{index}] is missing code_id")
            continue
        if code_id in seen:
            errors.append(f"Duplicate code_id: {code_id}")
        seen.add(code_id)
        description = str(entry.get("description") or "").strip()
        if not description:
            errors.append(f"code_id={code_id} has empty description")
        parent = str(entry.get("parent_id") or "").strip()
        if parent and parent not in ids:
            errors.append(f"code_id={code_id} has unknown parent_id={parent}")
    return errors


def flatten_codes(codebook: dict) -> pd.DataFrame:
    rows = []
    for entry in _codes(codebook):
        rows.append(
            {
                "code_id": entry.get("code_id"),
                "parent_id": entry.get("parent_id"),
                "name_ru": entry.get("name_ru"),
                "name_en": entry.get("name_en"),
                "description": entry.get("description"),
                "mutually_exclusive_group": entry.get("mutually_exclusive_group"),
            }
        )
    return pd.DataFrame(rows)


def get_codes_by_group(codebook: dict, group_name: str) -> list[str]:
    result: list[str] = []
    for entry in _codes(codebook):
        if str(entry.get("mutually_exclusive_group") or "").strip() == group_name:
            code_id = str(entry.get("code_id") or "").strip()
            if code_id:
                result.append(code_id)
    return sorted(set(result))


def _codes(codebook: dict) -> list[dict]:
    wrapper = codebook.get("codebook", codebook)
    codes = wrapper.get("codes", [])
    if not isinstance(codes, list):
        raise ValueError("Codebook field 'codes' must be a list.")
    return [item for item in codes if isinstance(item, dict)]

