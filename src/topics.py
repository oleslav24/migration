from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd


def assign_topics(
    embeddings: np.ndarray,
    docs: pd.DataFrame,
    n_topics: int,
    random_state: int,
) -> pd.DataFrame:
    result = docs.copy()
    if len(result) == 0:
        result["topic_id"] = pd.Series(dtype="Int64")
        return result

    n_clusters = max(1, min(n_topics, len(result)))
    from sklearn.cluster import KMeans

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    result["topic_id"] = model.fit_predict(embeddings).astype(int)
    return result


def generate_topic_labels(docs: pd.DataFrame, top_n: int = 8) -> dict[str, list[str]]:
    if docs.empty or "topic_id" not in docs:
        return {}

    try:
        return _tfidf_topic_labels(docs, top_n)
    except Exception:
        return _counter_topic_labels(docs, top_n)


def _tfidf_topic_labels(docs: pd.DataFrame, top_n: int) -> dict[str, list[str]]:
    from sklearn.feature_extraction.text import TfidfVectorizer

    labels: dict[str, list[str]] = {}
    token_pattern = r"(?u)\b[\wА-Яа-яЁё]{3,}\b"
    for topic_id, frame in docs.groupby("topic_id"):
        vectorizer = TfidfVectorizer(max_features=2000, token_pattern=token_pattern)
        matrix = vectorizer.fit_transform(frame["text"].astype(str))
        scores = np.asarray(matrix.mean(axis=0)).ravel()
        terms = np.asarray(vectorizer.get_feature_names_out())
        top_terms = terms[np.argsort(scores)[-top_n:][::-1]].tolist()
        labels[str(topic_id)] = top_terms
    return labels


def _counter_topic_labels(docs: pd.DataFrame, top_n: int) -> dict[str, list[str]]:
    labels: dict[str, list[str]] = {}
    for topic_id, frame in docs.groupby("topic_id"):
        counter: Counter[str] = Counter()
        for text in frame["text"].astype(str):
            counter.update(token for token in text.lower().split() if len(token) >= 3)
        labels[str(topic_id)] = [token for token, _ in counter.most_common(top_n)]
    return labels

