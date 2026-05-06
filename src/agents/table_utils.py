from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .context_pack import prepare_context_pack
from .contracts import load_contract


TEXT_COLUMNS = ["text", "comment", "message"]


def read_context_tables(contract_path: str | Path, workspace: str | Path = ".", output_root: str | Path | None = None) -> tuple[dict[str, Any], pd.DataFrame]:
    context_pack = prepare_context_pack(contract_path, workspace, output_root)
    frames: list[pd.DataFrame] = []
    for dataset in context_pack.get("datasets", []):
        if dataset.get("kind") != "table" or not dataset.get("readable", False):
            continue
        path = Path(dataset["path"])
        try:
            frame = pd.read_parquet(path) if path.suffix.lower() == ".parquet" else pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
        except Exception:
            continue
        frame = frame.copy()
        frame["source_path"] = str(path)
        frame["source_file"] = path.name
        frame["row_index"] = frame.index.astype(int)
        frames.append(frame)
    if not frames:
        return context_pack, pd.DataFrame()
    return context_pack, pd.concat(frames, ignore_index=True, sort=False)


def text_column(frame: pd.DataFrame) -> str | None:
    return next((column for column in TEXT_COLUMNS if column in frame.columns), None)


def parse_listish(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None or (not isinstance(value, (list, tuple, dict)) and pd.isna(value)):
        return []
    raw = str(value).strip()
    if not raw or raw.lower() in {"nan", "none", "[]"}:
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(raw)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    if ";" in raw:
        return [part.strip() for part in raw.split(";") if part.strip()]
    return [part.strip().strip("'\"") for part in raw.strip("[]").split(",") if part.strip().strip("'\"")]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def output_root_for(contract_path: str | Path, workspace: str | Path, output_root: str | Path | None, default_dir: str) -> Path:
    contract = load_contract(contract_path)
    if output_root is not None:
        root = Path(workspace) / output_root if not Path(output_root).is_absolute() else Path(output_root)
    else:
        root = Path(workspace) / default_dir / contract.agent_id
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write_check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return root
    except OSError:
        fallback = Path(workspace) / "tmp_write_check" / default_dir.replace("data/", "") / contract.agent_id
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def ensure_toponyms(frame: pd.DataFrame) -> pd.DataFrame:
    from src.toponyms import add_toponyms_column

    result = frame.copy()
    if "toponyms" in result:
        result["toponyms"] = result["toponyms"].map(parse_listish)
        return result
    column = text_column(result)
    if column is None:
        result["toponyms"] = [[] for _ in range(len(result))]
        return result
    return add_toponyms_column(result, column)


def ensure_period(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "month" in result:
        return result
    if "period" in result:
        result["month"] = result["period"].astype(str).str.slice(0, 7)
        return result
    if "datetime" in result:
        parsed = pd.to_datetime(result["datetime"], errors="coerce", utc=True, dayfirst=True)
        result["month"] = parsed.dt.tz_convert(None).dt.to_period("M").astype("string")
    return result

