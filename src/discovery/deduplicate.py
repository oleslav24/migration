from __future__ import annotations

import re

from .models import ArticleCandidate


def deduplicate_candidates(candidates: list[ArticleCandidate]) -> list[ArticleCandidate]:
    merged: dict[str, ArticleCandidate] = {}
    for candidate in candidates:
        key = _dedupe_key(candidate)
        if key not in merged:
            merged[key] = candidate
            merged[key].metadata.setdefault("sources", [candidate.source])
            continue
        merged[key] = _merge(merged[key], candidate)
    return list(merged.values())


def _dedupe_key(candidate: ArticleCandidate) -> str:
    if candidate.doi:
        return f"doi:{candidate.doi.lower().strip()}"
    return f"title:{normalize_title(candidate.title)}"


def normalize_title(title: str) -> str:
    return re.sub(r"\W+", " ", title.lower()).strip()


def _merge(base: ArticleCandidate, other: ArticleCandidate) -> ArticleCandidate:
    for field in (
        "year",
        "journal",
        "abstract",
        "doi",
        "url",
        "pdf_url",
        "open_access",
        "citation_count",
        "language",
        "relevance_score",
        "reason",
    ):
        if getattr(base, field) in (None, "", []):
            setattr(base, field, getattr(other, field))
    base.authors = base.authors or other.authors
    base.keywords = sorted(set(base.keywords) | set(other.keywords))
    sources = set(base.metadata.get("sources", [])) | set(other.metadata.get("sources", [])) | {base.source, other.source}
    base.metadata.update(other.metadata)
    base.metadata["sources"] = sorted(sources)
    return base
