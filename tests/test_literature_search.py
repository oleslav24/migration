from pathlib import Path
from uuid import uuid4

from src.literature.index import build_literature_index
from src.literature.search import search_literature


def test_search_returns_relevant_chunk():
    work_dir = Path("tmp_write_check") / uuid4().hex
    articles_dir = work_dir / "articles"
    index_dir = work_dir / "index"
    articles_dir.mkdir(parents=True, exist_ok=True)
    (articles_dir / "migration.md").write_text(
        "Digital traces from social media help study migration decisions.",
        encoding="utf-8",
    )
    (articles_dir / "cooking.txt").write_text("Cooking recipes and kitchen notes.", encoding="utf-8")

    config = {
        "literature": {
            "articles_dir": str(articles_dir),
            "index_dir": str(index_dir),
            "chunk_size": 200,
            "chunk_overlap": 20,
            "embedding_model": "hash",
            "embedding_backend": "hash",
            "backend": "brute_force",
            "top_k": 2,
        }
    }

    build_literature_index(config)
    results = search_literature("migration social media digital traces", str(index_dir), top_k=1)

    assert len(results) == 1
    assert results.loc[0, "filename"] == "migration.md"
    assert "migration decisions" in results.loc[0, "text"]
