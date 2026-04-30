import json

import pandas as pd

from src.toponyms import (
    add_toponyms_column,
    random_samples_per_toponym,
    sentiment_per_toponym,
    toponym_frequency,
    topics_per_toponym,
)


def test_extracts_thailand_toponyms_to_json_list():
    df = pd.DataFrame({"text": ["Bangkok and Phuket visa", "Квартира на Самуи", "No place"]})
    result = add_toponyms_column(df)

    assert json.loads(result.loc[0, "toponyms"]) == ["Bangkok", "Phuket"]
    assert json.loads(result.loc[1, "toponyms"]) == ["Samui"]
    assert json.loads(result.loc[2, "toponyms"]) == []


def test_toponym_aggregates():
    df = pd.DataFrame(
        {
            "doc_id": ["1", "2", "3"],
            "toponyms": ['["Bangkok", "Phuket"]', '["Bangkok"]', '["Samui"]'],
            "topic_id": [0, 1, 0],
            "sentiment": ["neutral", "negative", "positive"],
            "text": ["a", "b", "c"],
        }
    )

    frequency = toponym_frequency(df)
    topics = topics_per_toponym(df)
    sentiment = sentiment_per_toponym(df)
    samples = random_samples_per_toponym(df, samples_per_toponym=1)

    assert frequency.loc[0, "toponym"] == "Bangkok"
    assert frequency.loc[0, "count"] == 2
    assert {"toponym", "topic_id", "count", "share"}.issubset(topics.columns)
    assert {"toponym", "sentiment", "count", "share"}.issubset(sentiment.columns)
    assert set(samples["toponym"]).issubset({"Bangkok", "Phuket", "Samui"})
