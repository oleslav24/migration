from __future__ import annotations

from pathlib import Path

import yaml


def load_discovery_queries(path: str | Path) -> list[dict]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return payload.get("queries", [])
