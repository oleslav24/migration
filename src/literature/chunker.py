from __future__ import annotations

import re

import pandas as pd

from .loader import ArticleDocument


SPACE_RE = re.compile(r"\s+")


def chunk_documents(
    documents: list[ArticleDocument],
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> pd.DataFrame:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    rows: list[dict[str, object]] = []
    for document in documents:
        sources = (
            [(page.page_number, page.text) for page in document.pages]
            if document.pages
            else [(None, document.text)]
        )
        chunk_index = 0
        for page_number, text in sources:
            normalized = _normalize_text(text)
            for char_start, char_end, chunk_text in _iter_chunks(normalized, chunk_size, chunk_overlap):
                if not chunk_text.strip():
                    continue
                rows.append(
                    {
                        "chunk_id": f"{document.doc_id}_{chunk_index:06d}",
                        "doc_id": document.doc_id,
                        "filename": document.filename,
                        "path": document.path,
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "char_start": char_start,
                        "char_end": char_end,
                    }
                )
                chunk_index += 1
    return pd.DataFrame(
        rows,
        columns=[
            "chunk_id",
            "doc_id",
            "filename",
            "path",
            "page_number",
            "chunk_index",
            "text",
            "char_start",
            "char_end",
        ],
    )


def _iter_chunks(text: str, chunk_size: int, chunk_overlap: int):
    if not text:
        return
    step = chunk_size - chunk_overlap
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        yield start, end, text[start:end].strip()
        if end == len(text):
            break
        start += step


def _normalize_text(text: str) -> str:
    return SPACE_RE.sub(" ", str(text or "")).strip()
