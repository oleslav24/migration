from __future__ import annotations

import math
import re

from .models import ArticleCandidate, discovery_config


def score_candidate(candidate: ArticleCandidate, query: dict, config) -> ArticleCandidate:
    cfg = discovery_config(config)
    relevance = cfg["relevance"]
    title_weight = float(relevance.get("title_weight", 0.45))
    abstract_weight = float(relevance.get("abstract_weight", 0.35))
    keyword_weight = float(relevance.get("keyword_weight", 0.20))

    title_score = _term_score(candidate.title, query)
    abstract_score = _term_score(candidate.abstract or "", query)
    keyword_score = _keyword_score(candidate, query)
    recency = _recency_bonus(candidate.year, cfg["year_from"], cfg["year_to"])
    citation = _citation_bonus(candidate.citation_count)
    oa = 0.05 if candidate.open_access or candidate.pdf_url else 0.0

    score = (title_weight * title_score) + (abstract_weight * abstract_score) + (keyword_weight * keyword_score)
    score = min(1.0, score + recency + citation + oa)
    candidate.relevance_score = round(score, 4)
    candidate.reason = _reason(candidate, query, title_score, abstract_score, keyword_score, recency, citation, oa)
    return candidate


def _term_score(text: str, query: dict) -> float:
    haystack = _normalize(text)
    terms = [*_terms(query.get("required_terms", [])), *_terms(query.get("optional_terms", []))]
    if not terms:
        return 0.0
    hits = sum(1 for term in terms if term in haystack)
    return hits / len(terms)


def _keyword_score(candidate: ArticleCandidate, query: dict) -> float:
    haystack = _normalize(" ".join(candidate.keywords) + " " + candidate.title + " " + str(candidate.abstract or ""))
    required = _terms(query.get("required_terms", []))
    optional = _terms(query.get("optional_terms", []))
    required_hits = [term for term in required if term in haystack]
    optional_hits = [term for term in optional if term in haystack]
    required_score = len(required_hits) / len(required) if required else 1.0
    optional_score = len(optional_hits) / len(optional) if optional else 0.0
    return (0.7 * required_score) + (0.3 * optional_score)


def _recency_bonus(year: int | None, year_from: int, year_to: int) -> float:
    if not year:
        return 0.0
    if year < year_from or year > year_to:
        return -0.1
    span = max(1, year_to - year_from)
    return 0.05 * ((year - year_from) / span)


def _citation_bonus(citation_count: int | None) -> float:
    if not citation_count:
        return 0.0
    return min(0.08, math.log10(citation_count + 1) * 0.03)


def _reason(candidate, query, title_score, abstract_score, keyword_score, recency, citation, oa) -> str:
    matched_required = [term for term in _terms(query.get("required_terms", [])) if term in _normalize(candidate.title + " " + str(candidate.abstract or ""))]
    parts = [
        f"title_score={title_score:.2f}",
        f"abstract_score={abstract_score:.2f}",
        f"keyword_score={keyword_score:.2f}",
    ]
    if matched_required:
        parts.append(f"matched required terms: {', '.join(matched_required)}")
    if oa:
        parts.append("OA/PDF available")
    if candidate.citation_count is not None:
        parts.append(f"cited_by_count={candidate.citation_count}")
    if recency:
        parts.append(f"recency_bonus={recency:.2f}")
    if citation:
        parts.append(f"citation_bonus={citation:.2f}")
    return "; ".join(parts)


def _terms(values) -> list[str]:
    return [_normalize(str(value)) for value in values if str(value).strip()]


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()
