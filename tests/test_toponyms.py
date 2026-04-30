import pandas as pd

from src.toponyms import (
    TOPONYM_META,
    add_toponyms_column,
    city_level_stats,
    district_level_stats,
    extract_toponyms,
    random_samples_per_toponym,
    sentiment_per_toponym,
    toponym_frequency,
    topics_per_toponym,
)


def test_extracts_thailand_toponyms_to_list():
    df = pd.DataFrame(
        {"text": ["  Bangkok   and PHUKET visa  ", "Квартира на Самуи", "No place"]}
    )
    result = add_toponyms_column(df)

    assert result.loc[0, "toponyms"] == ["Bangkok", "Phuket"]
    assert result.loc[1, "toponyms"] == ["Samui"]
    assert result.loc[2, "toponyms"] == []


def test_detects_districts_and_removes_dangerous_aliases():
    assert extract_toponyms("condo in Thong Lo and Patong") == ["Thong Lo", "Patong"]
    assert "Koh Tao" not in extract_toponyms("tao means way")
    assert "Koh Chang" not in extract_toponyms("chang is a common word")
    assert "Koh Lanta" not in extract_toponyms("lanta without island prefix")


def test_toponym_meta_has_type_and_parent_city():
    assert TOPONYM_META["Thong Lo"] == {"type": "district", "parent_city": "Bangkok"}
    assert TOPONYM_META["Phuket"] == {"type": "city", "parent_city": "Phuket"}


def test_toponym_aggregates():
    df = pd.DataFrame(
        {
            "doc_id": ["1", "2", "3"],
            "toponyms": [["Bangkok", "Phuket", "Thong Lo"], ["Bangkok"], ["Samui"]],
            "topic_id": [0, 1, 0],
            "sentiment": ["neutral", "negative", "positive"],
            "text": ["a", "b", "c"],
        }
    )

    frequency = toponym_frequency(df)
    topics = topics_per_toponym(df)
    sentiment = sentiment_per_toponym(df)
    cities = city_level_stats(df)
    districts = district_level_stats(df)
    samples = random_samples_per_toponym(df, samples_per_toponym=1)

    assert frequency.loc[0, "toponym"] == "Bangkok"
    assert frequency.loc[0, "count"] == 2
    assert {"toponym", "type", "parent_city", "topic_id", "count", "share"}.issubset(topics.columns)
    assert {"toponym", "type", "parent_city", "sentiment", "count", "share"}.issubset(sentiment.columns)
    assert "Bangkok" in set(cities["parent_city"])
    assert districts.loc[0, "toponym"] == "Thong Lo"
    assert set(samples["toponym"]).issubset({"Bangkok", "Phuket", "Thong Lo", "Samui"})
