from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.migration_drivers import DRIVER_CATEGORIES, add_migration_driver_column

from .report_i18n import rt
from .table_utils import ensure_toponyms, output_root_for, read_context_tables, text_column, write_json


def run_migration_narrative_agent(contract_path: str | Path, workspace: str | Path = ".", output_root: str | Path | None = None, report_language: str = "en") -> dict[str, Any]:
    context_pack, frame = read_context_tables(contract_path, workspace, output_root)
    root = output_root_for(contract_path, workspace, output_root, "data/agent_migration_narratives")
    column = text_column(frame)
    limitations: list[str] = []
    if frame.empty or column is None:
        limitations.append("No text-bearing tables were available for narrative analysis.")
        evidence = []
        matrix = pd.DataFrame(columns=["migration_driver", "count", "evidence_count", "status"])
    else:
        frame = ensure_toponyms(frame)
        if "migration_driver" not in frame:
            frame = add_migration_driver_column(frame, column)
        evidence = _evidence(frame, column)
        matrix = _matrix(frame, evidence)
    write_json(root / "migration_narrative_evidence.json", {"context_pack_path": context_pack.get("context_pack_path"), "evidence_items": evidence, "limitations": limitations})
    matrix.to_csv(root / "migration_narrative_matrix.csv", index=False, encoding="utf-8")
    report_path = _report(root, evidence, matrix, limitations, report_language)
    return {"output_dir": str(root), "report_path": str(report_path), "evidence_items": len(evidence), "limitations": limitations, "report_language": report_language}


def _evidence(frame: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    items = []
    for category in DRIVER_CATEGORIES:
        sample = frame[frame["migration_driver"] == category].head(5)
        for _, row in sample.iterrows():
            items.append({"evidence_id": f"narrative:{category}:row:{row.get('row_index')}", "migration_driver": category, "source_path": row.get("source_path"), "row_index": row.get("row_index"), "text": str(row.get(column, ""))[:1200]})
    return items


def _matrix(frame: pd.DataFrame, evidence: list[dict[str, Any]]) -> pd.DataFrame:
    counts = frame["migration_driver"].value_counts().reindex(DRIVER_CATEGORIES, fill_value=0)
    evidence_counts = pd.Series([item["migration_driver"] for item in evidence]).value_counts().reindex(DRIVER_CATEGORIES, fill_value=0)
    return pd.DataFrame({"migration_driver": DRIVER_CATEGORIES, "count": counts.values, "evidence_count": evidence_counts.values, "status": ["observed evidence" if c else "absent evidence" for c in counts.values]})


def _report(root: Path, evidence: list[dict[str, Any]], matrix: pd.DataFrame, limitations: list[str], report_language: str = "en") -> Path:
    lines = [f"# {rt(report_language, 'migration_report')}", "", f"## {rt(report_language, 'quant_distribution')}", "", "```csv", matrix.to_csv(index=False).strip(), "```", "", f"## {rt(report_language, 'observed_evidence')}", ""]
    if not evidence:
        lines.append(rt(report_language, "no_narrative_evidence"))
    for item in evidence:
        lines.append(f"### {item['evidence_id']}")
        lines.append(f"{rt(report_language, 'driver')}: `{item['migration_driver']}`")
        lines.append(f"{rt(report_language, 'source')}: `{item['source_path']}` {rt(report_language, 'row')} `{item['row_index']}`")
        lines.append("")
        lines.append("> " + item["text"].replace("\n", " ")[:500])
        lines.append("")
    lines.extend([f"## {rt(report_language, 'interpretation_notes')}", "", f"- {rt(report_language, 'migration_note')}", "", f"## {rt(report_language, 'limitations')}", ""])
    for limitation in limitations or [rt(report_language, "migration_default_limitation")]:
        lines.append(f"- {limitation}")
    path = root / "migration_narrative_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
