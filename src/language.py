from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal


Language = Literal["ru", "en", "uz", "th", "other"]
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
THAI_RE = re.compile(r"[\u0E00-\u0E7F]")
UZ_HINT_RE = re.compile(
    r"\b(o['`]?zbekiston|uzbek|toshkent|samarqand|buxoro|andijon|namangan|"
    r"xorazm|qashqadaryo|surxondaryo|farg['`]?ona|ko['`]?ch|bo['`]?l|"
    r"yo['`]?q|ha|rahmat|ish|viza)\b",
    re.IGNORECASE,
)
TARGET_LANGUAGES = {"ru", "en", "uz", "th", "other"}


def detect_language(text: str, config: dict[str, Any] | None = None) -> Language:
    settings = config or {}
    backend = str(settings.get("backend", "rule-based")).lower()
    if backend in {"fasttext", "fasttext.py"}:
        detected = _detect_fasttext(text, settings.get("fasttext_model_path"))
        if detected is not None:
            return detected
    if backend == "langdetect":
        detected = _detect_langdetect(text)
        if detected is not None:
            return detected
    return detect_language_rule_based(text)


def detect_language_rule_based(text: str) -> Language:
    value = "" if text is None else str(text)
    thai = len(THAI_RE.findall(value))
    cyrillic = len(CYRILLIC_RE.findall(value))
    latin = len(LATIN_RE.findall(value))
    if thai > 0 and thai >= cyrillic and thai >= latin:
        return "th"
    if UZ_HINT_RE.search(value):
        return "uz"
    if cyrillic == 0 and latin == 0:
        return "other"
    if cyrillic >= latin:
        return "ru"
    return "en"


def _normalize_language(label: str | None) -> Language | None:
    if not label:
        return None
    value = label.lower().replace("__label__", "").split("_", 1)[0]
    if value in TARGET_LANGUAGES:
        return value  # type: ignore[return-value]
    return "other"


@lru_cache(maxsize=4)
def _load_fasttext_model(model_path: str | None):
    if not model_path:
        return None
    try:
        import fasttext
    except ImportError:
        return None
    path = Path(model_path)
    if not path.exists():
        return None
    return fasttext.load_model(str(path))


def _detect_fasttext(text: str, model_path: str | None) -> Language | None:
    model = _load_fasttext_model(model_path)
    if model is None:
        return None
    value = str(text or "").replace("\n", " ").strip()
    if not value:
        return "other"
    labels, _scores = model.predict(value, k=1)
    return _normalize_language(labels[0] if labels else None)


def _detect_langdetect(text: str) -> Language | None:
    value = str(text or "").strip()
    if not value:
        return "other"
    try:
        from langdetect import LangDetectException, detect
    except ImportError:
        return None
    try:
        return _normalize_language(detect(value))
    except LangDetectException:
        return "other"


def add_language_column(df, config: dict[str, Any] | None = None):
    result = df.copy()
    result["lang"] = result["clean_text"].map(lambda value: detect_language(value, config))
    return result
