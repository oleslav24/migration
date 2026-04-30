from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

import pandas as pd


THAILAND_TOPONYMS: dict[str, tuple[str, ...]] = {
    "Thailand": ("thailand", "тайланд", "таиланд", "королевство таиланд", "ประเทศไทย"),
    "Bangkok": ("bangkok", "bkk", "банкок", "бангкок", "กรุงเทพ", "กรุงเทพฯ"),
    "Phuket": ("phuket", "пхукет", "ภูเก็ต"),
    "Pattaya": ("pattaya", "паттайя", "พัทยา"),
    "Chiang Mai": ("chiang mai", "чианг май", "чиангмай", "เชียงใหม่"),
    "Chiang Rai": ("chiang rai", "чианг рай", "เชียงราย"),
    "Samui": ("samui", "koh samui", "ko samui", "самуи", "ко самуи", "เกาะสมุย"),
    "Krabi": ("krabi", "краби", "กระบี่"),
    "Hua Hin": ("hua hin", "хуахин", "хуа хин", "หัวหิน"),
    "Koh Phangan": ("koh phangan", "ko phangan", "phangan", "панган", "ко панган", "เกาะพะงัน"),
    "Koh Tao": ("koh tao", "ko tao", "tao", "ко тао", "เกาะเต่า"),
    "Koh Chang": ("koh chang", "ko chang", "chang", "ко чанг", "เกาะช้าง"),
    "Koh Lanta": ("koh lanta", "ko lanta", "lanta", "ланта", "เกาะลันตา"),
    "Ayutthaya": ("ayutthaya", "аютая", "аюттхая", "อยุธยา"),
    "Sukhothai": ("sukhothai", "сукхотай", "สุโขทัย"),
    "Isan": ("isan", "isaan", "исан", "อีสาน"),
    "Udon Thani": ("udon thani", "удон тхани", "อุดรธานี"),
    "Nakhon Ratchasima": ("nakhon ratchasima", "korat", "корат", "นครราชสีมา"),
    "Surat Thani": ("surat thani", "сурат тхани", "สุราษฎร์ธานี"),
    "Trang": ("trang", "транг", "ตรัง"),
    "Hat Yai": ("hat yai", "хадьяй", "хат яй", "หาดใหญ่"),
    "Rayong": ("rayong", "районг", "ระยอง"),
    "Chonburi": ("chonburi", "чонбури", "ชลบุรี"),
    "Nonthaburi": ("nonthaburi", "нонтхабури", "นนทบุรี"),
    "Samut Prakan": ("samut prakan", "самут пракан", "สมุทรปราการ"),
}

_PATTERNS = {
    name: tuple(re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", re.IGNORECASE) for alias in aliases)
    for name, aliases in THAILAND_TOPONYMS.items()
}


def extract_toponyms(text: str) -> list[str]:
    value = "" if text is None else str(text)
    found = [name for name, patterns in _PATTERNS.items() if any(pattern.search(value) for pattern in patterns)]
    return found


def add_toponyms_column(df: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    result = df.copy()
    if text_column not in result:
        result["toponyms"] = pd.Series(dtype="string")
        return result
    result["toponyms"] = result[text_column].map(lambda value: json.dumps(extract_toponyms(value), ensure_ascii=False))
    return result


def toponym_frequency(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty:
        return pd.DataFrame(columns=["toponym", "count", "share"])
    counts = exploded["toponym"].value_counts().rename_axis("toponym").reset_index(name="count")
    counts["share"] = counts["count"] / counts["count"].sum()
    return counts.sort_values(["count", "toponym"], ascending=[False, True]).reset_index(drop=True)


def top_toponyms(df: pd.DataFrame, limit: int = 10) -> list[str]:
    return toponym_frequency(df).head(limit)["toponym"].tolist()


def top_10_toponyms(df: pd.DataFrame) -> pd.DataFrame:
    return toponym_frequency(df).head(10)


def topics_per_toponym(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty or "topic_id" not in exploded:
        return pd.DataFrame(columns=["toponym", "topic_id", "count", "share"])
    counts = exploded.groupby(["toponym", "topic_id"]).size().reset_index(name="count")
    totals = counts.groupby("toponym")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return counts.sort_values(["toponym", "count"], ascending=[True, False]).reset_index(drop=True)


def sentiment_per_toponym(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty or "sentiment" not in exploded:
        return pd.DataFrame(columns=["toponym", "sentiment", "count", "share"])
    counts = exploded.groupby(["toponym", "sentiment"]).size().reset_index(name="count")
    totals = counts.groupby("toponym")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return counts.sort_values(["toponym", "sentiment"]).reset_index(drop=True)


def random_samples_per_toponym(
    df: pd.DataFrame,
    top_n: int = 10,
    samples_per_toponym: int = 10,
    random_state: int = 42,
) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty:
        return pd.DataFrame(columns=["toponym", "doc_id", "topic_id", "sentiment", "text"])

    frames: list[pd.DataFrame] = []
    for toponym in top_toponyms(df, top_n):
        frame = exploded[exploded["toponym"] == toponym]
        sample_size = min(samples_per_toponym, len(frame))
        sampled = frame.sample(n=sample_size, random_state=random_state) if sample_size else frame
        columns = [column for column in ["toponym", "doc_id", "topic_id", "sentiment", "text"] if column in sampled]
        frames.append(sampled[columns])
    if not frames:
        return pd.DataFrame(columns=["toponym", "doc_id", "topic_id", "sentiment", "text"])
    return pd.concat(frames, ignore_index=True)


def export_texts_by_toponym(
    df: pd.DataFrame,
    output_dir: Path,
    top_n: int = 10,
    samples_per_toponym: int = 50,
    random_state: int = 42,
) -> None:
    target = output_dir / "texts_by_toponym"
    target.mkdir(parents=True, exist_ok=True)
    samples = random_samples_per_toponym(df, top_n, samples_per_toponym, random_state)
    for toponym, frame in samples.groupby("toponym"):
        safe_name = _safe_filename(str(toponym))
        frame.to_csv(target / f"{safe_name}.csv", index=False, encoding="utf-8")


def _explode_toponyms(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "toponyms" not in df:
        return pd.DataFrame()
    result = df.copy()
    result["toponym"] = result["toponyms"].map(_parse_toponyms)
    result = result.explode("toponym")
    result = result.dropna(subset=["toponym"])
    result = result[result["toponym"].astype(str).str.len() > 0]
    return result


def _parse_toponyms(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if pd.isna(value):
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return [part.strip() for part in value.split(";") if part.strip()]
    return []


def _safe_filename(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip().lower())
    return normalized.strip("_") or "toponym"
