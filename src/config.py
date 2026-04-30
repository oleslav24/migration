from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PipelineConfig:
    input_path: str
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
