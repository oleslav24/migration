from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.toponyms import TOPONYM_META, city_level_stats, district_level_stats, sentiment_per_toponym, topics_per_toponym, toponym_frequency

from .context_pack import utc_now
from .report_i18n import rt
from .table_utils import ensure_toponyms, output_root_for, read_context_tables, text_column, write_json


def run_toponym_urban_space_agent(
    contract_path: str | Path,
    workspace: str | Path = ".",
    output_root: str | Path | None = None,
    random_state: int = 42,
    report_language: str = "en",
    hypothesis: str = "",
    dataset_scope: str = "all",
    top_n_toponyms: int = 10,
    samples_per_toponym: int = 3,
    max_texts_per_toponym: int = 500,
) -> dict[str, Any]:
    context_pack, frame = read_context_tables(contract_path, workspace, output_root)
    root = output_root_for(contract_path, workspace, output_root, "data/agent_toponyms")
    params = {
        "hypothesis": hypothesis,
        "dataset_scope": dataset_scope,
        "top_n_toponyms": int(top_n_toponyms),
        "samples_per_toponym": int(samples_per_toponym),
        "max_texts_per_toponym": int(max_texts_per_toponym),
        "random_state": int(random_state),
        "report_language": report_language,
    }
    if frame.empty:
        return _write_empty(root, context_pack, "No readable tables were available for toponym analysis.", report_language, params)
    frame = _filter_dataset_scope(frame, dataset_scope)
    if frame.empty:
        return _write_empty(root, context_pack, f"No rows matched dataset_scope={dataset_scope}.", report_language, params)
    frame = ensure_toponyms(frame)
    exploded = frame.explode("toponyms").rename(columns={"toponyms": "toponym"}).dropna(subset=["toponym"])
    exploded = exploded[exploded["toponym"].astype(str).str.len() > 0]
    if exploded.empty:
        return _write_empty(root, context_pack, "No toponyms were found in the allowed corpus context.", report_language, params)
    exploded["type"] = exploded["toponym"].map(lambda value: TOPONYM_META.get(str(value), {}).get("type"))
    exploded["parent_city"] = exploded["toponym"].map(lambda value: TOPONYM_META.get(str(value), {}).get("parent_city"))

    tables = {
        "toponym_frequency": toponym_frequency(frame),
        "city_level_stats": city_level_stats(frame),
        "district_level_stats": district_level_stats(frame),
        "source_comparison": _source_comparison(exploded),
        "sentiment_per_toponym": sentiment_per_toponym(frame),
        "topics_per_toponym": topics_per_toponym(frame),
        "drivers_per_toponym": _breakdown(exploded, "migration_driver"),
        "source_per_toponym": _breakdown(exploded, "source"),
    }
    for name, table in tables.items():
        table.to_csv(root / f"{name}.csv", index=False, encoding="utf-8")
    top_toponyms = _top_toponym_names(tables["toponym_frequency"], top_n_toponyms)
    samples = _samples(exploded[exploded["toponym"].isin(top_toponyms)], random_state, samples_per_toponym)
    samples.to_csv(root / "toponym_samples.csv", index=False, encoding="utf-8")
    texts_manifest = _export_texts_by_toponym(root, exploded, top_toponyms, max_texts_per_toponym)
    evidence = {
        "created_at": utc_now(),
        "context_pack_path": context_pack.get("context_pack_path"),
        "evidence_items": samples.to_dict(orient="records"),
        "limitations": [],
    }
    write_json(root / "toponym_context_pack.json", context_pack)
    write_json(root / "toponym_evidence_pack.json", evidence)
    manifest = {
        "created_at": utc_now(),
        "parameters": params,
        "top_toponyms": top_toponyms,
        "outputs": {
            "tables": [f"{name}.csv" for name in tables],
            "samples": "toponym_samples.csv",
            "texts_by_toponym": "texts_by_toponym/",
            "texts_by_toponym_manifest": "texts_by_toponym_manifest.json",
        },
        "texts_by_toponym": texts_manifest,
    }
    write_json(root / "toponym_research_manifest.json", manifest)
    report_path = _write_report(root, tables, samples, [], report_language, params, texts_manifest)
    return {
        "output_dir": str(root),
        "report_path": str(report_path),
        "evidence_items": len(samples),
        "limitations": [],
        "report_language": report_language,
        "research_manifest_path": str(root / "toponym_research_manifest.json"),
        "texts_by_toponym_dir": str(root / "texts_by_toponym"),
    }


