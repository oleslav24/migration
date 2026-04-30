from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .models import ArticleCandidate, DownloadResult, discovery_config


def export_discovery_results(
    candidates: list[ArticleCandidate],
    selected: list[ArticleCandidate],
    rejected: list[ArticleCandidate],
    config,
    downloads: list[DownloadResult] | None = None,
) -> None:
    cfg = discovery_config(config)
    output_dir = Path(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    _frame(candidates).to_csv(output_dir / "candidates.csv", index=False, encoding="utf-8")
    _write_parquet(_frame(candidates), output_dir / "candidates.parquet")
    _frame(selected).to_csv(output_dir / "selected_articles.csv", index=False, encoding="utf-8")
    _frame(rejected).to_csv(output_dir / "rejected_articles.csv", index=False, encoding="utf-8")
    (output_dir / "discovery_report.md").write_text(
        _report(candidates, selected, rejected, downloads or []), encoding="utf-8"
    )


def _frame(candidates: list[ArticleCandidate]) -> pd.DataFrame:
    rows = []
    for candidate in candidates:
        row = candidate.to_dict()
        row["authors"] = "; ".join(candidate.authors)
        row["keywords"] = "; ".join(candidate.keywords)
        row["metadata"] = json.dumps(candidate.metadata, ensure_ascii=False)
        rows.append(row)
    return pd.DataFrame(rows)


def candidates_from_csv(path: str | Path) -> list[ArticleCandidate]:
    frame = pd.read_csv(path).fillna("")
    candidates: list[ArticleCandidate] = []
    for _, row in frame.iterrows():
        metadata: dict[str, Any] = {}
        if row.get("metadata"):
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                metadata = {}
        candidates.append(
            ArticleCandidate(
                candidate_id=str(row.get("candidate_id", "")),
                source=str(row.get("source", "")),
                query_id=str(row.get("query_id", "")),
                title=str(row.get("title", "")),
                authors=[value for value in str(row.get("authors", "")).split("; ") if value],
                year=_int(row.get("year")),
                journal=str(row.get("journal") or "") or None,
                abstract=str(row.get("abstract") or "") or None,
                doi=str(row.get("doi") or "") or None,
                url=str(row.get("url") or "") or None,
                pdf_url=str(row.get("pdf_url") or "") or None,
                open_access=_bool(row.get("open_access")),
                citation_count=_int(row.get("citation_count")),
                language=str(row.get("language") or "") or None,
                keywords=[value for value in str(row.get("keywords", "")).split("; ") if value],
                relevance_score=float(row.get("relevance_score") or 0.0),
                reason=str(row.get("reason") or "") or None,
                metadata=metadata,
            )
        )
    return candidates


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    try:
        frame.to_parquet(path, index=False)
    except ImportError:
        frame.to_pickle(path)


def _report(candidates, selected, rejected, downloads: list[DownloadResult]) -> str:
    downloaded = [item for item in downloads if item.downloaded]
    lines = [
        "# Article Discovery Report",
        "",
        "## Summary",
        "",
        f"Total candidates: {len(candidates)}",
        f"After deduplication: {len(candidates)}",
        f"Selected: {len(selected)}",
        f"Downloaded PDFs: {len(downloaded)}",
        "",
        "## Selected articles",
        "",
        "| Score | Year | Title | Source | DOI | OA | PDF |",
        "|---|---:|---|---|---|---|---|",
    ]
    for candidate in selected:
        lines.append(
            f"| {candidate.relevance_score or 0:.3f} | {candidate.year or ''} | {candidate.title} | "
            f"{candidate.source} | {candidate.doi or ''} | {candidate.open_access} | {candidate.pdf_url or ''} |"
        )
    lines.extend(["", "## Rejected articles", "", "Причины отклонения:", "- низкая релевантность", "- нет open access full text", ""])
    for candidate in rejected[:50]:
        lines.append(f"- {candidate.title} — {candidate.reason or 'not selected'}")
    return "\n".join(lines)


def _int(value) -> int | None:
    try:
        if value == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _bool(value) -> bool | None:
    if value in ("", None):
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}
