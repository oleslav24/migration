from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

from .models import ArticleCandidate, DownloadResult, discovery_config


def download_pdf(candidate: ArticleCandidate, config) -> DownloadResult:
    cfg = discovery_config(config)
    if not candidate.pdf_url:
        return DownloadResult(candidate.candidate_id, False, reason="no pdf_url")
    if cfg["download"].get("only_open_access", True) and not candidate.open_access:
        return DownloadResult(candidate.candidate_id, False, reason="not marked open access")
    if cfg["download"].get("respect_robots_txt", True) and not _robots_allowed(candidate.pdf_url, cfg["user_agent"]):
        return DownloadResult(candidate.candidate_id, False, reason="blocked by robots.txt")

    request = urllib.request.Request(candidate.pdf_url, headers={"User-Agent": cfg["user_agent"], "Accept": "application/pdf"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            allowed = {value.lower() for value in cfg["download"].get("allowed_mime_types", ["application/pdf"])}
            if content_type and content_type not in allowed:
                return DownloadResult(candidate.candidate_id, False, reason=f"unexpected content-type: {content_type}")
            data = response.read()
    except Exception as exc:
        return DownloadResult(candidate.candidate_id, False, reason=f"download failed: {exc}")

    if not data.startswith(b"%PDF"):
        return DownloadResult(candidate.candidate_id, False, reason="response is not a PDF")

    articles_dir = Path(cfg["articles_dir"])
    metadata_dir = Path(cfg["metadata_dir"])
    articles_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    stem = _file_stem(candidate)
    pdf_path = articles_dir / f"{stem}.pdf"
    metadata_path = metadata_dir / f"{stem}.json"
    pdf_path.write_bytes(data)
    metadata_path.write_text(json.dumps(candidate.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return DownloadResult(candidate.candidate_id, True, str(pdf_path), str(metadata_path), reason="downloaded")


def _robots_allowed(url: str, user_agent: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    try:
        parser.set_url(robots_url)
        parser.read()
        return parser.can_fetch(user_agent, url)
    except Exception:
        return True


def _file_stem(candidate: ArticleCandidate) -> str:
    year = candidate.year or "unknown"
    key = candidate.doi or candidate.candidate_id
    safe_title = re.sub(r"[^A-Za-z0-9А-Яа-я._-]+", "_", candidate.title.lower()).strip("_")[:80]
    safe_key = re.sub(r"[^A-Za-z0-9._-]+", "_", key.lower()).strip("_")
    return f"{year}_{safe_title}_{safe_key}"
