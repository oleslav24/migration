from __future__ import annotations

from pathlib import Path
from typing import Any

from .context_pack import prepare_context_pack
from .evidence_pack import build_evidence_pack
from .reporting import export_context_report


def prepare_corpus_context(
    contract_path: str | Path,
    workspace: str | Path = ".",
    output_root: str | Path | None = None,
    report_language: str = "en",
) -> dict[str, Any]:
    context_pack = prepare_context_pack(contract_path, workspace, output_root)
    report_path = export_context_report(contract_path, context_pack, None, workspace, output_root, report_language)
    context_pack["context_report_path"] = str(report_path)
    return context_pack


def analyze_corpus_context(
    contract_path: str | Path,
    workspace: str | Path = ".",
    output_root: str | Path | None = None,
    report_language: str = "en",
) -> dict[str, Any]:
    context_pack = prepare_context_pack(contract_path, workspace, output_root)
    evidence_pack = build_evidence_pack(contract_path, context_pack, workspace, output_root)
    report_path = export_context_report(contract_path, context_pack, evidence_pack, workspace, output_root, report_language)
    return {
        "context_pack": context_pack,
        "evidence_pack": evidence_pack,
        "context_report_path": str(report_path),
    }
