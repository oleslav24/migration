from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_search_results(results: pd.DataFrame, query: str, output_dir: str | Path, stem: str = "literature_search_results") -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    results.to_csv(target / f"{stem}.csv", index=False, encoding="utf-8")
    (target / f"{stem}.md").write_text(_to_markdown(results, query), encoding="utf-8")


def _to_markdown(results: pd.DataFrame, query: str) -> str:
    lines = ["# Literature search results", "", "## Query", query, ""]
    for _, row in results.iterrows():
        lines.extend(
            [
                f"## Result {int(row['rank'])}",
                f"File: {row['filename']}",
                f"Page: {_display_value(row.get('page_number'))}",
                f"Chunk: {row['chunk_index']}",
                f"Score: {float(row['score']):.4f}",
                "",
                "Excerpt:",
                str(row["text"]),
                "",
            ]
        )
    return "\n".join(lines)


def _display_value(value) -> str:
    if pd.isna(value):
        return ""
    return str(value)
