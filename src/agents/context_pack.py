from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .access import assert_write_allowed, check_read_context
from .contracts import AgentContract, load_contract


DATA_SUFFIXES = {".csv", ".parquet", ".json", ".yaml", ".yml"}
TABLE_SUFFIXES = {".csv", ".parquet"}
MAX_DISCOVERED_FILES = 200
MAX_SAMPLE_ROWS = 5
MAX_FULL_DATE_SCAN_BYTES = 50_000_000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def prepare_context_pack(
    contract_path: str | Path,
    workspace: str | Path = ".",
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    context_paths = check_read_context(contract, workspace)
    datasets = discover_context_files(context_paths)
    summaries = [summarize_context_file(path) for path in datasets]
    pack = {
        "agent_id": contract.agent_id,
        "created_at": utc_now(),
        "contract_path": str(contract.path),
        "allowed_context": {
            "read": contract.read_paths,
            "write": contract.write_paths,
            "external": contract.raw.get("allowed_context", {}).get("external", []),
        },
        "context_paths_checked": [str(path) for path in context_paths],
        "datasets": summaries,
        "limitations": _context_limitations(summaries),
    }
    path = write_context_pack(pack, contract, workspace, output_root)
    pack["context_pack_path"] = str(path)
    return pack


def discover_context_files(context_paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in context_paths:
        if path.is_file() and path.suffix.lower() in DATA_SUFFIXES:
            files.append(path)
        elif path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in DATA_SUFFIXES:
                    files.append(candidate)
                    if len(files) >= MAX_DISCOVERED_FILES:
                        return sorted(files)
    return sorted(dict.fromkeys(files))


def summarize_context_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    summary: dict[str, Any] = {
        "path": str(path),
        "filename": path.name,
        "extension": suffix,
        "size_bytes": path.stat().st_size,
        "kind": "table" if suffix in TABLE_SUFFIXES else "metadata",
    }
    try:
        if suffix == ".csv":
            summary.update(_summarize_csv(path))
        elif suffix == ".parquet":
            summary.update(_summarize_parquet(path))
        elif suffix == ".json":
            summary.update(_summarize_json(path))
        else:
            summary["readable"] = True
    except Exception as exc:  # pragma: no cover - defensive for corrupted local files
        summary["readable"] = False
        summary["error"] = str(exc)
    return summary


def _summarize_csv(path: Path) -> dict[str, Any]:
    sample = pd.read_csv(path, nrows=MAX_SAMPLE_ROWS, encoding="utf-8", on_bad_lines="skip")
    summary = {
        "readable": True,
        "columns": list(sample.columns),
        "row_count": _count_csv_rows(path),
        "sample_rows": _records(sample),
    }
    summary.update(_date_range(path, sample))
    return summary


def _summarize_parquet(path: Path) -> dict[str, Any]:
    frame = pd.read_parquet(path)
    sample = frame.head(MAX_SAMPLE_ROWS)
    summary = {
        "readable": True,
        "columns": list(frame.columns),
        "row_count": int(len(frame)),
        "sample_rows": _records(sample),
    }
    summary.update(_date_range(path, frame))
    return summary


def _summarize_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        top_level = list(payload.keys())
    else:
        top_level = [type(payload).__name__]
    return {"readable": True, "top_level_keys": top_level}


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    safe = frame.astype("object").where(pd.notnull(frame), None)
    return safe.to_dict(orient="records")


def _count_csv_rows(path: Path) -> int:
    with path.open("rb") as handle:
        lines = sum(1 for _ in handle)
    return max(lines - 1, 0)


def _date_range(path: Path, frame: pd.DataFrame) -> dict[str, Any]:
    candidates = [column for column in ["datetime", "date", "created_at", "month", "period"] if column in frame.columns]
    if not candidates:
        return {}
    column = candidates[0]
    if path.suffix.lower() == ".csv" and path.stat().st_size <= MAX_FULL_DATE_SCAN_BYTES:
        values = pd.read_csv(path, usecols=[column], encoding="utf-8", on_bad_lines="skip")[column]
        scope = "full_file"
    else:
        values = frame[column]
        scope = "sample"
    parsed = pd.to_datetime(values, errors="coerce", utc=True, dayfirst=True)
    parsed = parsed.dropna()
    if parsed.empty:
        return {"date_column": column, "date_range_scope": scope}
    return {
        "date_column": column,
        "date_min": parsed.min().isoformat(),
        "date_max": parsed.max().isoformat(),
        "date_range_scope": scope,
    }


def _context_limitations(summaries: list[dict[str, Any]]) -> list[str]:
    limitations: list[str] = []
    if not summaries:
        limitations.append("No readable local context files were discovered.")
    if any(item.get("date_range_scope") == "sample" for item in summaries):
        limitations.append("Some date ranges are sample-based for large files.")
    if any(not item.get("readable", False) for item in summaries):
        limitations.append("Some files could not be read and were preserved as errors in the context pack.")
    return limitations


def write_context_pack(
    pack: dict[str, Any],
    contract: AgentContract,
    workspace: str | Path,
    output_root: str | Path | None = None,
) -> Path:
    root = _resolve_output_root(contract, workspace, output_root)
    target = root / "context_pack.json"
    target.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def _resolve_output_root(
    contract: AgentContract,
    workspace: str | Path,
    output_root: str | Path | None = None,
) -> Path:
    preferred = Path(output_root) if output_root else Path("data") / "agent_context" / contract.agent_id
    try:
        target = assert_write_allowed(preferred, contract, workspace)
        target.mkdir(parents=True, exist_ok=True)
        return target
    except PermissionError:
        fallback = assert_write_allowed(Path("tmp_write_check") / "agent_context" / contract.agent_id, contract, workspace)
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
