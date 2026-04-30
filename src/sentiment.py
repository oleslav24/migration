from __future__ import annotations

from typing import Any, Literal


Sentiment = Literal["positive", "negative", "neutral"]

POSITIVE_WORDS = {
    "good",
    "great",
    "thanks",
    "thank",
    "ok",
    "yes",
    "хорошо",
    "спасибо",
    "супер",
    "отлично",
    "да",
    "норм",
}
NEGATIVE_WORDS = {
    "bad",
    "problem",
    "no",
    "not",
    "нет",
    "плохо",
    "проблема",
    "сложно",
    "дорого",
    "отказ",
    "штраф",
}


def classify_sentiment(text: str) -> Sentiment:
    tokens = {token.strip(".,!?;:()[]{}\"'").lower() for token in str(text).split()}
    positive = len(tokens & POSITIVE_WORDS)
    negative = len(tokens & NEGATIVE_WORDS)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def add_sentiment_column(df, config: dict[str, Any] | None = None):
    result = df.copy()
    result["sentiment"] = result["text"].map(classify_sentiment)
    return result
