from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from src.embeddings import build_embeddings

from .chunker import chunk_documents
from .loader import load_articles


def build_literature_index(config) -> None:
    literature = _literature_config(config)
    articles_dir = literature["articles_dir"]
    index_dir = Path(literature["index_dir"])
    index_dir.mkdir(parents=True, exist_ok=True)

    documents = load_articles(articles_dir)
    chunks = chunk_documents(
        documents,
        chunk_size=int(literature["chunk_size"]),
        chunk_overlap=int(literature["chunk_overlap"]),
    )
    if chunks.empty:
        raise RuntimeError(f"No literature chunks built from {articles_dir}")

    embeddings = build_embeddings(
        chunks["text"].tolist(),
        model_name=str(literature["embedding_model"]),
        backend=str(literature.get("embedding_backend", "sentence-transformers")),
    )
    np.save(index_dir / "embeddings.npy", embeddings)
    chunks_storage = _write_chunks(chunks, index_dir / "chunks.parquet")

    metadata = {
        "articles_dir": str(articles_dir),
        "index_dir": str(index_dir),
        "document_count": len(documents),
        "chunk_count": int(len(chunks)),
        "chunk_size": int(literature["chunk_size"]),
        "chunk_overlap": int(literature["chunk_overlap"]),
        "embedding_model": str(literature["embedding_model"]),
        "embedding_backend": str(literature.get("embedding_backend", "sentence-transformers")),
        "backend": str(literature.get("backend", "sklearn")),
        "chunks_storage": chunks_storage,
    }
    _write_json(index_dir / "metadata.json", metadata)
    _build_search_index(embeddings, index_dir, metadata["backend"])


def _build_search_index(embeddings: np.ndarray, index_dir: Path, backend: str) -> None:
    if backend != "sklearn":
        _write_json(index_dir / "index.json", {"backend": "brute_force"})
        return
    try:
        from sklearn.neighbors import NearestNeighbors
    except ImportError:
        _write_json(index_dir / "index.json", {"backend": "brute_force", "reason": "missing_sklearn"})
        return
    model = NearestNeighbors(metric="cosine", algorithm="brute")
    model.fit(embeddings)
    with (index_dir / "index.pkl").open("wb") as handle:
        pickle.dump(model, handle)
    _write_json(index_dir / "index.json", {"backend": "sklearn", "metric": "cosine"})


def _write_chunks(chunks, path: Path) -> str:
    try:
        chunks.to_parquet(path, index=False)
        return "parquet"
    except ImportError:
        chunks.to_pickle(path)
        return "pickle_fallback"


def _literature_config(config) -> dict[str, Any]:
    if isinstance(config, dict):
        raw = config.get("literature", config)
        base_embedding_model = config.get(
            "embedding_model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    else:
        raw = getattr(config, "literature", {})
        base_embedding_model = getattr(
            config, "embedding_model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    return {
        "articles_dir": raw.get("articles_dir", "articles"),
        "index_dir": raw.get("index_dir", "data/literature_index"),
        "chunk_size": raw.get("chunk_size", 1200),
        "chunk_overlap": raw.get("chunk_overlap", 200),
        "embedding_model": raw.get("embedding_model", base_embedding_model),
        "embedding_backend": raw.get("embedding_backend", raw.get("embedding_model_backend", "sentence-transformers")),
        "backend": raw.get("backend", "sklearn"),
        "top_k": raw.get("top_k", 8),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
