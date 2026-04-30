from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    output_dir = ROOT / "data" / "output"
    labels_path = output_dir / "topic_labels.json"
    documents_path = output_dir / "documents_enriched.csv"
    if not labels_path.exists() or not documents_path.exists():
        print("Baseline outputs not found. Run: python examples/01_run_baseline.py")
        return
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    documents = pd.read_csv(documents_path)

    for topic_id, terms in sorted(labels.items(), key=lambda item: int(item[0])):
        topic_docs = documents[documents["topic_id"].astype(str) == str(topic_id)]
        print(f"Topic {topic_id}: {', '.join(terms)}")
        for text in topic_docs["text"].dropna().head(3):
            print(f"  - {str(text).replace(chr(10), ' ')[:220]}")
        print()


if __name__ == "__main__":
    main()
