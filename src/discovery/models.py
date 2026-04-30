from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ArticleCandidate:
    candidate_id: str
    source: str
    query_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    journal: str | None = None
    abstract: str | None = None
    doi: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    open_access: bool | None = None
    citation_count: int | None = None
    language: str | None = None
    keywords: list[str] = field(default_factory=list)
    relevance_score: float | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DownloadResult:
    candidate_id: str
    downloaded: bool
    path: str | None = None
    metadata_path: str | None = None
    reason: str | None = None


def discovery_config(config) -> dict[str, Any]:
    raw = config.get("discovery", config) if isinstance(config, dict) else getattr(config, "discovery", {})
    return {
        "output_dir": raw.get("output_dir", "data/discovery"),
        "articles_dir": raw.get("articles_dir", "articles/discovered/pdf"),
        "metadata_dir": raw.get("metadata_dir", "articles/discovered/metadata"),
        "year_from": raw.get("year_from", 2015),
        "year_to": raw.get("year_to", 2026),
        "max_results_per_query": raw.get("max_results_per_query", 50),
        "max_pdf_downloads": raw.get("max_pdf_downloads", 50),
        "languages": raw.get("languages", ["en", "ru"]),
        "providers": raw.get("providers", {}),
        "polite_delay_seconds": raw.get("polite_delay_seconds", 1.0),
        "user_agent": raw.get("user_agent", "migration-research-bot/0.1"),
        "relevance": raw.get("relevance", {}),
        "download": raw.get("download", {}),
    }


def ensure_discovery_dirs(config) -> None:
    cfg = discovery_config(config)
    for key in ("output_dir", "articles_dir", "metadata_dir"):
        Path(cfg[key]).mkdir(parents=True, exist_ok=True)
    Path(cfg["output_dir"], "raw").mkdir(parents=True, exist_ok=True)
