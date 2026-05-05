from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from .context_pack import _resolve_output_root, utc_now
from .contracts import load_contract


TEXT_COLUMNS = ["text", "comment", "message"]
GROUP_COLUMNS = ["source", "group", "language", "sentiment", "migration_driver", "topic_id"]
TOPONYM_COLUMNS = ["toponyms"]


def build_evidence_pack(
    contract_path: str | Path,
    context_pack: dict[str, Any],
    workspace: str | Path = ".",
    output_root: str | Path | None = None,
    max_samples_per_dataset: int = 5,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    evidence_items: list[dict[str, Any]] = []
    aggregate_items: list[dict[str, Any]] = []

    for dataset in context_pack.get("datasets", []):
        if dataset.get("kind") != "table" or not dataset.get("readable", False):
            continue
        path = Path(dataset["path"])
        frame = _read_table_sample(path)
        evidence_items.extend(_sample_texts(frame, dataset, max_samples_per_dataset))
        aggregate_items.extend(_aggregate_signals(frame, dataset))

    pack = {
        "agent_id": contract.agent_id,
        "created_at": utc_now(),
        "contract_path": str(contract.path),
        "context_pack_path": context_pack.get("context_pack_path"),
        "evidence_items": evidence_items,
        "aggregate_items": aggregate_items,
        "limitations": _evidence_limitations(evidence_items, aggregate_items),
    }
    path = write_evidence_pack(pack, contract_path, workspace, output_root)
    pack["evidence_pack_path"] = str(path)
    return pack


def _read_table_sample(path: Path, nrows: int = 500) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path).head(nrows)
    return pd.read_csv(path, nrows=nrows, encoding="utf-8", on_bad_lines="skip")


def _sample_texts(frame: pd.DataFrame, dataset: dict[str, Any], max_samples: int) -> list[dict[str, Any]]:
    text_column = next((column for column in TEXT_COLUMNS if column in frame.columns), None)
    if text_column is None:
        return []
    sample = frame[frame[text_column].notna()].head(max_samples)
    items: list[dict[str, Any]] = []
    for index, row in sample.iterrows():
        items.append(
            {
                "evidence_id": f"{Path(dataset['filename']).stem}:row:{index}",
                "type": "text_sample",
                "source_path": dataset["path"],
                "filename": dataset["filename"],
                "row_index": int(index),
                "text_column": text_column,
                "text": str(row[text_column])[:1200],
            }
        )
    return items


def _aggregate_signals(frame: pd.DataFrame, dataset: dict[str, Any]) -> list[dict[str, Any]]:
    aggregates: list[dict[str, Any]] = []
    for column in GROUP_COLUMNS:
        if column in frame.columns:
            counts = frame[column].fillna("missing").astype(str).value_counts().head(20)
            aggregates.append(
                {
                    "aggregate_id": f"{Path(dataset['filename']).stem}:{column}:distribution",
                    "type": "distribution",
                    "source_path": dataset["path"],
                    "filename": dataset["filename"],
                    "column": column,
                    "values": counts.to_dict(),
                    "scope": "sample_500_rows",
                }
            )
    for column in TOPONYM_COLUMNS:
        if column in frame.columns:
            counter = Counter()
            for value in frame[column].dropna().astype(str):
                for item in _parse_listish(value):
                    counter[item] += 1
            aggregates.append(
                {
                    "aggregate_id": f"{Path(dataset['filename']).stem}:{column}:frequency",
                    "type": "toponym_frequency",
                    "source_path": dataset["path"],
                    "filename": dataset["filename"],
                    "column": column,
                    "values": dict(counter.most_common(20)),
                    "scope": "sample_500_rows",
                }
            )
    return aggregates


def _parse_listish(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped or stripped in {"[]", "nan"}:
        return []
    try:
        payload = json.loads(stripped.replace("'", '"'))
        if isinstance(payload, list):
            return [str(item) for item in payload]
    except json.JSONDecodeError:
        pass
    return [part.strip() for part in stripped.strip("[]").split(",") if part.strip()]


def _evidence_limitations(evidence_items: list[dict[str, Any]], aggregate_items: list[dict[str, Any]]) -> list[str]:
    limitations: list[str] = []
    if not evidence_items:
        limitations.append("No text evidence samples were found in the discovered context.")
    if not aggregate_items:
        limitations.append("No aggregate signals were produced from the discovered context.")
    limitations.append("Evidence aggregates are computed from bounded samples unless precomputed exports are provided.")
    return limitations


def write_evidence_pack(
    pack: dict[str, Any],
    contract_path: str | Path,
    workspace: str | Path,
    output_root: str | Path | None = None,
) -> Path:
    contract = load_contract(contract_path)
    root = _resolve_output_root(contract, workspace, output_root)
    target = root / "evidence_pack.json"
    target.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    return target

