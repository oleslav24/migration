from __future__ import annotations

from .models import ArticleCandidate


def find_pdf_url(candidate: ArticleCandidate, config) -> ArticleCandidate:
    if candidate.pdf_url:
        return candidate
    if candidate.source == "arxiv" and candidate.url:
        candidate.pdf_url = candidate.url.replace("/abs/", "/pdf/")
        candidate.open_access = True
    return candidate
