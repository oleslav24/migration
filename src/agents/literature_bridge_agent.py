from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.config import PipelineConfig
from src.literature.search import search_literature

from .report_i18n import rt
from .table_utils import output_root_for, read_context_tables, text_column, write_json


DEFAULT_QUESTIONS = [
    {"id": "digital_traces_migration", "query": "digital traces migration social media migration decisions"},
    {"id": "urban_space_toponyms", "query": "urban space representation social media toponyms migrants"},
    {"id": "manual_content_analysis", "query": "content analysis social media migration discourse coding"},
]


def run_literature_bridge_agent(contract_path: str | Path, workspace: str | Path = ".", output_root: str | Path | None = None, config_path: str | Path = "config.yaml", report_language: str = "en") -> dict[str, Any]:
    context_pack, frame = read_context_tables(contract_path, workspace, output_root)
    root = output_root_for(contract_path, workspace, output_root, "data/agent_literature_bridge")
    column = text_column(frame)
    corpus_items = []
    if column is not None and not frame.empty:
        for _, row in frame.head(10).iterrows():
            corpus_items.append({"evidence_id": f"corpus:row:{row.get('row_index')}", "source_path": row.get("source_path"), "row_index": row.get("row_index"), "text": str(row.get(column, ""))[:1000]})
    literature_items, limitations = _search_literature(workspace, config_path)
    bridge = {"context_pack_path": context_pack.get("context_pack_path"), "questions": DEFAULT_QUESTIONS, "corpus_evidence": corpus_items, "literature_evidence": literature_items, "limitations": limitations}
    write_json(root / "literature_corpus_bridge.json", bridge)
    report_path = _report(root, bridge, report_language)
    return {"output_dir": str(root), "report_path": str(report_path), "corpus_evidence": len(corpus_items), "literature_evidence": len(literature_items), "limitations": limitations, "report_language": report_language}


def _search_literature(workspace: str | Path, config_path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    path = Path(workspace) / config_path
    if not path.exists():
        return [], ["Config file was not found; literature index could not be located."]
    config = PipelineConfig.from_yaml(path)
    index_dir = config.literature.get("index_dir", "data/literature_index")
    items: list[dict[str, Any]] = []
    limitations: list[str] = []
    for question in DEFAULT_QUESTIONS:
        try:
            results = search_literature(question["query"], index_dir, top_k=3)
        except FileNotFoundError:
            limitations.append(f"Literature index is missing for query: {question['id']}")
            continue
        for _, row in results.iterrows():
            items.append({"question_id": question["id"], "filename": row.get("filename"), "path": row.get("path"), "page_number": row.get("page_number"), "score": row.get("score"), "text": row.get("text")})
    return items, limitations


def _report(root: Path, bridge: dict[str, Any], report_language: str = "en") -> Path:
    lines = [f"# {rt(report_language, 'literature_bridge')}", "", rt(report_language, "literature_bridge_intro"), "", f"## {rt(report_language, 'matrix')}", ""]
    for question in bridge["questions"]:
        lit_count = sum(1 for item in bridge["literature_evidence"] if item.get("question_id") == question["id"])
        lines.append(f"- `{question['id']}`: corpus evidence `{len(bridge['corpus_evidence'])}`, literature snippets `{lit_count}`")
    lines.extend(["", f"## {rt(report_language, 'corpus_evidence')}", ""])
    for item in bridge["corpus_evidence"][:10]:
        lines.append(f"### {item['evidence_id']}")
        lines.append(f"{rt(report_language, 'source')}: `{item['source_path']}` {rt(report_language, 'row')} `{item['row_index']}`")
        lines.append("")
        lines.append("> " + item["text"].replace("\n", " ")[:500])
        lines.append("")
    lines.extend([f"## {rt(report_language, 'literature_snippets')}", ""])
    for index, item in enumerate(bridge["literature_evidence"][:15], start=1):
        lines.append(f"### L{index}: {item.get('question_id')}")
        lines.append(f"File: `{item.get('filename')}` Page: `{item.get('page_number')}` Score: `{item.get('score')}`")
        lines.append("")
        lines.append("> " + str(item.get("text", "")).replace("\n", " ")[:500])
        lines.append("")
    lines.extend([f"## {rt(report_language, 'gaps_limitations')}", ""])
    for limitation in bridge["limitations"] or [rt(report_language, "bridge_default_limitation")]:
        lines.append(f"- {limitation}")
    path = root / "literature_corpus_bridge.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
