from __future__ import annotations

import hashlib

from src.discovery.models import ArticleCandidate, discovery_config

from .base import ArticleProvider, api_url, fetch_json, query_text, save_raw


class OpenAlexProvider(ArticleProvider):
    name = "openalex"

    def search(self, query: dict, config) -> list[ArticleCandidate]:
        cfg = discovery_config(config)
        params = {
            "search": query_text(query),
            "per-page": int(cfg["max_results_per_query"]),
            "filter": f"from_publication_date:{cfg['year_from']}-01-01,to_publication_date:{cfg['year_to']}-12-31",
        }
        payload = fetch_json(api_url("https://api.openalex.org/works", params), config, self.name)
        save_raw(payload, config, self.name, query["id"])
        return [self._candidate(item, query["id"]) for item in payload.get("results", []) if item.get("title")]

    def _candidate(self, item: dict, query_id: str) -> ArticleCandidate:
        oa = item.get("open_access") or {}
        authors = [
            authorship.get("author", {}).get("display_name", "")
            for authorship in item.get("authorships", [])
            if authorship.get("author", {}).get("display_name")
        ]
        source = item.get("primary_location", {}).get("source") or {}
        doi = _strip_doi(item.get("doi"))
        return ArticleCandidate(
            candidate_id=_id("openalex", doi or item.get("id")),
            source="openalex",
            query_id=query_id,
            title=item.get("title") or "",
            authors=authors,
            year=item.get("publication_year"),
            journal=source.get("display_name"),
            abstract=_openalex_abstract(item.get("abstract_inverted_index")),
            doi=doi,
            url=item.get("id"),
            pdf_url=oa.get("oa_url"),
            open_access=oa.get("is_oa"),
            citation_count=item.get("cited_by_count"),
            language=item.get("language"),
            metadata={"sources": ["openalex"], "openalex_id": item.get("id")},
        )


def _openalex_abstract(inverted: dict | None) -> str | None:
    if not inverted:
        return None
    positions: list[tuple[int, str]] = []
    for word, offsets in inverted.items():
        positions.extend((int(offset), word) for offset in offsets)
    return " ".join(word for _offset, word in sorted(positions))


def _strip_doi(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace("https://doi.org/", "").lower()


def _id(source: str, value: str | None) -> str:
    return f"{source}_{hashlib.sha1(str(value or '').encode('utf-8')).hexdigest()[:12]}"
