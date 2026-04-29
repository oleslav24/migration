from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_metrics(
    enriched_docs: pd.DataFrame,
    embeddings: np.ndarray,
    config,
    source_message_count: int,
) -> dict[str, Any]:
    total_docs = int(len(enriched_docs))
    docs_with_topics = int(enriched_docs["topic_id"].notna().sum()) if total_docs else 0
    messages_with_topics = int(enriched_docs.loc[enriched_docs["topic_id"].notna(), "message_count"].sum())
    topic_counts = (
        enriched_docs["topic_id"].value_counts().sort_index().astype(int).to_dict()
        if total_docs
        else {}
    )
    return {
        "source_message_count": int(source_message_count),
        "document_count": total_docs,
        "coverage": {
            "documents": docs_with_topics / total_docs if total_docs else 0.0,
            "messages": messages_with_topics / source_message_count if source_message_count else 0.0,
        },
        "topic_distribution": {str(key): value for key, value in topic_counts.items()},
        "topic_stability": topic_stability(
            embeddings=embeddings,
            labels=enriched_docs["topic_id"].to_numpy() if total_docs else np.array([]),
            n_topics=config.n_topics,
            random_state=config.random_state,
        ),
    }


def topic_stability(
    embeddings: np.ndarray,
    labels: np.ndarray,
    n_topics: int,
    random_state: int,
) -> dict[str, float | str]:
    if len(labels) < 2:
        return {"method": "adjusted_rand_score", "score": 1.0}

    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score

    n_clusters = max(1, min(n_topics, len(labels)))
    rerun = KMeans(n_clusters=n_clusters, random_state=random_state + 1, n_init="auto")
    second_labels = rerun.fit_predict(embeddings)
    return {
        "method": "adjusted_rand_score",
        "score": float(adjusted_rand_score(labels, second_labels)),
    }

