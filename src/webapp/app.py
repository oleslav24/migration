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

AGENT_RUNNERS = {"analyze-corpus", "toponym-agent", "place-perception", "sampling-coding", "migration-narrative", "literature-bridge"}


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
    manifest_a = _load_manifest_summary(path_a)
    manifest_b = _load_manifest_summary(path_b)
    if manifest_a.get("error") or manifest_b.get("error"):
        return {"error": manifest_a.get("error") or manifest_b.get("error"), "differences": []}
    keys = sorted(set(manifest_a) | set(manifest_b))
    differences = [
        {"field": key, "a": manifest_a.get(key), "b": manifest_b.get(key)}
        for key in keys
        if manifest_a.get(key) != manifest_b.get(key)
    ]
    return {"a": manifest_a, "b": manifest_b, "differences": differences}


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
    data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
    experiment = data.get("experiment", {}) if isinstance(data, dict) else {}
    result = data.get("result", {}) if isinstance(data, dict) else {}
    return {
        "path": str(path.relative_to(ROOT)),
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
        reports = [item for item in files if item["kind"] == "report"]
        evidence = [item for item in files if item["kind"] == "evidence"]
        tables = [item for item in files if item["kind"] == "table"]
        configs = [item for item in files if item["kind"] == "config"]
        primary_report = _primary_report(manifest, reports)
        result.append({
            "id": exp_id,
            "title": experiment.get("title"),
            "runner": experiment.get("runner"),
            "status": "ready" if primary_report else "not_run",
            "hypothesis": (manifest.get("params") or {}).get("hypothesis", ""),
            "report_language": (manifest.get("params") or {}).get("report_language"),
            "manifest_path": manifest.get("path"),
            "last_run_at": manifest.get("manifest_mtime"),
            "output_dir": output_dir,
            "primary_report": primary_report,
            "reports": reports,
            "evidence": evidence,
            "tables": tables,
            "configs": configs,
            "counts": {"reports": len(reports), "evidence": len(evidence), "tables": len(tables)},
        })
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


def _primary_report(manifest: dict, reports: list[dict]) -> dict | None:
    report_path = manifest.get("report_path")
    if report_path:
        normalized = str(report_path).replace("/", "\\")
        for report in reports:
            if report["path"].replace("/", "\\") == normalized:
                return report
    return reports[0] if reports else None


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
