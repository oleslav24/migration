from __future__ import annotations

import hashlib
import re
import unicodedata

import pandas as pd

try:
    from ftfy import fix_text as ftfy_fix_text
except ImportError:  # pragma: no cover - exercised only without optional deps
    ftfy_fix_text = None


MOJIBAKE_MARKERS = ("Ð", "Ñ", "Â", "Ã", "ðŸ", "�")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")


def fix_encoding(text: str) -> str:
    """Repair common UTF-8-as-cp1251 mojibake while keeping normal text intact."""
    if text is None:
        return ""
    raw_value = str(text)
    value = raw_value
    needs_repair = any(marker in raw_value for marker in MOJIBAKE_MARKERS) or _looks_like_cyrillic_mojibake(raw_value)

    if needs_repair:
        candidates = {raw_value}
        frontier = [raw_value]
        # Two passes are enough for the most common double-encoded mojibake.
        for _ in range(2):
            next_frontier: list[str] = []
            for current in frontier:
                for encoding in ("cp1251", "latin1", "cp1252"):
                    try:
                        repaired = current.encode(encoding, errors="strict").decode("utf-8")
                    except UnicodeError:
                        continue
                    if repaired not in candidates:
                        candidates.add(repaired)
                        next_frontier.append(repaired)
                if "'" in current:
                    try:
                        repaired = current.replace("'", "’").encode("cp1252", errors="strict").decode("utf-8")
                    except UnicodeError:
                        repaired = ""
                    if repaired:
                        if repaired not in candidates:
                            candidates.add(repaired)
                            next_frontier.append(repaired)
            if not next_frontier:
                break
            frontier = next_frontier
        value = min(candidates, key=_mojibake_score)
    if ftfy_fix_text is not None:
        value = ftfy_fix_text(value)
    return value


def _looks_like_cyrillic_mojibake(text: str) -> bool:
    # Typical broken UTF-8->cp1251 strings: many "Р"/"С" plus punctuation-like artifacts.
    if text.count("Р") + text.count("С") < 2:
        return False
    artifacts = ("’", "'", "·", "°", "ё", "џ")
    return any(token in text for token in artifacts)


def _mojibake_score(text: str) -> int:
    marker_penalty = sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
    replacement_penalty = text.count("�") * 3
    latin_noise_penalty = text.count("Â") + text.count("Ã")
    return marker_penalty + replacement_penalty + latin_noise_penalty


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
