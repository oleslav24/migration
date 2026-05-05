from __future__ import annotations

from pathlib import Path
from typing import Any

from .context_pack import _resolve_output_root, utc_now
from .contracts import load_contract


def export_context_report(
    contract_path: str | Path,
    context_pack: dict[str, Any],
    evidence_pack: dict[str, Any] | None = None,
    workspace: str | Path = ".",
    output_root: str | Path | None = None,
) -> Path:
    contract = load_contract(contract_path)
    root = _resolve_output_root(contract, workspace, output_root)
    path = root / "context_report.md"
    lines = [
        f"# Context Report: {contract.agent_id}",
        "",
        f"Created: `{utc_now()}`",
        f"Contract: `{contract.path}`",
        "",
        "## Allowed Context",
        "",
        f"- Read: {', '.join(contract.read_paths) if contract.read_paths else 'none'}",
        f"- Write: {', '.join(contract.write_paths) if contract.write_paths else 'none'}",
        f"- External: {', '.join(contract.raw.get('allowed_context', {}).get('external', [])) or 'none'}",
        "",
        "## Datasets",
        "",
    ]
    datasets = context_pack.get("datasets", [])
    if not datasets:
        lines.append("No datasets were discovered.")
    for item in datasets:
        lines.extend(
            [
                f"### {item.get('filename')}",
                "",
                f"- Path: `{item.get('path')}`",
                f"- Type: `{item.get('kind')}`",
                f"- Readable: `{item.get('readable')}`",
                f"- Rows: `{item.get('row_count', 'n/a')}`",
                f"- Columns: {', '.join(item.get('columns', [])) if item.get('columns') else 'n/a'}",
            ]
        )
        if item.get("date_min") or item.get("date_max"):
            lines.append(f"- Date range: `{item.get('date_min')}` to `{item.get('date_max')}` ({item.get('date_range_scope')})")
        if item.get("error"):
            lines.append(f"- Error: `{item.get('error')}`")
        lines.append("")
    if evidence_pack is not None:
        lines.extend(
            [
                "## Evidence Pack",
                "",
                f"- Evidence items: `{len(evidence_pack.get('evidence_items', []))}`",
                f"- Aggregate items: `{len(evidence_pack.get('aggregate_items', []))}`",
                f"- Evidence path: `{evidence_pack.get('evidence_pack_path', 'n/a')}`",
                "",
            ]
        )
        for item in evidence_pack.get("evidence_items", [])[:10]:
            lines.extend(
                [
                    f"### {item.get('evidence_id')}",
                    "",
                    f"Source: `{item.get('source_path')}`",
                    "",
                    "> " + str(item.get("text", "")).replace("\n", " ")[:500],
                    "",
                ]
            )
    limitations = list(context_pack.get("limitations", []))
    if evidence_pack is not None:
        limitations.extend(evidence_pack.get("limitations", []))
    lines.extend(["## Limitations", ""])
    if limitations:
        for limitation in limitations:
            lines.append(f"- {limitation}")
    else:
        lines.append("- No limitations recorded.")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

