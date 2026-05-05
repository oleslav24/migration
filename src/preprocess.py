from __future__ import annotations

import hashlib
import re
import unicodedata

import pandas as pd

try:
    from ftfy import fix_text as ftfy_fix_text
except ImportError:  # pragma: no cover - exercised only without optional deps
    ftfy_fix_text = None


MOJIBAKE_MARKERS = ("Р", "С", "Ñ", "Ð", "рџ")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")


def fix_encoding(text: str) -> str:
    """Repair common UTF-8-as-cp1251 mojibake while keeping normal text intact."""
    if text is None:
        return ""
    value = str(text)
    if ftfy_fix_text is not None:
        value = ftfy_fix_text(value)

    if any(marker in value for marker in MOJIBAKE_MARKERS):
        candidates = [value]
        for encoding in ("cp1251", "latin1"):
            try:
                candidates.append(value.encode(encoding, errors="strict").decode("utf-8"))
            except UnicodeError:
                continue
        value = min(candidates, key=_mojibake_score)
    return value


def _mojibake_score(text: str) -> int:
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)


def clean_text(text: str) -> str:
    """Normalize text and remove transport noise without stripping language signals."""
    if text is None:
        return ""
    value = unicodedata.normalize("NFKC", str(text))
    value = CONTROL_RE.sub(" ", value)
    value = URL_RE.sub(" ", value)
    value = SPACE_RE.sub(" ", value).strip()
    return value


def parse_datetime(series: pd.Series) -> pd.Series:
    normalized = (
        series.astype("string")
        .str.replace(r"\s+UTC([+-]\d{2}):?(\d{2})$", r" \1\2", regex=True)
    )
    parsed = pd.to_datetime(normalized, format="%d.%m.%Y %H:%M:%S %z", errors="coerce", utc=True)
    missing = parsed.isna()
    if missing.any():
        parsed.loc[missing] = pd.to_datetime(normalized[missing], errors="coerce", utc=True)
    return parsed


def anonymize_author(author: object, salt: str) -> str:
    raw = "" if pd.isna(author) else str(author)
    return hashlib.sha256(f"{salt}{raw}".encode("utf-8")).hexdigest()


def preprocess_chunk(
    chunk: pd.DataFrame,
    min_text_length: int,
    anonymization_salt: str,
) -> pd.DataFrame:
    df = chunk.dropna(subset=["comment"]).copy()
    if "source" not in df:
        df["source"] = "unknown"
    df["source"] = df["source"].map(fix_encoding).map(clean_text)
    df["group"] = df["group"].map(fix_encoding).map(clean_text)
    df["clean_text"] = df["comment"].map(fix_encoding).map(clean_text)
    df["datetime"] = parse_datetime(df["datetime"])
    df = df.dropna(subset=["datetime", "clean_text", "group"])
    df = df[df["clean_text"].str.len() >= min_text_length]
    df["author_hash"] = df["author"].map(lambda value: anonymize_author(value, anonymization_salt))
    df["date"] = df["datetime"].dt.date.astype("string")
    df["year"] = df["datetime"].dt.year.astype("Int64")
    df["month"] = df["datetime"].dt.tz_convert(None).dt.to_period("M").astype("string")
    df["period"] = df["month"]
    return df[
        [
            "datetime",
            "date",
            "year",
            "month",
            "period",
            "author_hash",
            "source",
            "group",
            "clean_text",
        ]
    ].reset_index(drop=True)