def _filter_dataset_scope(frame: pd.DataFrame, dataset_scope: str) -> pd.DataFrame:
    scope = str(dataset_scope or "all").lower()
    if scope == "all" or "source" not in frame:
        return frame
    return frame[frame["source"].fillna("").astype(str).str.lower() == scope].copy()


def _breakdown(exploded: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in exploded:
        return pd.DataFrame(columns=["toponym", column, "count", "share"])
    counts = exploded.groupby(["toponym", column]).size().reset_index(name="count")
    totals = counts.groupby("toponym")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return counts.sort_values(["toponym", "count"], ascending=[True, False]).reset_index(drop=True)


def _source_comparison(exploded: pd.DataFrame) -> pd.DataFrame:
    if "source" not in exploded:
        return pd.DataFrame(columns=["source", "count", "share"])
    counts = exploded["source"].fillna("unknown").astype(str).str.lower().value_counts().rename_axis("source").reset_index(name="count")
    counts["share"] = counts["count"] / counts["count"].sum()
    return counts.sort_values(["count", "source"], ascending=[False, True]).reset_index(drop=True)


def _top_toponym_names(frequency: pd.DataFrame, top_n: int) -> list[str]:
    if frequency.empty or "toponym" not in frequency:
        return []
    return frequency.head(max(1, int(top_n)))["toponym"].astype(str).tolist()


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


def _export_texts_by_toponym(root: Path, exploded: pd.DataFrame, top_toponyms: list[str], max_texts_per_toponym: int) -> list[dict[str, Any]]:
    target = root / "texts_by_toponym"
    target.mkdir(parents=True, exist_ok=True)
    column = text_column(exploded) or "text"
    manifest: list[dict[str, Any]] = []
    for toponym in top_toponyms:
        group = exploded[exploded["toponym"] == toponym].head(max_texts_per_toponym).copy()
        keep = [
            c
            for c in ["source", "source_path", "source_file", "row_index", "datetime", "group", "toponym", "parent_city", "type", "sentiment", "topic_id", "migration_driver", column]
            if c in group
        ]
        out = group[keep].copy()
        if column in out and column != "text":
            out = out.rename(columns={column: "text"})
        filename = _safe_filename(toponym) + ".csv"
        out.to_csv(target / filename, index=False, encoding="utf-8")
        manifest.append({"toponym": toponym, "path": str((target / filename).relative_to(root)), "rows": int(len(out))})
    write_json(root / "texts_by_toponym_manifest.json", {"items": manifest, "max_texts_per_toponym": int(max_texts_per_toponym)})
    return manifest


def _safe_filename(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "_" for char in str(value)).strip("_")
    return safe or "toponym"


def _write_empty(root: Path, context_pack: dict[str, Any], limitation: str, report_language: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    write_json(root / "toponym_context_pack.json", context_pack)
    write_json(root / "toponym_evidence_pack.json", {"evidence_items": [], "limitations": [limitation]})
    write_json(root / "toponym_research_manifest.json", {"created_at": utc_now(), "parameters": params or {}, "limitations": [limitation], "texts_by_toponym": []})
    write_json(root / "texts_by_toponym_manifest.json", {"items": [], "max_texts_per_toponym": (params or {}).get("max_texts_per_toponym")})
    report_path = _write_report(root, {}, pd.DataFrame(), [limitation], report_language, params or {}, [])
    return {"output_dir": str(root), "report_path": str(report_path), "evidence_items": 0, "limitations": [limitation], "report_language": report_language}


def _write_report(
    root: Path,
    tables: dict[str, pd.DataFrame],
    samples: pd.DataFrame,
    limitations: list[str],
    report_language: str = "en",
    params: dict[str, Any] | None = None,
    texts_manifest: list[dict[str, Any]] | None = None,
) -> Path:
    params = params or {}
    texts_manifest = texts_manifest or []
    top_n = int(params.get("top_n_toponyms", 10))
    frequency = tables.get("toponym_frequency", pd.DataFrame())
    top_toponyms = frequency.head(max(1, top_n))["toponym"].astype(str).tolist() if "toponym" in frequency else []
    lines = [f"# {rt(report_language, 'toponym_research_report')}", ""]
    lines.extend([f"## {rt(report_language, 'research_hypothesis')}", "", params.get("hypothesis") or rt(report_language, "no_hypothesis_recorded"), ""])
    lines.extend([f"## {rt(report_language, 'corpus_method')}", ""])
    lines.append(f"- dataset_scope: `{params.get('dataset_scope', 'all')}`")
    lines.append(f"- top_n_toponyms: `{params.get('top_n_toponyms', 'n/a')}`")
    lines.append(f"- samples_per_toponym: `{params.get('samples_per_toponym', 'n/a')}`")
    lines.append(f"- max_texts_per_toponym: `{params.get('max_texts_per_toponym', 'n/a')}`")
    lines.append(f"- random_state: `{params.get('random_state', 'n/a')}`")
    lines.append(f"- report_language: `{params.get('report_language', report_language)}`")
    lines.append("")
    lines.extend([f"## {rt(report_language, 'key_observed_places')}", ""])
    _append_table_csv(lines, frequency.head(max(1, top_n)), rt(report_language, "no_evidence_samples"))
    lines.extend(["", f"## {rt(report_language, 'city_level_summary')}", ""])
    _append_table_csv(lines, tables.get("city_level_stats", pd.DataFrame()), rt(report_language, "no_evidence_samples"))
    lines.extend(["", f"## {rt(report_language, 'district_level_summary')}", ""])
    _append_table_csv(lines, tables.get("district_level_stats", pd.DataFrame()), rt(report_language, "no_evidence_samples"))
    lines.extend(["", f"## {rt(report_language, 'source_comparison')}", ""])
    _append_table_csv(lines, tables.get("source_comparison", pd.DataFrame()), rt(report_language, "no_evidence_samples"))
    lines.extend(["", f"## {rt(report_language, 'topics_per_toponym')}", ""])
    _append_table_csv(lines, _filter_table_by_toponyms(tables.get("topics_per_toponym", pd.DataFrame()), top_toponyms), rt(report_language, "no_evidence_samples"))
    lines.extend(["", f"## {rt(report_language, 'sentiment_per_toponym')}", ""])
    _append_table_csv(lines, _filter_table_by_toponyms(tables.get("sentiment_per_toponym", pd.DataFrame()), top_toponyms), rt(report_language, "no_evidence_samples"))
    lines.extend(["", f"## {rt(report_language, 'migration_drivers_per_toponym')}", ""])
    _append_table_csv(lines, _filter_table_by_toponyms(tables.get("drivers_per_toponym", pd.DataFrame()), top_toponyms), rt(report_language, "no_evidence_samples"))
    lines.extend(["", f"## {rt(report_language, 'evidence_examples')}", ""])
    lines.append(rt(report_language, "observed_evidence_intro"))
    lines.append("")
    if texts_manifest:
        lines.append(f"{rt(report_language, 'output_files')}:")
        for name, table in tables.items():
            lines.append(f"- `{name}.csv`: {len(table)} {rt(report_language, 'rows').lower()}")
        lines.append(f"- `toponym_samples.csv`: {len(samples)} {rt(report_language, 'rows').lower()}")
        lines.append(f"- `toponym_evidence_pack.json`")
    lines.append("")
    if samples.empty:
        lines.append(rt(report_language, "no_evidence_samples"))
    else:
        for row in samples.head(20).to_dict(orient="records"):
            lines.append(f"### {row.get('evidence_id')}")
            lines.append(f"{rt(report_language, 'source')}: `{row.get('source_path')}` {rt(report_language, 'row')} `{row.get('row_index')}`")
            lines.append("")
            lines.append("> " + str(row.get("text", ""))[:500].replace("\n", " "))
            lines.append("")
    lines.extend([f"## {rt(report_language, 'text_samples_exported')}", ""])
    if texts_manifest:
        for item in texts_manifest:
            lines.append(f"- `{item['toponym']}`: `{item['path']}` ({item['rows']} {rt(report_language, 'rows').lower()})")
    else:
        lines.append(rt(report_language, "no_evidence_samples"))
    lines.extend(["", f"## {rt(report_language, 'interpretation_notes')}", "", f"- {rt(report_language, 'toponym_interpretation_note')}", ""])
    lines.extend([f"## {rt(report_language, 'limitations')}", ""])
    for limitation in limitations or [rt(report_language, "toponym_default_limitation")]:
        lines.append(f"- {limitation}")
    path = root / "toponym_research_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _append_table_csv(lines: list[str], table: pd.DataFrame, empty_message: str, limit: int = 50) -> None:
    if table.empty:
        lines.append(empty_message)
        return
    lines.extend(["```csv", table.head(limit).to_csv(index=False).strip(), "```"])


def _filter_table_by_toponyms(table: pd.DataFrame, top_toponyms: list[str]) -> pd.DataFrame:
    if table.empty or "toponym" not in table or not top_toponyms:
        return table
    return table[table["toponym"].astype(str).isin(set(top_toponyms))].reset_index(drop=True)
