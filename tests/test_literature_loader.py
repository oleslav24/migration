from pathlib import Path
from uuid import uuid4

from src.literature.loader import load_articles


def test_load_articles_reads_txt_and_md():
    work_dir = Path("tmp_write_check") / uuid4().hex / "articles"
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "a.txt").write_text("migration digital traces", encoding="utf-8")
    (work_dir / "b.md").write_text("# Urban space\n\nToponyms and districts", encoding="utf-8")
    (work_dir / "empty.txt").write_text("", encoding="utf-8")

    documents = load_articles(str(work_dir))

    assert len(documents) == 2
    assert {document.extension for document in documents} == {".txt", ".md"}
    assert all(document.filename for document in documents)
