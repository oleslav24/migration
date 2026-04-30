from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.embeddings import build_embeddings


def search_literature(
    query: str,
    index_dir: str,
    top_k: int = 8,
) -> pd.DataFrame:
    root = Path(index_dir)
    chunks_path = root / "chunks.parquet"
    embeddings_path = root / "embeddings.npy"
    metadata_path = root / "metadata.json"
    if not chunks_path.exists() or not embeddings_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(f"Literature index is incomplete: {root}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    chunks = _read_chunks(chunks_path, metadata)
    embeddings = np.load(embeddings_path)
    query_embedding = build_embeddings(
        [query],
        model_name=metadata["embedding_model"],
        backend=metadata.get("embedding_backend", "sentence-transformers"),
    )

    distances, indices = _nearest(root, embeddings, query_embedding, max(top_k * 3, top_k))
    rows: list[dict[str, object]] = []
    seen_locations: set[tuple[str, object, object]] = set()
    for distance, index in zip(distances, indices):
        chunk = chunks.iloc[int(index)]
        location = (str(chunk["path"]), chunk.get("page_number"), chunk.get("chunk_index"))
        if location in seen_locations:
            continue
        seen_locations.add(location)
        rows.append(
            {
                "rank": len(rows) + 1,
                "score": float(1.0 - distance),
                "filename": chunk["filename"],
                "page_number": chunk.get("page_number"),
                "chunk_index": int(chunk["chunk_index"]),
                "text": chunk["text"],
                "path": chunk["path"],
            }
        )
        if len(rows) >= top_k:
            break
    return pd.DataFrame(rows, columns=["rank", "score", "filename", "page_number", "chunk_index", "text", "path"])


def _read_chunks(path: Path, metadata: dict) -> pd.DataFrame:
    if metadata.get("chunks_storage") == "pickle_fallback":
        return pd.read_pickle(path)
    try:
        return pd.read_parquet(path)
    except ImportError:
        return pd.read_pickle(path)


def _nearest(index_dir: Path, embeddings: np.ndarray, query_embedding: np.ndarray, limit: int):
    index_path = index_dir / "index.pkl"
    if index_path.exists():
        with index_path.open("rb") as handle:
            model = pickle.load(handle)
        distances, indices = model.kneighbors(query_embedding, n_neighbors=min(limit, len(embeddings)))
        return distances[0], indices[0]

    query = query_embedding[0]
    scores = embeddings @ query
    distances = 1.0 - scores
    order = np.argsort(distances)[:limit]
    return distances[order], order
