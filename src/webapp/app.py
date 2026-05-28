from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import yaml

from src.data_loader import _load_line_parsed_csv, _needs_line_parser
from src.agents.experiment_registry import load_registry
from src.agents.place_perception_agent import classify_place_perception
from src.language import detect_language
from src.migration_drivers import classify_migration_driver
from src.preprocess import clean_text, fix_encoding
from src.sentiment import classify_sentiment
from src.toponyms import TOPONYM_META, extract_toponyms


ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / "static"
RUNS_DIR = ROOT / "data" / "web_runs"
RUNS: dict[str, dict] = {}

PRESET_COMMANDS = {
    "pipeline_default": {
        "label": "Run full pipeline",
        "command": ["python", "-B", "-m", "src.webapp.runner", "pipeline-full"],
        "description": "Runs the full Telegram + YouTube corpus with local hash embeddings into a run-specific output directory.",
    },
    "pipeline_smoke": {
        "label": "Run smoke pipeline",
        "command": ["python", "-B", "-m", "src.webapp.runner", "pipeline-smoke"],
        "description": "Fast hash-backend smoke run for pipeline export validation.",
    },
    "youtube_sample": {
        "label": "Run YouTube sample",
        "command": ["python", "-B", "-m", "src.webapp.runner", "youtube-sample"],
        "description": "Runs 2,000 YouTube comments through the pipeline with hash embeddings.",
    },
    "discovery_search": {
        "label": "Run article discovery",
        "command": [
            "python",
            "-B",
            "-m",
            "src.discovery.cli",
            "search",
            "--config",
            "config.yaml",
            "--queries",
            "queries/article_discovery_queries.yaml",
        ],
        "description": "Queries Crossref/OpenAlex/arXiv/Semantic Scholar and refreshes data/discovery outputs.",
    },
    "literature_summarize_all": {
        "label": "Run literature summaries",
        "command": ["python", "-B", "-m", "src.webapp.runner", "literature-summaries"],
        "description": "Builds extractive summaries from the local literature index if it exists.",
    },
}

AGENT_RUNNERS = {"analyze-corpus", "toponym-agent", "place-perception", "sampling-coding", "migration-narrative", "literature-bridge", "research-story-e2e"}


class WebHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        if parsed.path == "/":
            return str(STATIC_DIR / "index.html")
        return str(STATIC_DIR / parsed.path.lstrip("/"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/summary":
            self._json(summary_payload())
        elif parsed.path == "/api/table":
            params = parse_qs(parsed.query)
            self._json(table_payload(
                params.get("path", [""])[0],
                params.get("q", [""])[0],
                _safe_int(params.get("limit", ["100"])[0], default=100, minimum=1, maximum=500),
            ))
        elif parsed.path == "/api/runs":
            self._json({"runs": sorted(RUNS.values(), key=lambda item: item["created_at"], reverse=True)})
        elif parsed.path == "/api/run-compare":
            params = parse_qs(parsed.query)
            self._json(compare_run_manifests(params.get("a", [""])[0], params.get("b", [""])[0]))
        elif parsed.path == "/api/run-comparison-candidates":
            params = parse_qs(parsed.query)
            self._json(
                run_comparison_candidates(
                    params.get("experiment_id", [""])[0],
                    params.get("run_id", [""])[0],
                    _safe_int(params.get("limit", ["6"])[0], default=6, minimum=1, maximum=30),
                )
            )
        elif parsed.path == "/api/run-log":
            params = parse_qs(parsed.query)
            self._text(read_run_log(params.get("id", [""])[0]))
        elif parsed.path == "/api/report":
            params = parse_qs(parsed.query)
            self._text(read_report(params.get("path", [""])[0]))
        elif parsed.path == "/api/evidence":
            params = parse_qs(parsed.query)
            self._json(evidence_payload(
                params.get("path", [""])[0],
                {
                    "source": params.get("source", [""])[0],
                    "toponym": params.get("toponym", [""])[0],
                    "sentiment": params.get("sentiment", [""])[0],
                    "driver": params.get("driver", [""])[0],
                    "topic": params.get("topic", [""])[0],
                    "text": params.get("text", [""])[0],
                },
                _safe_int(params.get("limit", ["100"])[0], default=100, minimum=1, maximum=500),
            ))
        else:
            super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/method-sample":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            self._json(method_sample_payload(str(payload.get("text") or "")))
            return
        if parsed.path == "/api/report-bundle":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            self._json(build_report_bundle(payload))
            return
        if parsed.path == "/api/run-packet":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            self._json(build_run_packet(payload))
            return
        if parsed.path == "/api/run-comparison":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            self._json(build_run_comparison(payload))
            return
        if parsed.path != "/api/run":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        experiment = payload.get("experiment")
        params = payload.get("params") or {}
        if experiment:
            try:
                self._json(start_experiment_run(experiment, params), status=202)
            except Exception as exc:
                self._json({"error": str(exc)}, status=500)
            return
        self.send_error(400, "Registry experiment is required")

    def _json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _text(self, value: str, status: int = 200) -> None:
        data = value.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def summary_payload() -> dict:
    config = _read_yaml(ROOT / "config.yaml")
    experiments = _registry_payload()
    files = {
        "pipeline": _csv_info(ROOT / "data" / "output"),
        "discovery": _csv_info(ROOT / "data" / "discovery"),
        "literature_summaries": _file_info(ROOT / "data" / "output" / "literature_summaries", {".md", ".json"}),
    }
    charts = {
        "topics": _chart_from_csv(ROOT / "data" / "output" / "topic_distribution.csv", "topic_id", "count"),
        "drivers": _chart_from_csv(ROOT / "data" / "output" / "migration_driver_distribution.csv", "migration_driver", "count"),
        "toponyms": _chart_from_csv(ROOT / "data" / "output" / "toponym_frequency.csv", "toponym", "count", limit=10),
        "discovery_sources": _value_counts(ROOT / "data" / "discovery" / "candidates.csv", "source"),
        "selected_sources": _value_counts(ROOT / "data" / "discovery" / "selected_articles.csv", "source"),
    }
    return {
        "config": {
            "input_path": config.get("input_path"),
            "input_paths": config.get("input_paths", []),
            "output_dir": config.get("output_dir"),
            "literature_index_dir": config.get("literature", {}).get("index_dir"),
            "discovery_output_dir": config.get("discovery", {}).get("output_dir"),
        },
        "files": files,
        "agent_files": _agent_file_info(),
        "experiment_outputs": _experiment_outputs_payload(experiments),
        "project_state": _project_state(config, files, experiments),
        "methods": _methods_payload(config),
        "run_manifests": _run_manifests_payload(),
        "safety": _safety_payload(),
        "charts": charts,
        "presets": {},
        "experiments": experiments,
    }


def table_payload(path_value: str, query: str = "", limit: int = 100) -> dict:
    path = _safe_data_path(path_value)
    if path is None or not path.exists() or path.suffix.lower() != ".csv":
        return {"columns": [], "rows": [], "error": "CSV not found or path is not allowed"}
    try:
        frame, scanned_rows = _read_preview_csv(path, query, limit)
    except Exception as exc:
        return {"columns": [], "rows": [], "error": str(exc)}
    return {
        "columns": frame.columns.tolist(),
        "rows": frame.fillna("").astype(str).to_dict(orient="records"),
        "path": str(path.relative_to(ROOT)),
        "query": query,
        "limit": limit,
        "returned_rows": len(frame),
        "scanned_rows": scanned_rows,
        "size": path.stat().st_size,
    }


def _read_preview_csv(path: Path, query: str, limit: int) -> tuple[pd.DataFrame, int]:
    value = query.strip().lower()
    if _needs_line_parser(path):
        return _read_line_parsed_preview(path, value, limit)
    if not value:
        frame = pd.read_csv(path, nrows=limit)
        return frame, len(frame)

    frames: list[pd.DataFrame] = []
    scanned_rows = 0
    for chunk in pd.read_csv(path, chunksize=5000):
        scanned_rows += len(chunk)
        mask = chunk.fillna("").astype(str).apply(lambda column: column.str.lower().str.contains(value, regex=False)).any(axis=1)
        matched = chunk.loc[mask]
        if not matched.empty:
            frames.append(matched)
        if sum(len(frame) for frame in frames) >= limit:
            break
    if not frames:
        columns = pd.read_csv(path, nrows=0).columns
        return pd.DataFrame(columns=columns), scanned_rows
    return pd.concat(frames, ignore_index=True).head(limit), scanned_rows


def _read_line_parsed_preview(path: Path, query: str, limit: int) -> tuple[pd.DataFrame, int]:
    frames: list[pd.DataFrame] = []
    scanned_rows = 0
    source = _source_from_name(path.name)
    for chunk in _load_line_parsed_csv(path, source, chunk_size=5000):
        scanned_rows += len(chunk)
        if query:
            mask = chunk.fillna("").astype(str).apply(lambda column: column.str.lower().str.contains(query, regex=False)).any(axis=1)
            chunk = chunk.loc[mask]
        if not chunk.empty:
            frames.append(chunk)
        if sum(len(frame) for frame in frames) >= limit:
            break
    if not frames:
        return pd.DataFrame(), scanned_rows
    return pd.concat(frames, ignore_index=True).head(limit), scanned_rows


def method_sample_payload(text: str) -> dict:
    config = _read_yaml(ROOT / "config.yaml")
    normalized = clean_text(fix_encoding(text)).lower()
    if not normalized:
        return {"error": "Text is empty.", "input": text, "normalized_text": ""}
    toponyms = extract_toponyms(normalized)
    return {
        "input": text,
        "normalized_text": normalized,
        "results": [
            {
                "method": "language_detection",
                "label": detect_language(normalized, config.get("language_detection", {})),
                "confidence": "heuristic",
                "evidence": normalized[:240],
            },
            {
                "method": "sentiment",
                "label": classify_sentiment(normalized),
                "confidence": "heuristic",
                "evidence": normalized[:240],
            },
            {
                "method": "migration_drivers",
                "label": classify_migration_driver(normalized),
                "confidence": "keyword-match",
                "evidence": normalized[:240],
            },
            {
                "method": "toponyms",
                "label": ", ".join(toponyms) if toponyms else "none",
                "confidence": "dictionary-match",
                "evidence": [
                    {"toponym": item, "type": TOPONYM_META.get(item, {}).get("type"), "parent_city": TOPONYM_META.get(item, {}).get("parent_city")}
                    for item in toponyms
                ],
            },
            {
                "method": "place_perception",
                "label": classify_place_perception(normalized),
                "confidence": "keyword-match",
                "evidence": normalized[:240],
            },
        ],
    }


def evidence_payload(path_value: str, filters: dict[str, str] | None = None, limit: int = 100) -> dict:
    path = _safe_artifact_path(path_value)
    if path is None or not path.exists() or path.suffix.lower() not in {".csv", ".json"}:
        return {"columns": [], "rows": [], "error": "Evidence file not found or path is not allowed"}
    try:
        frame = _evidence_frame(path)
        filtered = _filter_evidence_frame(frame, filters or {}).head(limit)
    except Exception as exc:
        return {"columns": [], "rows": [], "error": str(exc)}
    return {
        "columns": filtered.columns.tolist(),
        "rows": filtered.fillna("").astype(str).to_dict(orient="records"),
        "path": str(path.relative_to(ROOT)),
        "total_rows": len(frame),
        "returned_rows": len(filtered),
        "filters": filters or {},
    }


def _evidence_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
    if isinstance(data, dict):
        items = data.get("evidence_items") or data.get("evidence") or data.get("items") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []
    frame = pd.DataFrame(items)
    for column in frame.columns:
        frame[column] = frame[column].map(lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value)
    return frame


def _filter_evidence_frame(frame: pd.DataFrame, filters: dict[str, str]) -> pd.DataFrame:
    result = frame.copy()
    filter_columns = {
        "source": ["source", "source_path", "filename", "path"],
        "toponym": ["toponym", "toponyms", "parent_city"],
        "sentiment": ["sentiment"],
        "driver": ["migration_driver", "driver"],
        "topic": ["topic_id", "topic"],
        "text": ["text", "excerpt", "summary", "query"],
    }
    for key, columns in filter_columns.items():
        value = (filters.get(key) or "").strip().lower()
        if not value:
            continue
        existing = [column for column in columns if column in result]
        if not existing:
            result = result.iloc[0:0]
            break
        mask = result[existing].fillna("").astype(str).apply(lambda column: column.str.lower().str.contains(value, regex=False)).any(axis=1)
        result = result.loc[mask]
    return result


def start_run(preset: str) -> dict:
    runs_dir = _runs_dir()
    run_id = f"{int(time.time())}_{preset}"
    log_path = runs_dir / f"{run_id}.log"
    item = {
        "id": run_id,
        "preset": preset,
        "label": PRESET_COMMANDS[preset]["label"],
        "status": "running",
        "created_at": time.time(),
        "finished_at": None,
        "log_path": str(log_path.relative_to(ROOT)),
    }
    RUNS[run_id] = item
    thread = threading.Thread(target=_run_command, args=(run_id, PRESET_COMMANDS[preset]["command"], log_path), daemon=True)
    thread.start()
    return item


def start_experiment_run(experiment_id: str, params: dict | None = None) -> dict:
    experiment = _experiment_by_id(experiment_id)
    run_id = f"{int(time.time())}_{experiment_id}"
    log_path = _runs_dir() / f"{run_id}.log"
    item = {
        "id": run_id,
        "preset": experiment_id,
        "label": experiment["title"],
        "status": "running",
        "created_at": time.time(),
        "finished_at": None,
        "log_path": str(log_path.relative_to(ROOT)),
    }
    RUNS[run_id] = item
    command = ["python", "-B", "-m", "src.agents.cli", "run-experiment", "--id", experiment_id, "--params", json.dumps(params or {})]
    thread = threading.Thread(target=_run_command, args=(run_id, command, log_path), daemon=True)
    thread.start()
    return item


def _run_command(run_id: str, command: list[str], log_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    with log_path.open("w", encoding="utf-8", errors="replace") as handle:
        completed = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, text=True, env=env)
        code = completed.returncode
    RUNS[run_id]["status"] = "completed" if code == 0 else f"failed:{code}"
    RUNS[run_id]["finished_at"] = time.time()
    _snapshot_run_manifest(run_id)


def _snapshot_run_manifest(run_id: str) -> None:
    item = RUNS.get(run_id)
    if not item:
        return
    experiment_id = str(item.get("preset") or "").strip()
    if not experiment_id:
        return
    source = ROOT / "tmp_write_check" / "agent_experiments" / experiment_id / "run_manifest.json"
    if not source.exists() or source.name != "run_manifest.json":
        return
    try:
        data = json.loads(source.read_text(encoding="utf-8-sig", errors="replace") or "{}")
    except json.JSONDecodeError:
        return
    if not isinstance(data, dict):
        return
    data["_web_run"] = {
        "run_id": run_id,
        "status": item.get("status"),
        "created_at": item.get("created_at"),
        "finished_at": item.get("finished_at"),
        "captured_at": time.time(),
    }
    snapshot_dir = _runs_dir() / "manifests" / run_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    target = snapshot_dir / "run_manifest.json"
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    item["manifest_path"] = str(target.relative_to(ROOT))


def _runs_dir() -> Path:
    preferred = ROOT / "data" / "web_runs"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return preferred
    except OSError:
        fallback = ROOT / "tmp_write_check" / "web_runs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def read_run_log(run_id: str) -> str:
    item = RUNS.get(run_id)
    if not item:
        return ""
    path = ROOT / item["log_path"]
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_report(path_value: str) -> str:
    path = _safe_report_path(path_value)
    if path is None or not path.exists() or path.suffix.lower() not in {".md", ".json"}:
        return "Report not found or path is not allowed."
    return path.read_text(encoding="utf-8", errors="replace")


def compare_run_manifests(path_a: str, path_b: str) -> dict:
    return _run_comparison(path_a, path_b)


def run_comparison_candidates(experiment_id: str, run_id: str = "", limit: int = 6) -> dict:
    exp_id = str(experiment_id or "").strip()
    if not exp_id:
        return {"error": "experiment_id is required", "experiment_id": "", "current": None, "baselines": []}
    manifests_all = [
        item
        for item in _run_manifests_payload()
        if item.get("experiment_id") == exp_id and not item.get("error")
    ]
    manifests_all.sort(key=lambda item: item.get("manifest_mtime") or 0.0, reverse=True)
    manifests_with_run = [item for item in manifests_all if str(item.get("run_id") or "").strip()]
    manifests = manifests_with_run if manifests_with_run else manifests_all
    if not manifests:
        return {"experiment_id": exp_id, "current": None, "baselines": [], "limit": max(limit, 1)}
    current = next((item for item in manifests if item.get("run_id") == run_id), manifests[0])
    baselines = [item for item in manifests if item.get("path") != current.get("path")]
    return {
        "experiment_id": exp_id,
        "current": _comparison_candidate_entry(current),
        "baselines": [_comparison_candidate_entry(item) for item in baselines[: max(limit, 1)]],
        "limit": max(limit, 1),
    }


def build_run_comparison(payload: dict) -> dict:
    comparison = _run_comparison(str(payload.get("a") or payload.get("manifest_a") or ""), str(payload.get("b") or payload.get("manifest_b") or ""))
    if comparison.get("error"):
        return {"error": comparison["error"]}
    output_dir = _run_comparison_output_dir(str(payload.get("output_dir") or ""))
    filename_stem = _run_comparison_filename(comparison)
    markdown_path = output_dir / f"{filename_stem}.md"
    json_path = output_dir / f"{filename_stem}.json"
    csv_path = output_dir / f"{filename_stem}.csv"
    exports = {
        "markdown": str(markdown_path.relative_to(ROOT)),
        "json": str(json_path.relative_to(ROOT)),
        "csv": str(csv_path.relative_to(ROOT)),
    }
    comparison["exports"] = exports
    markdown_path.write_text("\n".join(_run_comparison_markdown(comparison)), encoding="utf-8")
    json_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(comparison.get("differences") or []).to_csv(csv_path, index=False, encoding="utf-8")
    return {
        "paths": exports,
        "difference_count": len(comparison.get("differences") or []),
        "table_count": len(comparison.get("table_comparisons") or []),
        "comparison": comparison,
    }


def _run_comparison(path_a: str, path_b: str) -> dict:
    manifest_a = _load_manifest_summary(path_a)
    manifest_b = _load_manifest_summary(path_b)
    if manifest_a.get("error") or manifest_b.get("error"):
        return {"error": manifest_a.get("error") or manifest_b.get("error"), "differences": []}
    artifacts_a = _run_artifacts_summary(manifest_a)
    artifacts_b = _run_artifacts_summary(manifest_b)
    differences = _manifest_differences(manifest_a, manifest_b)
    differences.extend(_artifact_count_differences(artifacts_a, artifacts_b))
    table_comparisons = _table_comparisons(artifacts_a.get("tables", []), artifacts_b.get("tables", []))
    differences.extend(_table_differences(table_comparisons))
    return {
        "a": manifest_a,
        "b": manifest_b,
        "artifacts": {"a": artifacts_a, "b": artifacts_b},
        "table_comparisons": table_comparisons,
        "differences": differences,
    }


def _comparison_candidate_entry(manifest: dict) -> dict:
    params = manifest.get("params") if isinstance(manifest.get("params"), dict) else {}
    hypothesis = str(params.get("hypothesis") or "").strip()
    run_id = str(manifest.get("run_id") or "")
    label_parts = [run_id] if run_id else []
    if hypothesis:
        label_parts.append(hypothesis[:80])
    return {
        "path": manifest.get("path"),
        "run_id": run_id,
        "manifest_mtime": manifest.get("manifest_mtime"),
        "report_path": manifest.get("report_path"),
        "label": " | ".join(part for part in label_parts if part),
        "hypothesis": hypothesis,
    }


def _manifest_differences(manifest_a: dict, manifest_b: dict) -> list[dict]:
    rows: list[dict] = []

    def add(field: str, value_a: object, value_b: object, section: str = "manifest") -> None:
        if value_a != value_b:
            rows.append({"section": section, "field": field, "a": value_a, "b": value_b})

    for key in ["experiment_id", "title", "runner", "contract", "output_dir", "report_path", "evidence_items", "sample_size"]:
        add(key, manifest_a.get(key), manifest_b.get(key))
    params_a = manifest_a.get("params") if isinstance(manifest_a.get("params"), dict) else {}
    params_b = manifest_b.get("params") if isinstance(manifest_b.get("params"), dict) else {}
    for key in sorted(set(params_a) | set(params_b)):
        add(f"params.{key}", params_a.get(key), params_b.get(key), "params")
    add("limitations", manifest_a.get("limitations"), manifest_b.get("limitations"), "result")
    return rows


def _artifact_count_differences(artifacts_a: dict, artifacts_b: dict) -> list[dict]:
    rows: list[dict] = []
    counts_a = artifacts_a.get("counts") or {}
    counts_b = artifacts_b.get("counts") or {}
    for key in sorted(set(counts_a) | set(counts_b)):
        if counts_a.get(key) != counts_b.get(key):
            rows.append({"section": "artifacts", "field": f"artifact_counts.{key}", "a": counts_a.get(key), "b": counts_b.get(key)})
    return rows


KEY_COMPARISON_TABLES = {
    "toponym_frequency.csv",
    "migration_driver_distribution.csv",
    "city_level_stats.csv",
    "district_level_stats.csv",
    "source_comparison.csv",
    "topics_per_toponym.csv",
    "sentiment_per_toponym.csv",
    "drivers_per_toponym.csv",
    "place_perception_distribution.csv",
    "place_perception_by_toponym.csv",
    "place_perception_by_source.csv",
    "migration_narrative_matrix.csv",
    "coding_sample.csv",
    "coding_sample_by_toponym.csv",
}


def _run_artifacts_summary(manifest: dict) -> dict:
    files = _artifact_files_for_output(manifest.get("output_dir"))
    reports = [item for item in files if item["kind"] == "report"]
    tables = [item for item in files if item["kind"] == "table"]
    evidence = [item for item in files if item["kind"] == "evidence"]
    configs = [item for item in files if item["kind"] == "config"]
    primary_report = _primary_report(manifest, reports)
    return {
        "output_dir": manifest.get("output_dir"),
        "primary_report": primary_report,
        "reports": reports,
        "tables": tables,
        "evidence": evidence,
        "configs": configs,
        "counts": {"reports": len(reports), "tables": len(tables), "evidence": len(evidence), "configs": len(configs)},
    }


def _table_comparisons(tables_a: list[dict], tables_b: list[dict]) -> list[dict]:
    by_name_a = {item.get("name"): item for item in tables_a if item.get("name") in KEY_COMPARISON_TABLES}
    by_name_b = {item.get("name"): item for item in tables_b if item.get("name") in KEY_COMPARISON_TABLES}
    rows: list[dict] = []
    for name in sorted(set(by_name_a) | set(by_name_b)):
        profile_a = _table_profile(by_name_a.get(name))
        profile_b = _table_profile(by_name_b.get(name))
        rows.append({
            "table": name,
            "a": profile_a,
            "b": profile_b,
            "changed": _table_profile_signature(profile_a) != _table_profile_signature(profile_b),
        })
    return rows


def _table_profile(item: dict | None) -> dict | None:
    if not item or not item.get("path"):
        return None
    path = _safe_artifact_path(str(item.get("path")))
    if path is None or not path.exists() or path.suffix.lower() != ".csv":
        return None
    try:
        frame = pd.read_csv(path, nrows=200).fillna("")
    except Exception as exc:
        return {"path": item.get("path"), "name": item.get("name"), "error": str(exc), "rows_sampled": 0, "columns": [], "preview": ""}
    top = _table_profile_top(frame)
    return {
        "path": item.get("path"),
        "name": item.get("name"),
        "rows_sampled": len(frame),
        "columns": [str(column) for column in frame.columns],
        "preview": _table_profile_preview(frame),
        "top_label": top.get("label"),
        "top_value": top.get("value"),
    }


def _table_profile_preview(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    columns = [str(column) for column in frame.columns]
    label_column = next((column for column in ["toponym", "parent_city", "source", "migration_driver", "place_perception", "sentiment", "topic_id"] if column in frame), columns[0])
    value_column = next((column for column in ["count", "n", "total", "frequency", "sample_size"] if column in frame), columns[1] if len(columns) > 1 else columns[0])
    pairs = []
    for row in frame.head(5).astype(str).to_dict(orient="records"):
        label = row.get(label_column, "")
        value = row.get(value_column, "")
        pairs.append(f"{label}={value}" if value else label)
    return "; ".join(pairs)


def _table_profile_top(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"label": None, "value": None}
    columns = [str(column) for column in frame.columns]
    label_column = next((column for column in ["toponym", "parent_city", "source", "migration_driver", "place_perception", "sentiment", "topic_id"] if column in frame), columns[0])
    value_column = next((column for column in ["count", "n", "total", "frequency", "sample_size"] if column in frame), columns[1] if len(columns) > 1 else columns[0])
    row = frame.head(1).astype(str).to_dict(orient="records")[0]
    return {
        "label": row.get(label_column, ""),
        "value": _coerce_numeric(row.get(value_column, "")),
    }


def _coerce_numeric(value: object) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _table_profile_signature(profile: dict | None) -> tuple:
    if not profile:
        return (None,)
    return (profile.get("rows_sampled"), tuple(profile.get("columns") or []), profile.get("preview"), profile.get("error"))


def _table_differences(table_comparisons: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for item in table_comparisons:
        profile_a = item.get("a") or {}
        profile_b = item.get("b") or {}
        if not item.get("changed"):
            continue
        rows.append({
            "section": "tables",
            "field": f"table.{item.get('table')}",
            "a": _table_profile_summary(profile_a),
            "b": _table_profile_summary(profile_b),
        })
    return rows


def _table_profile_summary(profile: dict | None) -> str:
    if not profile:
        return "missing"
    if profile.get("error"):
        return f"error: {profile.get('error')}"
    return f"rows_sampled={profile.get('rows_sampled')}; top={profile.get('top_label')}:{profile.get('top_value')}; preview={profile.get('preview')}"


def build_report_bundle(payload: dict) -> dict:
    title = clean_text(str(payload.get("title") or "Research report bundle")) or "Research report bundle"
    paths = [str(item) for item in payload.get("paths", []) if item]
    if not paths:
        return {"error": "No report paths selected"}
    output_dir = ROOT / "tmp_write_check" / "web_report_studio"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "report_bundle.md"
    lines = [f"# {title}", "", "Generated from selected local artifacts. Review all evidence before using this in publication text.", ""]
    included = []
    for path_value in paths[:20]:
        path = _safe_artifact_path(path_value)
        if path is None or not path.exists() or path.suffix.lower() not in {".md", ".json", ".csv"}:
            continue
        included.append(str(path.relative_to(ROOT)))
        lines.extend([f"## {path.name}", "", f"Path: `{path.relative_to(ROOT)}`", ""])
        if path.suffix.lower() == ".csv":
            frame = pd.read_csv(path, nrows=20).fillna("")
            lines.extend(_markdown_table(frame))
        elif path.suffix.lower() == ".json":
            text = path.read_text(encoding="utf-8", errors="replace")[:6000]
            lines.extend(["```json", text, "```"])
        else:
            lines.append(path.read_text(encoding="utf-8", errors="replace")[:8000])
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return {"path": str(output_path.relative_to(ROOT)), "included": included, "count": len(included)}


def build_run_packet(payload: dict) -> dict:
    manifest = _manifest_for_packet(payload)
    if manifest.get("error"):
        return {"error": manifest["error"]}
    output_dir = manifest.get("output_dir")
    files = _artifact_files_for_output(output_dir)
    reports = [item for item in files if item["kind"] == "report"]
    tables = [item for item in files if item["kind"] == "table"]
    evidence = [item for item in files if item["kind"] == "evidence"]
    configs = [item for item in files if item["kind"] == "config"]
    primary_report = _primary_report(manifest, reports)
    packet_dir = _run_packet_output_dir(str(payload.get("output_dir") or ""))
    created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    filename = _packet_filename(manifest)
    output_path = packet_dir / filename
    lines = [
        f"# Run Packet: {manifest.get('title') or manifest.get('experiment_id') or 'experiment'}",
        "",
        "Generated from local run metadata and artifacts. Review all evidence before using this in publication text.",
        "",
        "## Run metadata",
        "",
        f"- Created: `{created_at}`",
        f"- Experiment: `{manifest.get('experiment_id') or ''}`",
        f"- Runner: `{manifest.get('runner') or ''}`",
        f"- Manifest: `{manifest.get('path') or ''}`",
        f"- Output directory: `{output_dir or ''}`",
        f"- Primary report: `{(primary_report or {}).get('path') or manifest.get('report_path') or ''}`",
        "",
        "## Parameters",
        "",
        "```json",
        json.dumps(manifest.get("params") or {}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Artifact summary",
        "",
        f"- Reports: `{len(reports)}`",
        f"- Tables: `{len(tables)}`",
        f"- Evidence files: `{len(evidence)}`",
        f"- Config/manifest files: `{len(configs)}`",
        "",
        "## Key artifacts",
        "",
    ]
    artifact_rows = _run_packet_artifact_rows(manifest, primary_report, reports, tables, evidence, configs)
    if artifact_rows:
        lines.extend(["| Kind | File | Path |", "| --- | --- | --- |"])
        for row in artifact_rows[:40]:
            lines.append(f"| {row['kind']} | {row['name']} | `{row['path']}` |")
    else:
        lines.append("No artifacts found for this run output directory.")
    lines.extend([
        "",
        "## Review notes",
        "",
        "- Treat this packet as an index of evidence and outputs, not as a final interpretation.",
        "- Open the linked report/table/evidence files before making research claims.",
        "",
    ])
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "path": str(output_path.relative_to(ROOT)),
        "created_at": created_at,
        "experiment_id": manifest.get("experiment_id"),
        "manifest_path": manifest.get("path"),
        "output_dir": output_dir,
        "artifact_count": len(artifact_rows),
    }


def _manifest_for_packet(payload: dict) -> dict:
    manifest_path = str(payload.get("manifest_path") or "")
    if manifest_path:
        return _load_manifest_summary(manifest_path)
    experiment_id = str(payload.get("experiment") or payload.get("experiment_id") or "")
    if not experiment_id:
        return {"error": "Manifest path or experiment id is required"}
    manifests = [item for item in _run_manifests_payload() if item.get("experiment_id") == experiment_id]
    if not manifests:
        return {"error": f"No run manifest found for experiment: {experiment_id}"}
    return manifests[0]


def _run_packet_output_dir(path_value: str = "") -> Path:
    if path_value:
        path = _safe_artifact_path(path_value)
        if path is not None and _is_allowed_artifact_root(path):
            path.mkdir(parents=True, exist_ok=True)
            return path
    preferred = ROOT / "data" / "output" / "web_run_packets"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except OSError:
        fallback = ROOT / "tmp_write_check" / "web_run_packets"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _packet_filename(manifest: dict) -> str:
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    experiment = str(manifest.get("experiment_id") or "experiment")
    safe_experiment = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in experiment)[:80]
    return f"{stamp}_{safe_experiment}_run_packet.md"


def _run_packet_artifact_rows(
    manifest: dict,
    primary_report: dict | None,
    reports: list[dict],
    tables: list[dict],
    evidence: list[dict],
    configs: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()

    def add(kind: str, item: dict | None) -> None:
        if not item or not item.get("path") or item["path"] in seen:
            return
        seen.add(item["path"])
        rows.append({"kind": kind, "name": item.get("name") or Path(item["path"]).name, "path": item["path"]})

    manifest_path = manifest.get("path")
    if manifest_path:
        add("manifest", {"path": manifest_path, "name": Path(str(manifest_path)).name})
    add("primary_report", primary_report)
    for kind, items in (("report", reports), ("table", tables), ("evidence", evidence), ("config", configs)):
        for item in items:
            add(kind, item)
    return rows


def _run_comparison_output_dir(path_value: str = "") -> Path:
    if path_value:
        path = _safe_artifact_path(path_value)
        if path is not None and _is_allowed_artifact_root(path):
            path.mkdir(parents=True, exist_ok=True)
            return path
    preferred = ROOT / "data" / "output" / "web_run_comparisons"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except OSError:
        fallback = ROOT / "tmp_write_check" / "web_run_comparisons"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _run_comparison_filename(comparison: dict) -> str:
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    experiment_a = str((comparison.get("a") or {}).get("experiment_id") or "a")
    experiment_b = str((comparison.get("b") or {}).get("experiment_id") or "b")
    raw = f"{experiment_a}_vs_{experiment_b}"
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in raw)[:100]
    return f"{stamp}_{safe}_run_comparison"


def _run_comparison_markdown(comparison: dict) -> list[str]:
    manifest_a = comparison.get("a") or {}
    manifest_b = comparison.get("b") or {}
    artifacts = comparison.get("artifacts") or {}
    title = f"{manifest_a.get('experiment_id') or 'A'} vs {manifest_b.get('experiment_id') or 'B'}"
    lines = [
        f"# Run Comparison: {title}",
        "",
        "Generated from local run manifests and output artifacts. Treat this as a reproducibility aid, not as a final interpretation.",
        "",
        "## Compared runs",
        "",
        "| Field | A | B |",
        "| --- | --- | --- |",
        f"| Manifest | `{manifest_a.get('path') or ''}` | `{manifest_b.get('path') or ''}` |",
        f"| Experiment | `{manifest_a.get('experiment_id') or ''}` | `{manifest_b.get('experiment_id') or ''}` |",
        f"| Runner | `{manifest_a.get('runner') or ''}` | `{manifest_b.get('runner') or ''}` |",
        f"| Output directory | `{manifest_a.get('output_dir') or ''}` | `{manifest_b.get('output_dir') or ''}` |",
        "",
        "## Parameter and metadata differences",
        "",
    ]
    differences = comparison.get("differences") or []
    if differences:
        frame = pd.DataFrame(differences)
        lines.extend(_markdown_table(frame[["section", "field", "a", "b"]] if {"section", "field", "a", "b"}.issubset(frame.columns) else frame))
    else:
        lines.extend(["No differences found in compared manifest summary fields or key artifact profiles.", ""])
    lines.extend([
        "",
        "## Artifact counts",
        "",
        "| Kind | A | B |",
        "| --- | ---: | ---: |",
    ])
    counts_a = ((artifacts.get("a") or {}).get("counts") or {})
    counts_b = ((artifacts.get("b") or {}).get("counts") or {})
    for key in ["reports", "tables", "evidence", "configs"]:
        lines.append(f"| {key} | {counts_a.get(key, 0)} | {counts_b.get(key, 0)} |")
    lines.extend(["", "## Key table comparison", ""])
    table_rows = comparison.get("table_comparisons") or []
    if table_rows:
        lines.extend(["| Table | A rows sampled | A preview | B rows sampled | B preview |", "| --- | ---: | --- | ---: | --- |"])
        for row in table_rows:
            profile_a = row.get("a") or {}
            profile_b = row.get("b") or {}
            lines.append(
                "| "
                + " | ".join(
                    _md_cell(value)
                    for value in [
                        row.get("table") or "",
                        profile_a.get("rows_sampled", "missing") if profile_a else "missing",
                        profile_a.get("preview", "") if profile_a else "",
                        profile_b.get("rows_sampled", "missing") if profile_b else "missing",
                        profile_b.get("preview", "") if profile_b else "",
                    ]
                )
                + " |"
            )
    else:
        lines.append("No comparable key tables found.")
    lines.extend([
        "",
        "## Review notes",
        "",
        "- Use this comparison to decide which run/report/evidence files need closer review.",
        "- Do not treat table deltas as causal findings without checking source texts and evidence snippets.",
        "",
    ])
    return lines


def _markdown_table(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return ["No rows.", ""]
    columns = [str(column) for column in frame.columns]
    rows = ["| " + " | ".join(_md_cell(column) for column in columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in frame.astype(str).to_dict(orient="records"):
        rows.append("| " + " | ".join(_md_cell(row.get(column, "")) for column in columns) + " |")
    return rows


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")[:300]


def _load_manifest_summary(path_value: str) -> dict:
    path = _safe_artifact_path(path_value)
    if path is None or not path.exists() or path.name != "run_manifest.json":
        return {"error": "Run manifest not found or path is not allowed"}
    try:
        # utf-8-sig handles BOM-prefixed manifests produced by some Windows editors.
        data = json.loads(path.read_text(encoding="utf-8-sig", errors="replace") or "{}")
    except json.JSONDecodeError:
        return {"error": f"Run manifest is not valid JSON: {path.relative_to(ROOT)}"}
    experiment = data.get("experiment", {}) if isinstance(data, dict) else {}
    result = data.get("result", {}) if isinstance(data, dict) else {}
    run_meta = data.get("_web_run", {}) if isinstance(data, dict) else {}
    run_id = run_meta.get("run_id") if isinstance(run_meta, dict) else None
    if not run_id:
        run_id = _manifest_run_id_from_path(path)
    return {
        "path": str(path.relative_to(ROOT)),
        "run_id": run_id,
        "experiment_id": experiment.get("id"),
        "title": experiment.get("title"),
        "runner": experiment.get("runner"),
        "contract": experiment.get("agent_contract"),
        "params": data.get("params", {}) if isinstance(data, dict) else {},
        "output_dir": result.get("output_dir") if isinstance(result, dict) else None,
        "report_path": result.get("report_path") if isinstance(result, dict) else None,
        "evidence_items": result.get("evidence_items") if isinstance(result, dict) else None,
        "limitations": result.get("limitations") if isinstance(result, dict) else None,
        "sample_size": result.get("sample_size") if isinstance(result, dict) else None,
    }


def _manifest_run_id_from_path(path: Path) -> str | None:
    try:
        parts = path.resolve().parts
    except OSError:
        return None
    for index, value in enumerate(parts):
        if value != "manifests":
            continue
        if index + 1 < len(parts):
            return str(parts[index + 1])
    return None


def _registry_payload() -> list[dict]:
    try:
        return load_registry(ROOT / "experiments" / "registry.yaml")
    except Exception:
        return []


def _project_state(config: dict, files: dict, experiments: list[dict]) -> dict:
    datasets = _dataset_payload(config)
    outputs = _outputs_payload(files)
    agents = _agents_payload(experiments)
    readiness = []
    if not datasets:
        readiness.append({"status": "missing", "label": "No configured datasets found"})
    elif any(item["exists"] for item in datasets):
        readiness.append({"status": "ready", "label": "At least one configured dataset is available"})
    else:
        readiness.append({"status": "missing", "label": "Configured datasets are not available"})
    readiness.append({"status": "ready" if experiments else "missing", "label": f"{len(experiments)} registry experiments available"})
    readiness.append({"status": "ready" if files.get("discovery") else "missing", "label": "Discovery outputs available" if files.get("discovery") else "Discovery outputs not found"})
    readiness.append({"status": "ready" if outputs["agent_artifacts"] else "missing", "label": "Agent artifacts available" if outputs["agent_artifacts"] else "Agent artifacts not created yet"})
    return {"datasets": datasets, "outputs": outputs, "agents": agents, "readiness": readiness}


def _dataset_payload(config: dict) -> list[dict]:
    raw_inputs = config.get("input_paths") or [{"path": config.get("input_path"), "source": "default"}]
    result = []
    for item in raw_inputs:
        if isinstance(item, str):
            path_value = item
            source = _source_from_name(item)
        else:
            path_value = item.get("path")
            source = item.get("source") or _source_from_name(path_value)
        if not path_value:
            continue
        path = _resolve_dataset_path(path_value)
        info = {"path": path_value, "resolved_path": str(path.relative_to(ROOT)) if path and path.exists() else path_value, "source": source, "exists": bool(path and path.exists())}
        if path and path.exists():
            info.update(_dataset_file_info(path))
        result.append(info)
    return result


def _resolve_dataset_path(path_value: str) -> Path | None:
    candidates = [ROOT / path_value, ROOT / "DS" / Path(path_value).name]
    return next((path for path in candidates if path.exists()), candidates[0])


def _dataset_file_info(path: Path) -> dict:
    info = {"name": path.name, "size": path.stat().st_size, "columns": [], "sample_rows": [], "row_count": None, "row_count_note": "not scanned"}
    if path.suffix.lower() != ".csv":
        return info
    try:
        if _needs_line_parser(path):
            sample = next(_load_line_parsed_csv(path, _source_from_name(path.name), 5), pd.DataFrame())
        else:
            sample = pd.read_csv(path, nrows=5, encoding="utf-8", on_bad_lines="skip")
        info["columns"] = sample.columns.tolist()
        info["sample_rows"] = sample.fillna("").astype(str).to_dict(orient="records")
        if path.stat().st_size <= 50_000_000:
            with path.open("rb") as handle:
                info["row_count"] = max(sum(1 for _ in handle) - 1, 0)
            info["row_count_note"] = "full count"
        else:
            info["row_count_note"] = "large file; row count is computed by pipeline runs"
    except Exception as exc:
        info["error"] = str(exc)
    return info


def _source_from_name(path_value: str | None) -> str:
    name = Path(path_value or "").name.lower()
    if "telegram" in name:
        return "telegram"
    if "youtube" in name:
        return "youtube"
    return "unknown"


def _outputs_payload(files: dict) -> dict:
    return {
        "pipeline_csv": len(files.get("pipeline", [])),
        "discovery_csv": len(files.get("discovery", [])),
        "literature_reports": len(files.get("literature_summaries", [])),
        "agent_artifacts": len(_agent_file_info()),
    }


def _run_manifests_payload() -> list[dict]:
    roots = [ROOT / "data", ROOT / "tmp_write_check"]
    result = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("run_manifest.json")):
            summary = _load_manifest_summary(str(path.relative_to(ROOT)))
            if not summary.get("error"):
                summary["manifest_mtime"] = path.stat().st_mtime
                result.append(summary)
    result.sort(key=lambda item: item.get("manifest_mtime") or 0.0, reverse=True)
    return result[:100]


def _experiment_outputs_payload(experiments: list[dict]) -> list[dict]:
    manifests = _run_manifests_payload()
    by_experiment: dict[str, dict] = {}
    for manifest in manifests:
        exp_id = manifest.get("experiment_id")
        if not exp_id:
            continue
        current = by_experiment.get(exp_id)
        if current is None or (manifest.get("manifest_mtime") or 0.0) > (current.get("manifest_mtime") or 0.0):
            by_experiment[exp_id] = manifest
    result = []
    for experiment in experiments:
        exp_id = experiment.get("id")
        manifest = by_experiment.get(exp_id, {})
        output_dir = manifest.get("output_dir")
        files = _artifact_files_for_output(output_dir)
        files.extend(_linked_artifacts_for_experiment(exp_id, manifest))
        files = _dedupe_artifacts(files)
        reports = [item for item in files if item["kind"] == "report"]
        evidence = [item for item in files if item["kind"] == "evidence"]
        tables = [item for item in files if item["kind"] == "table"]
        configs = [item for item in files if item["kind"] == "config"]
        primary_report = _primary_report(manifest, reports)
        key_table = _primary_table(exp_id, tables)
        key_evidence = _primary_evidence(exp_id, evidence)
        params = _manifest_params(manifest.get("params"))
        result.append({
            "id": exp_id,
            "title": experiment.get("title"),
            "runner": experiment.get("runner"),
            "status": "ready" if primary_report else "not_run",
            "hypothesis": params.get("hypothesis", ""),
            "report_language": params.get("report_language"),
            "last_params": params,
            "manifest_path": manifest.get("path"),
            "last_run_at": manifest.get("manifest_mtime"),
            "output_dir": output_dir,
            "primary_report": primary_report,
            "reports": reports,
            "evidence": evidence,
            "tables": tables,
            "configs": configs,
            "key_table": key_table,
            "key_evidence": key_evidence,
            "counts": {"reports": len(reports), "evidence": len(evidence), "tables": len(tables)},
        })
    return result


def _manifest_params(raw: object) -> dict[str, str | int | float | bool]:
    if not isinstance(raw, dict):
        return {}
    result: dict[str, str | int | float | bool] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, (str, int, float, bool)):
            result[key] = value
    return result


def _artifact_files_for_output(output_dir: str | None) -> list[dict]:
    if not output_dir:
        return []
    try:
        root = (ROOT / output_dir).resolve()
    except OSError:
        return []
    if not root.exists() or not _is_allowed_artifact_root(root):
        return []
    result = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".csv"}:
            result.append({
                "path": str(path.relative_to(ROOT)),
                "name": path.name,
                "size": path.stat().st_size,
                "kind": _artifact_kind(path),
            })
    return result


def _artifact_kind(path: Path) -> str:
    name = path.name.lower()
    if path.suffix.lower() == ".md":
        return "report"
    if path.suffix.lower() == ".csv":
        return "table"
    if "evidence" in name:
        return "evidence"
    if "manifest" in name or "config" in name or "context_pack" in name:
        return "config"
    return "evidence"


def _linked_artifacts_for_experiment(exp_id: str | None, manifest: dict) -> list[dict]:
    if exp_id != "research_story_e2e":
        return []
    output_dir = manifest.get("output_dir")
    if not output_dir:
        return []
    try:
        root = (ROOT / str(output_dir)).resolve()
    except OSError:
        return []
    if not root.exists() or not _is_allowed_artifact_root(root):
        return []

    summary_path = root / "research_story_e2e_summary.json"
    if not summary_path.exists():
        return []

    summary = _read_json(summary_path)
    if not isinstance(summary, dict):
        return []

    linked: list[dict] = []
    outputs = summary.get("outputs")
    if isinstance(outputs, dict):
        for value in outputs.values():
            artifact = _artifact_from_path_value(value)
            if artifact:
                linked.append(artifact)

    steps = summary.get("steps")
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict):
                continue
            artifact = _artifact_from_path_value(step.get("report_path"))
            if artifact:
                linked.append(artifact)
            output_artifacts = _step_output_artifacts(step.get("step"), step.get("output_dir"))
            linked.extend(output_artifacts)
    return linked


def _read_json(path: Path) -> dict | list | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return None
    if isinstance(value, (dict, list)):
        return value
    return None


def _artifact_from_path_value(path_value: object) -> dict | None:
    if not path_value:
        return None
    try:
        raw = Path(str(path_value))
    except Exception:
        return None
    try:
        path = raw.resolve() if raw.is_absolute() else (ROOT / raw).resolve()
    except OSError:
        return None
    if not path.exists() or not path.is_file():
        return None
    if path.suffix.lower() not in {".md", ".json", ".csv"}:
        return None
    if not _is_allowed_artifact_root(path):
        return None
    return {
        "path": str(path.relative_to(ROOT)),
        "name": path.name,
        "size": path.stat().st_size,
        "kind": _artifact_kind(path),
    }


def _step_output_artifacts(step_name: object, output_dir: object) -> list[dict]:
    if not output_dir:
        return []
    files_by_step = {
        "toponym": [
            "toponym_research_report.md",
            "toponym_frequency.csv",
            "source_comparison.csv",
            "topics_per_toponym.csv",
            "sentiment_per_toponym.csv",
            "migration_driver_distribution.csv",
            "texts_by_toponym_manifest.json",
            "toponym_evidence_pack.json",
        ],
        "place_perception": [
            "place_perception_report.md",
            "place_perception_distribution.csv",
            "place_perception_by_toponym.csv",
            "place_perception_by_source.csv",
            "place_perception_evidence.json",
        ],
        "migration_narrative": [
            "migration_narrative_report.md",
            "migration_narrative_matrix.csv",
            "migration_narrative_evidence.json",
        ],
        "sampling": [
            "coding_sample_by_toponym.csv",
            "coding_sample.csv",
            "coding_codebook_toponym.md",
            "coding_codebook.md",
            "coding_manifest_toponym.json",
            "coding_manifest.json",
        ],
    }
    step = str(step_name or "").strip().lower()
    expected = files_by_step.get(step, [])
    if not expected:
        return []
    base = _artifact_from_path_value(output_dir)
    if base is not None and base["kind"] in {"report", "table", "evidence", "config"}:
        # output_dir can unexpectedly point to a file in hand-written manifests.
        return [base]
    root = Path(str(output_dir))
    if not root.is_absolute():
        root = (ROOT / root).resolve()
    if not root.exists() or not root.is_dir() or not _is_allowed_artifact_root(root):
        return []
    result: list[dict] = []
    for name in expected:
        artifact = _artifact_from_path_value(root / name)
        if artifact:
            result.append(artifact)
    return result


def _dedupe_artifacts(files: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for item in files:
        path = str(item.get("path") or "")
        if not path or path in seen:
            continue
        seen.add(path)
        result.append(item)
    return result


def _primary_report(manifest: dict, reports: list[dict]) -> dict | None:
    report_path = manifest.get("report_path")
    if report_path:
        normalized = str(report_path).replace("/", "\\")
        for report in reports:
            if report["path"].replace("/", "\\") == normalized:
                return report
    return reports[0] if reports else None


def _primary_table(exp_id: str | None, tables: list[dict]) -> dict | None:
    if not tables:
        return None
    priority = {
        "toponym_research_workflow": ["toponym_frequency.csv", "top_10_toponyms.csv", "source_comparison.csv"],
        "research_story_e2e": ["research_story_e2e_steps.csv", "migration_narrative_matrix.csv", "coding_sample_by_toponym.csv", "coding_sample.csv"],
        "migration_narratives": ["migration_narrative_matrix.csv", "migration_driver_distribution.csv"],
        "place_perception": ["place_perception_distribution.csv", "place_perception_by_toponym.csv"],
        "sampling_coding": ["coding_sample_by_toponym.csv", "coding_sample.csv"],
    }.get(str(exp_id or ""), [])
    for preferred in priority:
        for table in tables:
            if table.get("name") == preferred:
                return table
    return tables[0]


def _primary_evidence(exp_id: str | None, evidence: list[dict]) -> dict | None:
    if not evidence:
        return None
    priority = {
        "toponym_research_workflow": ["toponym_evidence_pack.json"],
        "place_perception": ["place_perception_evidence.json"],
        "migration_narratives": ["migration_narrative_evidence.json"],
        "literature_bridge": ["literature_corpus_bridge.json"],
    }.get(str(exp_id or ""), [])
    for preferred in priority:
        for item in evidence:
            if item.get("name") == preferred:
                return item
    return evidence[0]


def _is_allowed_artifact_root(path: Path) -> bool:
    allowed = [(ROOT / "data").resolve(), (ROOT / "tmp_write_check").resolve()]
    return any(str(path).startswith(str(root)) for root in allowed)


def _agents_payload(experiments: list[dict]) -> list[dict]:
    return [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "runner": item.get("runner"),
            "contract": item.get("agent_contract"),
            "status": item.get("status", "unknown"),
            "expected_outputs": item.get("expected_outputs", []),
        }
        for item in experiments
    ]


def _methods_payload(config: dict) -> list[dict]:
    return [
        {
            "id": "language_detection",
            "title": "Language detection",
            "backend": config.get("language_detection", {}).get("backend", "rule-based"),
            "stage": "preprocessing",
            "inputs": ["clean_text"],
            "outputs": ["language"],
            "quality_gates": ["ru/en/uz/th/other labels only", "rule-based fallback available"],
            "experiments": ["corpus_context"],
            "limitations": "Short mixed-language comments remain hard to classify.",
        },
        {
            "id": "sentiment",
            "title": "Sentiment",
            "backend": config.get("sentiment", {}).get("backend", "rule-based"),
            "stage": "classification",
            "inputs": ["text"],
            "outputs": ["sentiment"],
            "quality_gates": ["stable baseline labels", "examples reviewed in reports"],
            "experiments": ["place_perception", "toponym_urban_space"],
            "limitations": "Rule-based sentiment is a baseline, not a final affect model.",
        },
        {
            "id": "topics",
            "title": "Topic modeling",
            "backend": config.get("topic_model", {}).get("backend", "kmeans"),
            "stage": "exploration",
            "inputs": ["embeddings", "text"],
            "outputs": ["topic_id", "topic_labels"],
            "quality_gates": ["topic labels require human review", "hash backend available for smoke tests"],
            "experiments": ["corpus_context", "toponym_urban_space"],
            "limitations": "Topic labels require human review.",
        },
        {
            "id": "toponyms",
            "title": "Toponym extraction",
            "backend": "dictionary",
            "stage": "place extraction",
            "inputs": ["text"],
            "outputs": ["toponyms", "city/district stats"],
            "quality_gates": ["dangerous aliases removed", "districts mapped to parent city"],
            "experiments": ["toponym_urban_space", "literature_bridge"],
            "limitations": "Dictionary extraction misses unseen aliases and ambiguous place names.",
        },
        {
            "id": "migration_drivers",
            "title": "Migration drivers",
            "backend": "rule-based taxonomy",
            "stage": "classification",
            "inputs": ["text"],
            "outputs": ["migration_driver"],
            "quality_gates": ["transparent taxonomy", "distribution exported"],
            "experiments": ["migration_narratives", "toponym_urban_space"],
            "limitations": "Transparent heuristic labels require validation.",
        },
        {
            "id": "place_perception",
            "title": "Place perception",
            "backend": "rule-based taxonomy",
            "stage": "interpretive support",
            "inputs": ["text", "toponyms"],
            "outputs": ["place_perception"],
            "quality_gates": ["examples exported", "no unsupported final claims"],
            "experiments": ["place_perception"],
            "limitations": "Designed for exploration and manual coding support.",
        },
    ]


def _safety_payload() -> dict:
    return {
        "execution_model": "registry-only experiments",
        "forbidden": [
            "arbitrary shell commands from UI",
            "web scraping",
            "paywall bypass",
            "LLM claims without evidence",
        ],
        "allowed_read_roots": ["data", "tmp_write_check", "queries"],
        "allowed_write_roots": ["data/web_runs", "tmp_write_check"],
        "review_gates": [
            "local artifacts only",
            "evidence paths preserved",
            "run manifests recorded",
            "report bundles marked for human review",
        ],
    }


def _experiment_by_id(experiment_id: str) -> dict:
    for item in _registry_payload():
        if item.get("id") == experiment_id and item.get("runner") in AGENT_RUNNERS:
            return item
    raise ValueError(f"Unknown registry experiment: {experiment_id}")


def _agent_file_info() -> list[dict]:
    roots = [ROOT / "data"]
    roots.extend(path for path in (ROOT / "tmp_write_check").glob("agent_*") if path.is_dir())
    suffixes = {".md", ".json", ".csv"}
    result = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in suffixes and ("agent_" in str(path) or "agent" in path.name):
                result.append({"path": str(path.relative_to(ROOT)), "name": path.name, "size": path.stat().st_size})
    return result[:200]


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _csv_info(directory: Path) -> list[dict]:
    return _file_info(directory, {".csv"})


def _file_info(directory: Path, suffixes: set[str]) -> list[dict]:
    if not directory.exists():
        return []
    result = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in suffixes:
            result.append({"path": str(path.relative_to(ROOT)), "name": path.name, "size": path.stat().st_size})
    return result


def _chart_from_csv(path: Path, label_column: str, value_column: str, limit: int | None = None) -> dict:
    if not path.exists():
        return {"labels": [], "values": []}
    frame = pd.read_csv(path)
    if label_column not in frame or value_column not in frame:
        return {"labels": [], "values": []}
    if limit:
        frame = frame.head(limit)
    return {"labels": frame[label_column].astype(str).tolist(), "values": frame[value_column].fillna(0).astype(float).tolist()}


def _value_counts(path: Path, column: str) -> dict:
    if not path.exists():
        return {"labels": [], "values": []}
    frame = pd.read_csv(path)
    if column not in frame:
        return {"labels": [], "values": []}
    counts = frame[column].fillna("unknown").astype(str).value_counts()
    return {"labels": counts.index.tolist(), "values": counts.astype(float).tolist()}


def _safe_data_path(path_value: str) -> Path | None:
    try:
        path = (ROOT / path_value).resolve()
    except OSError:
        return None
    allowed = [(ROOT / "data").resolve(), (ROOT / "DS").resolve(), (ROOT / "queries").resolve(), (ROOT / "tmp_write_check").resolve()]
    if any(str(path).startswith(str(root)) for root in allowed):
        return path
    return None


def _safe_int(value: object, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def _safe_report_path(path_value: str) -> Path | None:
    try:
        path = (ROOT / path_value).resolve()
    except OSError:
        return None
    allowed = [
        (ROOT / "data").resolve(),
        (ROOT / "tmp_write_check").resolve(),
        (ROOT / "docs").resolve(),
        (ROOT / "queries").resolve(),
        (ROOT / "experiments").resolve(),
    ]
    if any(str(path).startswith(str(root)) for root in allowed):
        return path
    return None


def _safe_artifact_path(path_value: str) -> Path | None:
    try:
        path = (ROOT / path_value).resolve()
    except OSError:
        return None
    allowed = [
        (ROOT / "data").resolve(),
        (ROOT / "tmp_write_check").resolve(),
        (ROOT / "docs").resolve(),
        (ROOT / "queries").resolve(),
        (ROOT / "experiments").resolve(),
    ]
    if any(str(path).startswith(str(root)) for root in allowed):
        return path
    return None


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), WebHandler)
    print(f"Web UI: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
