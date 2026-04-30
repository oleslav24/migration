from src.literature.evidence import EvidenceItem
from src.literature.summarizer import extractive_summary


def test_extractive_summary_returns_summary_on_few_fragments():
    task = {
        "id": "digital",
        "title": "Digital traces",
        "question_ru": "Как цифровые следы влияют на миграционные решения?",
        "question_en": "How do digital traces influence migration decisions?",
        "keywords": ["digital traces", "migration decisions", "content analysis"],
    }
    evidence = [
        EvidenceItem(
            evidence_id="E1",
            task_id="digital",
            query="digital traces",
            filename="a.md",
            path="a.md",
            page_number=None,
            chunk_index=0,
            score=0.9,
            text="Digital traces in social media can be used to observe migration decisions.",
        ),
        EvidenceItem(
            evidence_id="E2",
            task_id="digital",
            query="content analysis",
            filename="b.md",
            path="b.md",
            page_number=2,
            chunk_index=1,
            score=0.7,
            text="The paper mentions content analysis and sampling limitations.",
        ),
    ]

    summary = extractive_summary(task, evidence)

    assert summary["task_id"] == "digital"
    assert summary["key_findings"]
    assert "content analysis" in summary["methods"]
    assert summary["evidence_used"][0]["filename"] == "a.md"
