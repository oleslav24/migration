from src.literature.chunker import chunk_documents
from src.literature.loader import ArticleDocument


def test_chunking_with_overlap():
    document = ArticleDocument(
        doc_id="doc",
        path="article.txt",
        filename="article.txt",
        extension=".txt",
        text="abcdefghijklmnopqrstuvwxyz",
    )

    chunks = chunk_documents([document], chunk_size=10, chunk_overlap=3)

    assert chunks["text"].tolist()[:3] == ["abcdefghij", "hijklmnopq", "opqrstuvwx"]
    assert chunks.loc[1, "char_start"] == 7
