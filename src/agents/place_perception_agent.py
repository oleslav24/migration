from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .context_pack import utc_now
from .report_i18n import rt
from .table_utils import ensure_toponyms, output_root_for, read_context_tables, text_column, write_json


PLACE_TAXONOMY: dict[str, tuple[str, ...]] = {
    "affordability": ("cheap", "expensive", "price", "cost", "rent", "дешев", "дорог", "цена", "стоимость"),
    "safety": ("safe", "danger", "crime", "police", "безопас", "опасно", "полиция"),
    "infrastructure": ("school", "hospital", "internet", "mall", "road", "школ", "больниц", "интернет", "дорог"),
    "mobility": ("traffic", "bts", "mrt", "taxi", "bike", "bus", "пробк", "такси", "байк", "транспорт"),
    "climate": ("climate", "weather", "rain", "heat", "sea", "климат", "погода", "дожд", "жара", "море"),
    "community": ("community", "friends", "russian", "expat", "чат", "комьюнити", "друз", "русск"),
    "bureaucracy/legal": ("visa", "permit", "immigration", "documents", "виза", "документ", "иммиграц"),
    "housing": ("condo", "apartment", "house", "landlord", "deposit", "кондо", "квартир", "дом", "залог"),
    "tourism/temporary stay": ("tourist", "hotel", "vacation", "trip", "турист", "отель", "отпуск", "поездк"),
    "adaptation problems": ("problem", "difficult", "language", "scam", "проблем", "сложно", "язык", "обман"),
}


def classify_place_perception(text: object) -> str:
    value = str(text or "").lower()
    scores = {label: sum(1 for keyword in keywords if keyword in value) for label, keywords in PLACE_TAXONOMY.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "adaptation problems"


def run_place_perception_agent(contract_path: str | Path, workspace: str | Path = ".", output_root: str | Path | None = None, report_language: str = "en") -> dict[str, Any]:
    context_pack, frame = read_context_tables(contract_path, workspace, output_root)
    root = output_root_for(contract_path, workspace, output_root, "data/agent_place_perception")
    column = text_column(frame)
    limitations: list[str] = []
    if frame.empty or column is None:
        limitations.append("No text-bearing tables were available for place perception analysis.")
        return _write_outputs(root, pd.DataFrame(), limitations, context_pack, report_language)
    frame = ensure_toponyms(frame)
    frame["place_perception"] = frame[column].map(classify_place_perception)
    distribution = frame["place_perception"].value_counts().rename_axis("place_perception").reset_index(name="count")
    distribution["share"] = distribution["count"] / distribution["count"].sum()
    distribution.to_csv(root / "place_perception_distribution.csv", index=False, encoding="utf-8")
    _by_toponym(frame).to_csv(root / "place_perception_by_toponym.csv", index=False, encoding="utf-8")
    _by_source(frame).to_csv(root / "place_perception_by_source.csv", index=False, encoding="utf-8")
    examples = _examples(frame, column)
    return _write_outputs(root, examples, limitations, context_pack, report_language)


def _by_toponym(frame: pd.DataFrame) -> pd.DataFrame:
    exploded = frame.explode("toponyms").rename(columns={"toponyms": "toponym"}).dropna(subset=["toponym"])
    if exploded.empty:
        return pd.DataFrame(columns=["toponym", "place_perception", "count", "share"])
    counts = exploded.groupby(["toponym", "place_perception"]).size().reset_index(name="count")
    counts["share"] = counts["count"] / counts.groupby("toponym")["count"].transform("sum")
    return counts


def _by_source(frame: pd.DataFrame) -> pd.DataFrame:
    if "source" not in frame:
        return pd.DataFrame(columns=["source", "place_perception", "count", "share"])
    counts = frame.groupby(["source", "place_perception"]).size().reset_index(name="count")
    counts["share"] = counts["count"] / counts.groupby("source")["count"].transform("sum")
    return counts


def _examples(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    rows = []
    for label, group in frame.groupby("place_perception", sort=True):
        sample = group.head(3)
        for _, row in sample.iterrows():
            rows.append({
                "evidence_id": f"place:{label}:row:{row.get('row_index')}",
                "place_perception": label,
                "source_path": row.get("source_path"),
                "row_index": row.get("row_index"),
                "text": str(row.get(column, ""))[:1000],
            })
    return pd.DataFrame(rows)


def _write_outputs(root: Path, examples: pd.DataFrame, limitations: list[str], context_pack: dict[str, Any], report_language: str = "en") -> dict[str, Any]:
    examples.to_csv(root / "place_perception_examples.csv", index=False, encoding="utf-8")
    write_json(root / "place_perception_evidence.json", {"created_at": utc_now(), "context_pack_path": context_pack.get("context_pack_path"), "evidence_items": examples.to_dict(orient="records"), "limitations": limitations})
    lines = [f"# {rt(report_language, 'place_report')}", "", f"## {rt(report_language, 'evidence_snippets')}", ""]
    if examples.empty:
        lines.append(rt(report_language, "no_evidence_snippets"))
    else:
        for row in examples.to_dict(orient="records"):
            lines.append(f"### {row['evidence_id']}")
            lines.append(f"{rt(report_language, 'source')}: `{row.get('source_path')}` {rt(report_language, 'row')} `{row.get('row_index')}`")
            lines.append("")
            lines.append("> " + row.get("text", "").replace("\n", " ")[:500])
            lines.append("")
    lines.extend([f"## {rt(report_language, 'limitations')}", ""])
    for limitation in limitations or [rt(report_language, "place_default_limitation")]:
        lines.append(f"- {limitation}")
    report_path = root / "place_perception_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return {"output_dir": str(root), "report_path": str(report_path), "evidence_items": len(examples), "limitations": limitations, "report_language": report_language}
