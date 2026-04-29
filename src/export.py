from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def export_results(
    enriched_docs: pd.DataFrame,
    analysis_results: dict[str, pd.DataFrame],
    metrics: dict[str, Any],
    topic_labels: dict[str, list[str]],
    config,
) -> None:
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _export_frame(enriched_docs, output_dir / "documents_enriched.csv")
    for name, frame in analysis_results.items():
        _export_frame(frame, output_dir / f"{name}.csv")

    _write_json(output_dir / "metrics.json", metrics)
    _write_json(output_dir / "topic_labels.json", topic_labels)
    _write_json(output_dir / "config_resolved.json", config.to_dict())

    if config.make_plots:
        export_plots(analysis_results, output_dir)


def _export_frame(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_plots(analysis_results: dict[str, pd.DataFrame], output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    distribution = analysis_results.get("topic_distribution")
    if distribution is not None and not distribution.empty:
        ax = distribution.plot.bar(x="topic_id", y="count", legend=False)
        ax.set_xlabel("Topic")
        ax.set_ylabel("Documents")
        ax.figure.tight_layout()
        ax.figure.savefig(output_dir / "topic_distribution.png", dpi=150)
        plt.close(ax.figure)

    temporal = analysis_results.get("temporal_dynamics")
    if temporal is not None and not temporal.empty:
        pivot = temporal.pivot(index="period", columns="topic_id", values="share").fillna(0)
        ax = pivot.plot(figsize=(10, 5))
        ax.set_xlabel("Period")
        ax.set_ylabel("Share")
        ax.figure.tight_layout()
        ax.figure.savefig(output_dir / "temporal_dynamics.png", dpi=150)
        plt.close(ax.figure)

    groups = analysis_results.get("group_comparison")
    if groups is not None and not groups.empty:
        pivot = groups.pivot(index="group", columns="topic_id", values="share").fillna(0)
        ax = pivot.plot.bar(stacked=True, figsize=(10, 5))
        ax.set_xlabel("Group")
        ax.set_ylabel("Share")
        ax.figure.tight_layout()
        ax.figure.savefig(output_dir / "group_comparison.png", dpi=150)
        plt.close(ax.figure)

