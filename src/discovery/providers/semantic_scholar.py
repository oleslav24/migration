from __future__ import annotations

import hashlib

from src.discovery.models import ArticleCandidate, discovery_config

from .base import ArticleProvider, api_url, fetch_json, query_text, save_raw


class SemanticScholarProvider(ArticleProvider):
    name = "semantic_scholar"

    def search(self, query: dict, config) -> list[ArticleCandidate]:
        cfg = discovery_config(config)
        fields = "title,abstract,authors,year,venue,externalIds,citationCount,openAccessPdf,url"
        payload = fetch_json(
            api_url(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                {"query": query_text(query, preferred="query_en"), "limit": int(cfg["max_results_per_query"]), "fields": fields},
            ),
            config,
            self.name,
        )
        save_raw(payload, config, self.name, query["id"])
        return [self._candidate(item, query["id"]) for item in payload.get("data", []) if item.get("title")]

    def _candidate(self, item: dict, query_id: str) -> ArticleCandidate:
        doi = (item.get("externalIds") or {}).get("DOI")
        pdf_url = (item.get("openAccessPdf") or {}).get("url")
        return ArticleCandidate(
            candidate_id=_id("semantic_scholar", doi or item.get("paperId")),
            source="semantic_scholar",
            query_id=query_id,
            title=item.get("title") or "",
            authors=[author.get("name", "") for author in item.get("authors", []) if author.get("name")],
            year=item.get("year"),
            journal=item.get("venue"),
            abstract=item.get("abstract"),
            doi=doi,
            url=item.get("url"),
            pdf_url=pdf_url,
            open_access=bool(pdf_url),
            citation_count=item.get("citationCount"),
            metadata={"sources": ["semantic_scholar"], "paper_id": item.get("paperId")},
        )


def _id(source: str, value: str | None) -> str:
    return f"{source}_{hashlib.sha1(str(value or '').encode('utf-8')).hexdigest()[:12]}"
