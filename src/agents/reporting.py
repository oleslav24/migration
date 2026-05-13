from __future__ import annotations

from pathlib import Path
from typing import Any

from .context_pack import _resolve_output_root, utc_now
from .contracts import load_contract
from .report_i18n import rt


def export_context_report(
    contract_path: str | Path,
    context_pack: dict[str, Any],
    evidence_pack: dict[str, Any] | None = None,
    workspace: str | Path = ".",
    output_root: str | Path | None = None,
    report_language: str = "en",
) -> Path:
    contract = load_contract(contract_path)
    root = _resolve_output_root(contract, workspace, output_root)
    path = root / "context_report.md"
    lines = [
        f"# {rt(report_language, 'context.title')}: {contract.agent_id}",
        "",
        f"{rt(report_language, 'created')}: `{utc_now()}`",
        f"{rt(report_language, 'contract')}: `{contract.path}`",
        "",
        f"## {rt(report_language, 'allowed_context')}",
        "",
        f"- {rt(report_language, 'read')}: {', '.join(contract.read_paths) if contract.read_paths else 'none'}",
        f"- {rt(report_language, 'write')}: {', '.join(contract.write_paths) if contract.write_paths else 'none'}",
        f"- {rt(report_language, 'external')}: {', '.join(contract.raw.get('allowed_context', {}).get('external', [])) or 'none'}",
        "",
        f"## {rt(report_language, 'datasets')}",
        "",
    ]
    datasets = context_pack.get("datasets", [])
    if not datasets:
        lines.append(rt(report_language, "no_datasets"))
    for item in datasets:
        lines.extend(
            [
                f"### {item.get('filename')}",
                "",
                f"- {rt(report_language, 'path')}: `{item.get('path')}`",
                f"- {rt(report_language, 'type')}: `{item.get('kind')}`",
                f"- {rt(report_language, 'readable')}: `{item.get('readable')}`",
                f"- {rt(report_language, 'rows')}: `{item.get('row_count', 'n/a')}`",
                f"- {rt(report_language, 'columns')}: {', '.join(item.get('columns', [])) if item.get('columns') else 'n/a'}",
            ]
        )
        if item.get("date_min") or item.get("date_max"):
            lines.append(f"- {rt(report_language, 'date_range')}: `{item.get('date_min')}` to `{item.get('date_max')}` ({item.get('date_range_scope')})")
        if item.get("error"):
            lines.append(f"- {rt(report_language, 'error')}: `{item.get('error')}`")
        lines.append("")
    if evidence_pack is not None:
        lines.extend(
            [
                f"## {rt(report_language, 'evidence_pack')}",
                "",
                f"- {rt(report_language, 'evidence_items')}: `{len(evidence_pack.get('evidence_items', []))}`",
                f"- {rt(report_language, 'aggregate_items')}: `{len(evidence_pack.get('aggregate_items', []))}`",
                f"- {rt(report_language, 'evidence_path')}: `{evidence_pack.get('evidence_pack_path', 'n/a')}`",
                "",
            ]
        )
        for item in evidence_pack.get("evidence_items", [])[:10]:
            lines.extend(
                [
                    f"### {item.get('evidence_id')}",
                    "",
                    f"{rt(report_language, 'source')}: `{item.get('source_path')}`",
                    "",
                    "> " + str(item.get("text", "")).replace("\n", " ")[:500],
                    "",
                ]
            )
    limitations = list(context_pack.get("limitations", []))
    if evidence_pack is not None:
        limitations.extend(evidence_pack.get("limitations", []))
    lines.extend([f"## {rt(report_language, 'limitations')}", ""])
    if limitations:
        for limitation in limitations:
            lines.append(f"- {limitation}")
    else:
        lines.append(f"- {rt(report_language, 'no_limitations')}")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
