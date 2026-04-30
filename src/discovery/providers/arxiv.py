from __future__ import annotations

import hashlib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from src.discovery.models import ArticleCandidate, discovery_config

from .base import ArticleProvider, query_text, save_raw


ATOM = {"a": "http://www.w3.org/2005/Atom"}


class ArxivProvider(ArticleProvider):
    name = "arxiv"

    def search(self, query: dict, config) -> list[ArticleCandidate]:
        cfg = discovery_config(config)
        url = (
            "https://export.arxiv.org/api/query?"
            + urllib.parse.urlencode(
                {
                    "search_query": f"all:{query_text(query, preferred='query_en')}",
                    "start": 0,
                    "max_results": int(cfg["max_results_per_query"]),
                }
            )
        )
        request = urllib.request.Request(url, headers={"User-Agent": cfg["user_agent"]})
        with urllib.request.urlopen(request, timeout=30) as response:
            xml_text = response.read().decode("utf-8")
        save_raw({"xml": xml_text}, config, self.name, query["id"])
        root = ET.fromstring(xml_text)
        return [self._candidate(entry, query["id"]) for entry in root.findall("a:entry", ATOM)]

    def _candidate(self, entry, query_id: str) -> ArticleCandidate:
        arxiv_id = entry.findtext("a:id", default="", namespaces=ATOM)
        title = " ".join(entry.findtext("a:title", default="", namespaces=ATOM).split())
        abstract = " ".join(entry.findtext("a:summary", default="", namespaces=ATOM).split())
        year_text = entry.findtext("a:published", default="", namespaces=ATOM)[:4]
        pdf_url = next(
            (
                link.attrib.get("href")
                for link in entry.findall("a:link", ATOM)
                if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf"
            ),
            arxiv_id.replace("/abs/", "/pdf/") if "/abs/" in arxiv_id else None,
        )
        return ArticleCandidate(
            candidate_id=_id("arxiv", arxiv_id),
            source="arxiv",
            query_id=query_id,
            title=title,
            authors=[author.findtext("a:name", default="", namespaces=ATOM) for author in entry.findall("a:author", ATOM)],
            year=int(year_text) if year_text.isdigit() else None,
            abstract=abstract,
            url=arxiv_id,
            pdf_url=pdf_url,
            open_access=True,
            metadata={"sources": ["arxiv"], "arxiv_id": arxiv_id},
        )


def _id(source: str, value: str | None) -> str:
    return f"{source}_{hashlib.sha1(str(value or '').encode('utf-8')).hexdigest()[:12]}"
