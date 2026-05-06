from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.toponyms import TOPONYM_META, city_level_stats, district_level_stats, sentiment_per_toponym, topics_per_toponym, toponym_frequency

from .context_pack import utc_now
from .table_utils import ensure_toponyms, output_root_for, read_context_tables, text_column, write_json


def run_toponym_urban_space_agent(contract_path: str | Path, workspace: str | Path = ".", output_root: str | Path | None = None, random_state: int = 42) -> dict[str, Any]:
    context_pack, frame = read_context_tables(contract_path, workspace, output_root)
    root = output_root_for(contract_path, workspace, output_root, "data/agent_toponyms")
    if frame.empty:
        return _write_empty(root, context_pack, "No readable tables were available for toponym analysis.")
    frame = ensure_toponyms(frame)
    exploded = frame.explode("toponyms").rename(columns={"toponyms": "toponym"}).dropna(subset=["toponym"])
    exploded = exploded[exploded["toponym"].astype(str).str.len() > 0]
    if exploded.empty:
        return _write_empty(root, context_pack, "No toponyms were found in the allowed corpus context.")
    exploded["type"] = exploded["toponym"].map(lambda value: TOPONYM_META.get(str(value), {}).get("type"))
    exploded["parent_city"] = exploded["toponym"].map(lambda value: TOPONYM_META.get(str(value), {}).get("parent_city"))

    tables = {
        "toponym_frequency": toponym_frequency(frame),
        "city_level_stats": city_level_stats(frame),
        "district_level_stats": district_level_stats(frame),
        "sentiment_per_toponym": sentiment_per_toponym(frame),
        "topics_per_toponym": topics_per_toponym(frame),
        "drivers_per_toponym": _breakdown(exploded, "migration_driver"),
        "source_per_toponym": _breakdown(exploded, "source"),
    }
    for name, table in tables.items():
        table.to_csv(root / f"{name}.csv", index=False, encoding="utf-8")
    samples = _samples(exploded, random_state)
    samples.to_csv(root / "toponym_samples.csv", index=False, encoding="utf-8")
    evidence = {
        "created_at": utc_now(),
        "context_pack_path": context_pack.get("context_pack_path"),
        "evidence_items": samples.to_dict(orient="records"),
        "limitations": [],
    }
    write_json(root / "toponym_context_pack.json", context_pack)
    write_json(root / "toponym_evidence_pack.json", evidence)
    report_path = _write_report(root, tables, samples, [])
    return {"output_dir": str(root), "report_path": str(report_path), "evidence_items": len(samples), "limitations": []}


def _breakdown(exploded: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in exploded:
        return pd.DataFrame(columns=["toponym", column, "count", "share"])
    counts = exploded.groupby(["toponym", column]).size().reset_index(name="count")
    totals = counts.groupby("toponym")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return counts.sort_values(["toponym", "count"], ascending=[True, False]).reset_index(drop=True)


def _samples(exploded: pd.DataFrame, random_state: int, per_toponym: int = 3) -> pd.DataFrame:
    column = text_column(exploded) or "text"
    rows: list[pd.DataFrame] = []
    for toponym, group in exploded.groupby("toponym", sort=True):
        sample = group.sample(n=min(per_toponym, len(group)), random_state=random_state)
        keep = [c for c in ["toponym", "type", "parent_city", "source_path", "source_file", "row_index", "source", "group", "sentiment", "topic_id", "migration_driver", column] if c in sample]
        part = sample[keep].copy()
        if column in part and column != "text":
            part = part.rename(columns={column: "text"})
        part["evidence_id"] = [f"toponym:{toponym}:row:{idx}" for idx in part["row_index"]]
        rows.append(part)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _write_empty(root: Path, context_pack: dict[str, Any], limitation: str) -> dict[str, Any]:
    write_json(root / "toponym_context_pack.json", context_pack)
    write_json(root / "toponym_evidence_pack.json", {"evidence_items": [], "limitations": [limitation]})
    report_path = _write_report(root, {}, pd.DataFrame(), [limitation])
    return {"output_dir": str(root), "report_path": str(report_path), "evidence_items": 0, "limitations": [limitation]}


def _write_report(root: Path, tables: dict[str, pd.DataFrame], samples: pd.DataFrame, limitations: list[str]) -> Path:
    lines = ["# Toponym Urban Space Report", "", "## Outputs", ""]
    for name, table in tables.items():
        lines.append(f"- `{name}.csv`: {len(table)} rows")
    lines.extend(["", "## Evidence Samples", ""])
    if samples.empty:
        lines.append("No evidence samples available.")
    else:
        for row in samples.head(20).to_dict(orient="records"):
            lines.append(f"### {row.get('evidence_id')}")
            lines.append(f"Source: `{row.get('source_path')}` row `{row.get('row_index')}`")
            lines.append("")
            lines.append("> " + str(row.get("text", ""))[:500].replace("\n", " "))
            lines.append("")
    lines.extend(["## Limitations", ""])
    for limitation in limitations or ["Analysis is based only on allowed local context and extracted toponyms."]:
        lines.append(f"- {limitation}")
    path = root / "toponym_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

