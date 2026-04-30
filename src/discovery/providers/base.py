from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.discovery.models import ArticleCandidate, discovery_config


LOGGER = logging.getLogger(__name__)


class ArticleProvider:
    name: str

    def search(self, query: dict, config) -> list[ArticleCandidate]:
        raise NotImplementedError


def query_text(query: dict) -> str:
    return " ".join(part for part in [query.get("query_en", ""), query.get("query_ru", "")] if part).strip()


def fetch_json(url: str, config, provider: str) -> dict[str, Any]:
    cfg = discovery_config(config)
    request = urllib.request.Request(url, headers={"User-Agent": cfg["user_agent"], "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    time.sleep(float(cfg["polite_delay_seconds"]))
    return payload


def save_raw(payload: Any, config, provider: str, query_id: str) -> None:
    cfg = discovery_config(config)
    target = Path(cfg["output_dir"]) / "raw" / provider
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{query_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def api_url(base: str, params: dict[str, Any]) -> str:
    return f"{base}?{urllib.parse.urlencode(params, doseq=True)}"


def first(value) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0])
    if value:
        return str(value)
    return None


def clean_html(value: str | None) -> str | None:
    if not value:
        return None
    import re

    return re.sub(r"<[^>]+>", " ", value).replace("\n", " ").strip()
