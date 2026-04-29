from __future__ import annotations

import re
from typing import Literal


Language = Literal["ru", "en", "other"]
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
LATIN_RE = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> Language:
    value = "" if text is None else str(text)
    cyrillic = len(CYRILLIC_RE.findall(value))
    latin = len(LATIN_RE.findall(value))
    if cyrillic == 0 and latin == 0:
        return "other"
    if cyrillic >= latin:
        return "ru"
    return "en"


def add_language_column(df):
    result = df.copy()
    result["lang"] = result["clean_text"].map(detect_language)
    return result

