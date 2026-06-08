from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_manual_coding_report(annotations: pd.DataFrame, output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    coders = sorted(set(annotations.get("coder_id", pd.Series(dtype=str)).dropna().astype(str)))
    groups = sorted(set(annotations.get("group", pd.Series(dtype=str)).dropna().astype(str)))
    periods = sorted(set(annotations.get("period", pd.Series(dtype=str)).dropna().astype(str)))
    freq = _field_frequency(annotations, "migration_driver")
    lines = [
        "# Manual Coding Report",
        "",
        "## Dataset",
        "",
        f"Total annotated items: {len(annotations)}",
        f"Coders: {', '.join(coders) if coders else 'n/a'}",
        f"Period: {', '.join(periods) if periods else 'n/a'}",
        f"Groups: {', '.join(groups) if groups else 'n/a'}",
        "",
        "## Code frequencies",
        "",
        freq.to_markdown(index=False) if not freq.empty else "No migration_driver codes.",
        "",
        "## Notes and memos",
        "",
    ]
    if "memo" in annotations.columns:
        memo_rows = annotations[annotations["memo"].astype(str).str.strip() != ""].head(20)
        for _, row in memo_rows.iterrows():
            lines.append(f"- {row.get('annotation_id', '')}: {str(row.get('memo', '')).strip()}")
    else:
        lines.append("No memo column.")
    out.write_text("\n".join(lines), encoding="utf-8")


def _field_frequency(frame: pd.DataFrame, field: str) -> pd.DataFrame:
    if field not in frame.columns:
        return pd.DataFrame(columns=[field, "count"])
    counts = frame[field].fillna("unknown").astype(str).value_counts().rename_axis(field).reset_index(name="count")
    return counts

