from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from .index import _literature_config
from .search import search_literature


@dataclass
class EvidenceItem:
    evidence_id: str
    task_id: str
    query: str
    filename: str
    path: str
    page_number: int | None
    chunk_index: int
    score: float
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def collect_evidence(
    task: dict,
    config,
    top_k: int = 12,
) -> list[EvidenceItem]:
    literature = _literature_config(config)
    queries = _task_queries(task)
    collected: list[EvidenceItem] = []
    seen: set[tuple[str, int | None, int]] = set()

    for query in queries:
        try:
            results = search_literature(query, literature["index_dir"], top_k)
        except FileNotFoundError:
            results = pd.DataFrame()
        for _, row in results.iterrows():
            page_number = _optional_int(row.get("page_number"))
            chunk_index = int(row.get("chunk_index", 0))
            key = (str(row.get("filename", "")), page_number, chunk_index)
            if key in seen:
                continue
            seen.add(key)
            collected.append(
                EvidenceItem(
                    evidence_id=f"E{len(collected) + 1}",
                    task_id=str(task.get("id", "manual_task")),
                    query=query,
                    filename=str(row.get("filename", "")),
                    path=str(row.get("path", "")),
                    page_number=page_number,
                    chunk_index=chunk_index,
                    score=float(row.get("score", 0.0)),
                    text=str(row.get("text", "")),
                )
            )

    collected.sort(key=lambda item: item.score, reverse=True)
    return _renumber(collected[:top_k])


def filter_evidence(
    evidence: list[EvidenceItem],
    min_score: float | None = None,
    max_items: int = 20,
) -> list[EvidenceItem]:
    result = [item for item in evidence if min_score is None or item.score >= min_score]
    result = sorted(result, key=lambda item: item.score, reverse=True)[:max_items]
    return _renumber(result)


def _task_queries(task: dict) -> list[str]:
    queries: list[str] = []
    for key in ("question_en", "question_ru"):
        value = str(task.get(key, "") or "").strip()
        if value:
            queries.append(value)
    keywords = [str(value).strip() for value in task.get("keywords", []) if str(value).strip()]
    if keywords:
        queries.append(" ".join(keywords))
    return queries or [str(task.get("title", task.get("id", "")))]


def _optional_int(value) -> int | None:
    if pd.isna(value):
        return None
    return int(value)


def _renumber(evidence: list[EvidenceItem]) -> list[EvidenceItem]:
    for index, item in enumerate(evidence, start=1):
        item.evidence_id = f"E{index}"
    return evidence
