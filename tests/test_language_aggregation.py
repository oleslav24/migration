import pandas as pd

from src.aggregation import aggregate_messages
from src.language import detect_language


def test_detect_language_simple_cases():
    assert detect_language("Привет мир") == "ru"
    assert detect_language("hello world") == "en"
    assert detect_language("😀😀") == "other"


def test_aggregate_messages_by_group_and_hour():
    df = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2020-10-13 08:01:00+00:00",
                    "2020-10-13 08:30:00+00:00",
                    "2020-10-13 09:01:00+00:00",
                ]
            ),
            "group": ["A", "A", "A"],
            "clean_text": ["first", "second", "third"],
            "lang": ["en", "en", "en"],
            "period": ["2020-10", "2020-10", "2020-10"],
        }
    )
    docs = aggregate_messages(df, "1h")
    assert len(docs) == 2
    assert docs.loc[0, "message_count"] == 2
    assert "first\nsecond" == docs.loc[0, "text"]

