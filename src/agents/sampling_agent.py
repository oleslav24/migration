from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .report_i18n import rt
from .table_utils import ensure_period, ensure_toponyms, output_root_for, read_context_tables, text_column


MANUAL_COLUMNS = ["manual_relevance", "manual_place_frame", "manual_migration_driver", "manual_notes", "coder_id"]
DEFAULT_STRATA = ["source", "month", "toponym", "migration_driver", "sentiment", "topic_id"]


def run_sampling_coding_agent(contract_path: str | Path, workspace: str | Path = ".", output_root: str | Path | None = None, sample_size: int = 100, random_state: int = 42, report_language: str = "en") -> dict[str, Any]:
    _, frame = read_context_tables(contract_path, workspace, output_root)
    root = output_root_for(contract_path, workspace, output_root, "data/agent_sampling")
    if frame.empty:
        sample = pd.DataFrame(columns=[*MANUAL_COLUMNS])
    else:
        frame = ensure_period(ensure_toponyms(frame))
        frame = frame.explode("toponyms").rename(columns={"toponyms": "toponym"})
        frame["sample_id"] = [f"sample:{i}" for i in range(len(frame))]
        sample = _stratified_sample(frame, sample_size, random_state)
        for column in MANUAL_COLUMNS:
            sample[column] = ""
    sample.to_csv(root / "coding_sample.csv", index=False, encoding="utf-8")
    sample.to_csv(root / "intercoder_template.csv", index=False, encoding="utf-8")
    codebook = _codebook(report_language)
    (root / "coding_codebook.md").write_text(codebook, encoding="utf-8")
    manifest = {"sample_size_requested": sample_size, "sample_size_actual": int(len(sample)), "random_state": random_state, "strata": DEFAULT_STRATA, "manual_columns": MANUAL_COLUMNS}
    (root / "coding_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output_dir": str(root), "sample_size": len(sample), "manifest": manifest, "report_language": report_language}


def _stratified_sample(frame: pd.DataFrame, sample_size: int, random_state: int) -> pd.DataFrame:
    cols = [c for c in DEFAULT_STRATA if c in frame.columns]
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
