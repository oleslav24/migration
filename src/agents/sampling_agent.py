from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .report_i18n import rt
from .table_utils import ensure_period, ensure_toponyms, output_root_for, read_context_tables, text_column


MANUAL_COLUMNS = ["manual_relevance", "manual_place_frame", "manual_migration_driver", "manual_notes", "coder_id"]
DEFAULT_STRATA = ["source", "month", "toponym", "migration_driver", "sentiment", "topic_id"]
TOPONYM_STRATA_CHOICES = ["source", "month", "sentiment", "topic_id", "migration_driver"]


def run_sampling_coding_agent(
    contract_path: str | Path,
    workspace: str | Path = ".",
    output_root: str | Path | None = None,
    sample_size: int = 100,
    random_state: int = 42,
    report_language: str = "en",
    toponym: str = "",
    stratify_by: str = "source",
) -> dict[str, Any]:
    _, frame = read_context_tables(contract_path, workspace, output_root)
    root = output_root_for(contract_path, workspace, output_root, "data/agent_sampling")
    toponym_value = str(toponym or "").strip()
    stratify_value = str(stratify_by or "").strip().lower() or "source"
    source_mode = "context_tables"
    source_toponym_file = None

    if toponym_value:
        toponym_frame, source_toponym_file = _load_toponym_texts_frame(workspace, toponym_value)
        frame = toponym_frame
        source_mode = "texts_by_toponym"

    if frame.empty:
        sample = pd.DataFrame(columns=[*MANUAL_COLUMNS])
        strata_used: list[str] = [stratify_value] if toponym_value else DEFAULT_STRATA
    else:
        if source_mode == "texts_by_toponym":
            frame = ensure_period(frame.copy())
            if "toponym" not in frame:
                frame["toponym"] = toponym_value
            frame["toponym"] = frame["toponym"].fillna(toponym_value).astype(str)
            strata_used = [stratify_value] if stratify_value in TOPONYM_STRATA_CHOICES else []
        else:
            frame = ensure_period(ensure_toponyms(frame))
            frame = frame.explode("toponyms").rename(columns={"toponyms": "toponym"})
            strata_used = [c for c in DEFAULT_STRATA if c in frame.columns]
        frame["sample_id"] = [f"sample:{i}" for i in range(len(frame))]
        sample = _stratified_sample(frame, sample_size, random_state, strata_used)
        for column in MANUAL_COLUMNS:
            sample[column] = ""
    sample.to_csv(root / "coding_sample.csv", index=False, encoding="utf-8")
    sample.to_csv(root / "intercoder_template.csv", index=False, encoding="utf-8")
    codebook = _codebook(report_language)
    (root / "coding_codebook.md").write_text(codebook, encoding="utf-8")
    manifest = {
        "sample_size_requested": sample_size,
        "sample_size_actual": int(len(sample)),
        "random_state": random_state,
        "strata": strata_used,
        "manual_columns": MANUAL_COLUMNS,
        "source_mode": source_mode,
        "toponym": toponym_value or None,
        "stratify_by": stratify_value if toponym_value else None,
        "source_toponym_file": source_toponym_file,
    }
    (root / "coding_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    result: dict[str, Any] = {"output_dir": str(root), "sample_size": len(sample), "manifest": manifest, "report_language": report_language}

    if toponym_value:
        sample.to_csv(root / "coding_sample_by_toponym.csv", index=False, encoding="utf-8")
        (root / "coding_codebook_toponym.md").write_text(_codebook_toponym(report_language, toponym_value, stratify_value), encoding="utf-8")
        manifest_toponym = {
            "toponym": toponym_value,
            "sample_size_requested": sample_size,
            "sample_size_actual": int(len(sample)),
            "random_state": random_state,
            "stratify_by": stratify_value,
            "allowed_stratify_by": TOPONYM_STRATA_CHOICES,
            "source_toponym_file": source_toponym_file,
            "manual_columns": MANUAL_COLUMNS,
        }
        (root / "coding_manifest_toponym.json").write_text(json.dumps(manifest_toponym, ensure_ascii=False, indent=2), encoding="utf-8")
        result["manifest_toponym"] = manifest_toponym

    return result


def _stratified_sample(frame: pd.DataFrame, sample_size: int, random_state: int, strata_columns: list[str]) -> pd.DataFrame:
    cols = [c for c in strata_columns if c in frame.columns]
    if not cols:
        return frame.sample(n=min(sample_size, len(frame)), random_state=random_state).reset_index(drop=True)
    sampled = frame.groupby(cols, dropna=False, group_keys=False).apply(lambda group: group.sample(n=1, random_state=random_state))
    if len(sampled) < min(sample_size, len(frame)):
        remaining = frame.drop(index=sampled.index, errors="ignore")
        extra = remaining.sample(n=min(sample_size - len(sampled), len(remaining)), random_state=random_state) if not remaining.empty else remaining
        sampled = pd.concat([sampled, extra])
    return sampled.head(sample_size).drop_duplicates(subset=["source_path", "row_index"]).reset_index(drop=True)


def _codebook(report_language: str = "en") -> str:
    return f"""# {rt(report_language, 'coding_codebook')}

{rt(report_language, 'fields')}:

- `manual_relevance`: {rt(report_language, 'manual_relevance')}
- `manual_place_frame`: {rt(report_language, 'manual_place_frame')}
- `manual_migration_driver`: {rt(report_language, 'manual_migration_driver')}
- `manual_notes`: {rt(report_language, 'manual_notes')}
- `coder_id`: {rt(report_language, 'coder_id')}
"""


def _codebook_toponym(report_language: str, toponym: str, stratify_by: str) -> str:
    return (
        f"# {rt(report_language, 'coding_codebook')}: {toponym}\n\n"
        f"- toponym: `{toponym}`\n"
        f"- stratify_by: `{stratify_by}`\n\n"
        + _codebook(report_language)
    )


def _load_toponym_texts_frame(workspace: str | Path, toponym: str) -> tuple[pd.DataFrame, str | None]:
    root = Path(workspace)
    file_path = _resolve_toponym_csv_path(root, toponym)
    if file_path is None or not file_path.exists():
        return pd.DataFrame(), None
    frame = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
    if "source_path" not in frame:
        frame["source_path"] = str(file_path)
    if "row_index" not in frame:
        frame["row_index"] = frame.index.astype(int)
    return frame, str(file_path)


def _resolve_toponym_csv_path(workspace: Path, toponym: str) -> Path | None:
    run_manifest = workspace / "tmp_write_check" / "agent_experiments" / "toponym_research_workflow" / "run_manifest.json"
    candidates: list[Path] = []
    if run_manifest.exists():
        try:
            manifest_data = json.loads(run_manifest.read_text(encoding="utf-8"))
            result = manifest_data.get("result", {}) if isinstance(manifest_data, dict) else {}
            output_dir = result.get("output_dir")
            if output_dir:
                root = workspace / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)
                candidates.append(root)
        except Exception:
            pass
    for base in [workspace / "data" / "agent_toponyms", workspace / "tmp_write_check" / "agent_toponyms"]:
        if base.exists():
            candidates.extend([item for item in base.iterdir() if item.is_dir()])

    seen: set[str] = set()
    for candidate in sorted(candidates, key=lambda item: item.stat().st_mtime if item.exists() else 0.0, reverse=True):
        key = str(candidate.resolve())
        if key in seen:
            continue
        seen.add(key)
        match = _match_toponym_file(candidate, toponym)
        if match is not None:
            return match
    return None


def _match_toponym_file(root: Path, toponym: str) -> Path | None:
    manifest_path = root / "texts_by_toponym_manifest.json"
    target = (root / "texts_by_toponym")
    toponym_lc = toponym.strip().lower()
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            for item in payload.get("items", []):
                if str(item.get("toponym", "")).strip().lower() == toponym_lc:
                    path = root / str(item.get("path", ""))
                    if path.exists():
                        return path
        except Exception:
            pass
    if not target.exists():
        return None
    safe = _safe_filename(toponym) + ".csv"
    path = target / safe
    if path.exists():
        return path
    return None


def _safe_filename(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "_" for char in str(value)).strip("_")
    return safe or "toponym"
