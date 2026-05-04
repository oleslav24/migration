from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PipelineConfig:
    input_path: str
    input_paths: list[Any] | None = None
    output_dir: str = "data/output"
    interim_dir: str = "data/interim"
    time_window: str = "1h"
    min_text_length: int = 5
    n_topics: int = 10
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_backend: str = "sentence-transformers"
    random_state: int = 42
    chunk_size: int = 100_000
    anonymization_salt: str = "local-dev-salt"
    save_interim_parquet: bool = True
    make_plots: bool = True
    max_rows: int | None = None
    language_detection: dict[str, Any] = field(
        default_factory=lambda: {
            "backend": "rule-based",
            "fallback_backend": "rule-based",
            "target_languages": ["ru", "en", "uz", "th", "other"],
            "fasttext_model_path": None,
        }
    )
    sentiment: dict[str, Any] = field(default_factory=lambda: {"backend": "rule-based"})
    topic_model: dict[str, Any] = field(
        default_factory=lambda: {"backend": "kmeans", "n_topics": 10, "label_top_n": 8}
    )
    experiments: dict[str, Any] = field(
        default_factory=lambda: {"temporal": "month", "group_comparison": True}
    )
    literature: dict[str, Any] = field(
        default_factory=lambda: {
            "articles_dir": "articles",
            "index_dir": "data/literature_index",
            "chunk_size": 1200,
            "chunk_overlap": 200,
            "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "embedding_backend": "sentence-transformers",
            "backend": "sklearn",
            "top_k": 8,
            "summarization": {
                "mode": "extractive",
                "max_evidence_items": 20,
                "max_chars_per_evidence": 1500,
                "language": "ru",
                "llm_provider": "none",
                "llm_model": "none",
            },
        }
    )
    discovery: dict[str, Any] = field(
        default_factory=lambda: {
            "output_dir": "data/discovery",
            "articles_dir": "articles/discovered/pdf",
            "metadata_dir": "articles/discovered/metadata",
            "year_from": 2015,
            "year_to": 2026,
            "max_results_per_query": 50,
            "max_pdf_downloads": 50,
            "languages": ["en", "ru"],
            "providers": {
                "crossref": True,
                "openalex": True,
                "semantic_scholar": True,
                "arxiv": True,
                "manual_seed": True,
            },
            "polite_delay_seconds": 1.0,
            "user_agent": "migration-research-bot/0.1 mailto:YOUR_EMAIL@example.com",
            "relevance": {
                "min_score": 0.45,
                "title_weight": 0.45,
                "abstract_weight": 0.35,
                "keyword_weight": 0.20,
            },
            "download": {
                "only_open_access": True,
                "respect_robots_txt": True,
                "allowed_mime_types": ["application/pdf"],
            },
        }
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PipelineConfig":
        with Path(path).open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        config = cls(**raw)
        if "topic_model" in raw and raw["topic_model"].get("n_topics") is not None:
            config.n_topics = int(raw["topic_model"]["n_topics"])
        return config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def ensure_directories(self) -> None:
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.interim_dir).mkdir(parents=True, exist_ok=True)
