import pandas as pd

from src.coding.sampling import _sample_by_strategy


def test_sample_by_toponym_filters_rows():
    frame = pd.DataFrame(
        {
            "doc_id": ["a", "b", "c"],
            "group": ["g1", "g1", "g2"],
            "period": ["2025-01", "2025-01", "2025-02"],
            "window_start": ["2025-01-01", "2025-01-02", "2025-02-01"],
            "text": ["one", "two", "three"],
            "toponyms": ["Patong;Phuket", "Bangkok", "Patong"],
            "topic_id": [0, 1, 2],
            "sentiment": ["neutral", "positive", "negative"],
        }
    )

    sample = _sample_by_strategy(
        frame=frame,
        n=10,
        strategy="by_toponym",
        seed=42,
        filters={"toponym": "Patong"},
    )
    assert len(sample) == 2
    assert sample["toponyms"].astype(str).str.contains("Patong").all()
