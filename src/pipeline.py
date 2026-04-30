from __future__ import annotations

from pathlib import Path

import pandas as pd

from .aggregation import aggregate_messages
from .analysis import compute_analysis
from .config import PipelineConfig
from .data_loader import load_csv
from .embeddings import build_embeddings
from .export import export_results
from .language import add_language_column
from .migration_drivers import add_migration_driver_column
from .metrics import compute_metrics
from .preprocess import preprocess_chunk
from .sentiment import add_sentiment_column
from .toponyms import add_toponyms_column
from .topics import assign_topics, generate_topic_labels


def run_pipeline(config: PipelineConfig) -> dict[str, object]:
    config.ensure_directories()
    print(f"Input: {config.input_path}")

    clean_chunks: list[pd.DataFrame] = []
    source_rows = 0
    for index, chunk in enumerate(load_csv(config), start=1):
        source_rows += len(chunk)
        clean = preprocess_chunk(
            chunk,
            min_text_length=config.min_text_length,
            anonymization_salt=config.anonymization_salt,
        )
        clean = add_language_column(clean, config.language_detection)
        clean_chunks.append(clean)
        print(f"Chunk {index}: loaded={len(chunk)} clean={len(clean)}")

    messages = pd.concat(clean_chunks, ignore_index=True) if clean_chunks else pd.DataFrame()
    print(f"Rows loaded: {source_rows}")
    print(f"Rows after cleaning: {len(messages)}")

    if config.save_interim_parquet and not messages.empty:
        interim_path = Path(config.interim_dir) / "clean_messages.parquet"
        messages.to_parquet(interim_path, index=False)
        print(f"Interim parquet: {interim_path}")

    docs = aggregate_messages(messages, config.time_window)
    print(f"Aggregated documents: {len(docs)}")

    embeddings = build_embeddings(
        docs["text"].tolist(),
        model_name=config.embedding_model,
        backend=config.embedding_backend,
        random_state=config.random_state,
    )
    enriched_docs = assign_topics(embeddings, docs, config.n_topics, config.random_state)
    enriched_docs = add_sentiment_column(enriched_docs, config.sentiment)
    enriched_docs = add_migration_driver_column(enriched_docs)
    enriched_docs = add_toponyms_column(enriched_docs)
    topic_labels = generate_topic_labels(enriched_docs, top_n=int(config.topic_model.get("label_top_n", 8)))
    analysis_results = compute_analysis(enriched_docs)
    metrics = compute_metrics(enriched_docs, embeddings, config, source_message_count=len(messages))
    export_results(enriched_docs, analysis_results, metrics, topic_labels, config)

    print(f"Coverage documents: {metrics['coverage']['documents']:.3f}")
    print(f"Coverage messages: {metrics['coverage']['messages']:.3f}")
    print(f"Output: {config.output_dir}")
    return {
        "messages": messages,
        "documents": enriched_docs,
        "analysis": analysis_results,
        "metrics": metrics,
        "topic_labels": topic_labels,
    }
