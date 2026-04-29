from __future__ import annotations

import hashlib

import numpy as np


def build_embeddings(
    docs,
    model_name: str,
    backend: str = "sentence-transformers",
    random_state: int = 42,
) -> np.ndarray:
    texts = ["" if text is None else str(text) for text in docs]
    if backend == "hash":
        return build_hash_embeddings(texts, dimensions=384)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is required for embedding_backend='sentence-transformers'. "
            "Install requirements or set embedding_backend: hash for smoke tests."
        ) from exc

    model = SentenceTransformer(model_name)
    return model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)


def build_hash_embeddings(texts: list[str], dimensions: int = 384) -> np.ndarray:
    vectors = np.zeros((len(texts), dimensions), dtype=np.float32)
    for row, text in enumerate(texts):
        tokens = text.lower().split()
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vectors[row, index] += sign
        norm = np.linalg.norm(vectors[row])
        if norm > 0:
            vectors[row] /= norm
    return vectors

