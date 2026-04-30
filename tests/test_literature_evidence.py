import pandas as pd

from src.literature.evidence import collect_evidence


def test_collect_evidence_deduplicates(monkeypatch):
    calls = []

    def fake_search(query, index_dir, top_k):
        calls.append(query)
        return pd.DataFrame(
            [
                {
                    "rank": 1,
                    "score": 0.9,
                    "filename": "a.md",
                    "page_number": None,
                    "chunk_index": 1,
                    "text": "Digital traces and migration decisions.",
                    "path": "a.md",
                },
                {
                    "rank": 2,
                    "score": 0.8,
                    "filename": "a.md",
                    "page_number": None,
                    "chunk_index": 1,
                    "text": "Duplicate location.",
                    "path": "a.md",
                },
            ]
        )

    monkeypatch.setattr("src.literature.evidence.search_literature", fake_search)
    task = {
        "id": "t",
        "question_en": "digital traces migration",
        "question_ru": "цифровые следы миграция",
        "keywords": ["social media"],
    }

    evidence = collect_evidence(task, {"literature": {"index_dir": "missing"}}, top_k=10)

    assert len(calls) == 3
    assert len(evidence) == 1
    assert evidence[0].evidence_id == "E1"
