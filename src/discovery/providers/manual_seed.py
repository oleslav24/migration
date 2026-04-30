from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from src.discovery.models import ArticleCandidate

from .base import ArticleProvider


class ManualSeedProvider(ArticleProvider):
    name = "manual_seed"

    def __init__(self, seed_path: str = "queries/seed_sources.yaml") -> None:
        self.seed_path = seed_path

    def search(self, query: dict, config) -> list[ArticleCandidate]:
        path = Path(self.seed_path)
        if not path.exists():
            return []
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        candidates: list[ArticleCandidate] = []
        for item in payload.get("sources", []):
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            candidates.append(
                ArticleCandidate(
                    candidate_id=_id("manual_seed", item.get("doi") or title),
                    source="manual_seed",
                    query_id=query.get("id", "manual_seed"),
                    title=title,
                    authors=item.get("authors", []) or [],
                    year=item.get("year"),
                    journal=item.get("journal"),
                    abstract=item.get("abstract"),
                    doi=item.get("doi") or None,
                    url=item.get("url") or None,
                    pdf_url=item.get("pdf_url") or None,
                    open_access=bool(item.get("pdf_url")) if item.get("open_access") is None else bool(item.get("open_access")),
                    keywords=item.get("keywords", []) or [],
                    metadata={"sources": ["manual_seed"], "note": item.get("note")},
                )
            )
        return candidates


def _id(source: str, value: str | None) -> str:
    return f"{source}_{hashlib.sha1(str(value or '').encode('utf-8')).hexdigest()[:12]}"
