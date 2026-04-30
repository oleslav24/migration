from __future__ import annotations

import json
from pathlib import Path


def export_summary_report(summary: dict, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_summary_markdown(summary), encoding="utf-8")


def export_summary_json(summary: dict, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def _summary_markdown(summary: dict) -> str:
    lines = [
        f"# Literature Summary: {summary.get('title', '')}",
        "",
        "## Research question",
        f"RU: {summary.get('question_ru', '')}",
        f"EN: {summary.get('question_en', '')}",
        "",
        "## Executive summary",
        str(summary.get("summary_ru", "")),
        "",
        "## Key findings",
    ]
    lines.extend(_numbered(summary.get("key_findings", [])))
    lines.extend(["", "## Concepts"])
    lines.extend(_bullets(summary.get("concepts", [])))
    lines.extend(["", "## Methods mentioned"])
    lines.extend(_bullets(summary.get("methods", [])))
    lines.extend(["", "## Limitations"])
    lines.extend(_bullets(summary.get("limitations", [])))
    lines.extend(["", "## Relevance for migration/toponym project", str(summary.get("relevance_for_project", ""))])
    lines.extend(["", "## Evidence used"])
    for item in summary.get("evidence_used", []):
        lines.extend(
            [
                f"### {item.get('evidence_id', '')}",
                f"File: {item.get('filename', '')}",
                f"Page: {_display(item.get('page_number'))}",
                f"Chunk: {item.get('chunk_index', '')}",
                f"Score: {float(item.get('score', 0.0)):.4f}",
                "Excerpt:",
                f"> {str(item.get('text', '')).replace(chr(10), ' ')}",
                "",
            ]
        )
    return "\n".join(lines)


def _numbered(items: list[str]) -> list[str]:
    return [f"{index}. {item}" for index, item in enumerate(items, start=1)] or ["1. Нет данных."]


def _bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- Нет данных."]


def _display(value) -> str:
    return "" if value is None else str(value)
