from __future__ import annotations

import hashlib

from src.discovery.models import ArticleCandidate, discovery_config

from .base import ArticleProvider, api_url, clean_html, fetch_json, first, query_text, save_raw


class CrossrefProvider(ArticleProvider):
    name = "crossref"

    def search(self, query: dict, config) -> list[ArticleCandidate]:
        cfg = discovery_config(config)
        params = {
            "query.bibliographic": query_text(query, preferred="query_en"),
            "rows": int(cfg["max_results_per_query"]),
            "filter": f"from-pub-date:{cfg['year_from']},until-pub-date:{cfg['year_to']}",
        }
        payload = fetch_json(api_url("https://api.crossref.org/works", params), config, self.name)
        save_raw(payload, config, self.name, query["id"])
        items = payload.get("message", {}).get("items", [])
        return [self._candidate(item, query["id"]) for item in items if first(item.get("title"))]

    def _candidate(self, item: dict, query_id: str) -> ArticleCandidate:
        doi = item.get("DOI")
        year = _crossref_year(item)
        authors = [
            " ".join(part for part in [author.get("given"), author.get("family")] if part)
            for author in item.get("author", [])
        ]
        links = item.get("link", []) or []
        pdf_url = next((link.get("URL") for link in links if "pdf" in str(link.get("content-type", "")).lower()), None)
        return ArticleCandidate(
            candidate_id=_id("crossref", doi or first(item.get("title"))),
            source="crossref",
            query_id=query_id,
            title=first(item.get("title")) or "",
            authors=[author for author in authors if author],
            year=year,
            journal=first(item.get("container-title")),
            abstract=clean_html(item.get("abstract")),
            doi=doi,
            url=item.get("URL"),
            pdf_url=pdf_url,
            open_access=bool(pdf_url) if pdf_url else None,
            language=item.get("language"),
            metadata={"sources": ["crossref"]},
        )


def _crossref_year(item: dict) -> int | None:
    date_parts = item.get("published-print", item.get("published-online", item.get("created", {}))).get("date-parts")
    if date_parts and date_parts[0]:
        return int(date_parts[0][0])
    return None


def _id(source: str, value: str | None) -> str:
    return f"{source}_{hashlib.sha1(str(value or '').encode('utf-8')).hexdigest()[:12]}"
