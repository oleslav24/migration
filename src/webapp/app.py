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
            self._json(table_payload(params.get("path", [""])[0]))
        elif parsed.path == "/api/runs":
            self._json({"runs": sorted(RUNS.values(), key=lambda item: item["created_at"], reverse=True)})
        elif parsed.path == "/api/run-log":
            params = parse_qs(parsed.query)
            self._text(read_run_log(params.get("id", [""])[0]))
        else:
            super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        preset = payload.get("preset")
        if preset not in PRESET_COMMANDS:
            self.send_error(400, "Unknown preset")
            return
        try:
            self._json(start_run(preset), status=202)
        except Exception as exc:
            self._json({"error": str(exc)}, status=500)

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
        "charts": charts,
        "presets": PRESET_COMMANDS,
    }


def table_payload(path_value: str) -> dict:
    path = _safe_data_path(path_value)
    if path is None or not path.exists() or path.suffix.lower() != ".csv":
        return {"columns": [], "rows": [], "error": "CSV not found or path is not allowed"}
    frame = pd.read_csv(path).head(100).fillna("")
    return {"columns": frame.columns.tolist(), "rows": frame.astype(str).to_dict(orient="records"), "path": str(path.relative_to(ROOT))}


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
    allowed = [(ROOT / "data").resolve(), (ROOT / "queries").resolve()]
    if any(str(path).startswith(str(root)) for root in allowed):
        return path
    return None


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), WebHandler)
    print(f"Web UI: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
