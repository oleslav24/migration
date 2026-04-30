from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd


THAILAND_TOPONYMS: dict[str, tuple[str, ...]] = {
    "Thailand": ("thailand", "таиланд", "тайланд"),
    "Bangkok": ("bangkok", "bkk", "банкок", "бангкок"),
    "Phuket": ("phuket", "пхукет"),
    "Pattaya": ("pattaya", "паттайя"),
    "Chiang Mai": ("chiang mai", "чианг май", "чиангмай"),
    "Chiang Rai": ("chiang rai", "чианг рай"),
    "Samui": ("samui", "koh samui", "ko samui", "самуи", "ко самуи"),
    "Krabi": ("krabi", "краби"),
    "Hua Hin": ("hua hin", "хуахин", "хуа хин"),
    "Koh Phangan": ("koh phangan", "ko phangan", "phangan", "панган", "ко панган"),
    "Koh Tao": ("koh tao", "ko tao", "ко тао"),
    "Koh Chang": ("koh chang", "ko chang", "ко чанг"),
    "Koh Lanta": ("koh lanta", "ko lanta", "ко ланта"),
    "Ayutthaya": ("ayutthaya", "аютая", "аюттхая"),
    "Sukhothai": ("sukhothai", "сукхотай"),
    "Isan": ("isan", "isaan", "исан"),
    "Udon Thani": ("udon thani", "удон тхани"),
    "Nakhon Ratchasima": ("nakhon ratchasima", "korat", "корат"),
    "Surat Thani": ("surat thani", "сурат тхани"),
    "Trang": ("trang", "транг"),
    "Hat Yai": ("hat yai", "хадьяй", "хат яй"),
    "Rayong": ("rayong", "районг"),
    "Chonburi": ("chonburi", "чонбури"),
    "Nonthaburi": ("nonthaburi", "нонтхабури"),
    "Samut Prakan": ("samut prakan", "самут пракан"),
    # Bangkok districts and common expat areas.
    "Sukhumvit": ("sukhumvit", "сукхумвит"),
    "Asok": ("asok", "asoke", "асок"),
    "Thong Lo": ("thong lo", "thonglor", "тонг ло", "тонгло"),
    "Ekkamai": ("ekkamai", "эккамай"),
    "Phrom Phong": ("phrom phong", "prom phong", "пхром пхонг"),
    "Silom": ("silom", "силом"),
    "Sathorn": ("sathorn", "sathon", "сатхорн"),
    "Ari": ("ari", "ари"),
    "On Nut": ("on nut", "он нут"),
    "Ratchada": ("ratchada", "ratchadaphisek", "ратчада"),
    "Lat Phrao": ("lat phrao", "ladprao", "лат пхрао"),
    "Chatuchak": ("chatuchak", "чатучак"),
    "Bang Na": ("bang na", "банг на"),
    "Khao San": ("khao san", "каосан", "кхаосан"),
    # Phuket areas.
    "Patong": ("patong", "патонг"),
    "Kata": ("kata", "ката"),
    "Karon": ("karon", "карон"),
    "Rawai": ("rawai", "раваи"),
    "Nai Harn": ("nai harn", "най харн", "наи харн"),
    "Chalong": ("chalong", "чалонг"),
    "Kamala": ("kamala", "камала"),
    "Bang Tao": ("bang tao", "банг тао"),
    "Surin Beach": ("surin beach", "surin", "сурин"),
    "Mai Khao": ("mai khao", "май као"),
    "Phuket Town": ("phuket town", "пхукет таун"),
    # Chiang Mai zones.
    "Nimman": ("nimman", "nimmanhaemin", "нимман"),
    "Old City Chiang Mai": ("old city chiang mai", "old city", "старый город чианг май"),
    "Santitham": ("santitham", "сантихам"),
    "Hang Dong": ("hang dong", "ханг донг"),
    "Mae Rim": ("mae rim", "мае рим"),
    "Mae Hia": ("mae hia", "мае хиа"),
    "Doi Suthep": ("doi suthep", "дой сутхеп"),
    # Pattaya areas.
    "Jomtien": ("jomtien", "джомтьен"),
    "Pratumnak": ("pratumnak", "pratamnak", "пратамнак"),
    "Naklua": ("naklua", "наклуа"),
    "Wongamat": ("wongamat", "вонгамат"),
    "Central Pattaya": ("central pattaya", "центр паттайи"),
    "South Pattaya": ("south pattaya", "южная паттайя"),
    "North Pattaya": ("north pattaya", "северная паттайя"),
}

TOPONYM_META: dict[str, dict[str, str | None]] = {
    "Thailand": {"type": "country", "parent_city": None},
    "Bangkok": {"type": "city", "parent_city": "Bangkok"},
    "Phuket": {"type": "city", "parent_city": "Phuket"},
    "Pattaya": {"type": "city", "parent_city": "Pattaya"},
    "Chiang Mai": {"type": "city", "parent_city": "Chiang Mai"},
    "Chiang Rai": {"type": "city", "parent_city": "Chiang Rai"},
    "Samui": {"type": "city", "parent_city": "Samui"},
    "Krabi": {"type": "city", "parent_city": "Krabi"},
    "Hua Hin": {"type": "city", "parent_city": "Hua Hin"},
    "Koh Phangan": {"type": "city", "parent_city": "Koh Phangan"},
    "Koh Tao": {"type": "city", "parent_city": "Koh Tao"},
    "Koh Chang": {"type": "city", "parent_city": "Koh Chang"},
    "Koh Lanta": {"type": "city", "parent_city": "Koh Lanta"},
    "Ayutthaya": {"type": "city", "parent_city": "Ayutthaya"},
    "Sukhothai": {"type": "city", "parent_city": "Sukhothai"},
    "Isan": {"type": "region", "parent_city": None},
    "Udon Thani": {"type": "city", "parent_city": "Udon Thani"},
    "Nakhon Ratchasima": {"type": "city", "parent_city": "Nakhon Ratchasima"},
    "Surat Thani": {"type": "city", "parent_city": "Surat Thani"},
    "Trang": {"type": "city", "parent_city": "Trang"},
    "Hat Yai": {"type": "city", "parent_city": "Hat Yai"},
    "Rayong": {"type": "city", "parent_city": "Rayong"},
    "Chonburi": {"type": "city", "parent_city": "Chonburi"},
    "Nonthaburi": {"type": "city", "parent_city": "Nonthaburi"},
    "Samut Prakan": {"type": "city", "parent_city": "Samut Prakan"},
}

for _district in (
    "Sukhumvit",
    "Asok",
    "Thong Lo",
    "Ekkamai",
    "Phrom Phong",
    "Silom",
    "Sathorn",
    "Ari",
    "On Nut",
    "Ratchada",
    "Lat Phrao",
    "Chatuchak",
    "Bang Na",
    "Khao San",
):
    TOPONYM_META[_district] = {"type": "district", "parent_city": "Bangkok"}

for _area in (
    "Patong",
    "Kata",
    "Karon",
    "Rawai",
    "Nai Harn",
    "Chalong",
    "Kamala",
    "Bang Tao",
    "Surin Beach",
    "Mai Khao",
    "Phuket Town",
):
    TOPONYM_META[_area] = {"type": "district", "parent_city": "Phuket"}

for _zone in (
    "Nimman",
    "Old City Chiang Mai",
    "Santitham",
    "Hang Dong",
    "Mae Rim",
    "Mae Hia",
    "Doi Suthep",
):
    TOPONYM_META[_zone] = {"type": "district", "parent_city": "Chiang Mai"}

for _area in (
    "Jomtien",
    "Pratumnak",
    "Naklua",
    "Wongamat",
    "Central Pattaya",
    "South Pattaya",
    "North Pattaya",
):
    TOPONYM_META[_area] = {"type": "district", "parent_city": "Pattaya"}


def _normalize_text(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


_PATTERNS = {
    name: tuple(re.compile(rf"(?<!\w){re.escape(_normalize_text(alias))}(?!\w)") for alias in aliases)
    for name, aliases in THAILAND_TOPONYMS.items()
}


def extract_toponyms(text: str) -> list[str]:
    value = _normalize_text(text)
    return [name for name, patterns in _PATTERNS.items() if any(pattern.search(value) for pattern in patterns)]


def add_toponyms_column(df: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    result = df.copy()
    if text_column not in result:
        result["toponyms"] = [[] for _ in range(len(result))]
        return result
    result["toponyms"] = result[text_column].map(extract_toponyms)
    return result


def toponym_frequency(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty:
        return pd.DataFrame(columns=["toponym", "type", "parent_city", "count", "share"])
    counts = exploded["toponym"].value_counts().rename_axis("toponym").reset_index(name="count")
    counts["share"] = counts["count"] / counts["count"].sum()
    return _with_meta(counts).sort_values(["count", "toponym"], ascending=[False, True]).reset_index(drop=True)


def top_toponyms(df: pd.DataFrame, limit: int = 10) -> list[str]:
    return toponym_frequency(df).head(limit)["toponym"].tolist()


def top_10_toponyms(df: pd.DataFrame) -> pd.DataFrame:
    return toponym_frequency(df).head(10)


def city_level_stats(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty:
        return pd.DataFrame(columns=["parent_city", "count", "share"])
    city_rows = exploded.dropna(subset=["parent_city"])
    if city_rows.empty:
        return pd.DataFrame(columns=["parent_city", "count", "share"])
    counts = city_rows["parent_city"].value_counts().rename_axis("parent_city").reset_index(name="count")
    counts["share"] = counts["count"] / counts["count"].sum()
    return counts.sort_values(["count", "parent_city"], ascending=[False, True]).reset_index(drop=True)


def district_level_stats(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty:
        return pd.DataFrame(columns=["toponym", "parent_city", "count", "share"])
    districts = exploded[exploded["type"] == "district"]
    if districts.empty:
        return pd.DataFrame(columns=["toponym", "parent_city", "count", "share"])
    counts = districts.groupby(["toponym", "parent_city"]).size().reset_index(name="count")
    totals = counts.groupby("parent_city")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return counts.sort_values(["parent_city", "count"], ascending=[True, False]).reset_index(drop=True)


def topics_per_toponym(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty or "topic_id" not in exploded:
        return pd.DataFrame(columns=["toponym", "type", "parent_city", "topic_id", "count", "share"])
    counts = exploded.groupby(["toponym", "topic_id"]).size().reset_index(name="count")
    totals = counts.groupby("toponym")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return _with_meta(counts).sort_values(["toponym", "count"], ascending=[True, False]).reset_index(drop=True)


def sentiment_per_toponym(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty or "sentiment" not in exploded:
        return pd.DataFrame(columns=["toponym", "type", "parent_city", "sentiment", "count", "share"])
    counts = exploded.groupby(["toponym", "sentiment"]).size().reset_index(name="count")
    totals = counts.groupby("toponym")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return _with_meta(counts).sort_values(["toponym", "sentiment"]).reset_index(drop=True)


def random_samples_per_toponym(
    df: pd.DataFrame,
    top_n: int = 10,
    samples_per_toponym: int = 10,
    random_state: int = 42,
) -> pd.DataFrame:
    exploded = _explode_toponyms(df)
    if exploded.empty:
        return pd.DataFrame(columns=["toponym", "type", "parent_city", "doc_id", "topic_id", "sentiment", "text"])

    frames: list[pd.DataFrame] = []
    for toponym in top_toponyms(df, top_n):
        frame = exploded[exploded["toponym"] == toponym]
        sample_size = min(samples_per_toponym, len(frame))
        sampled = frame.sample(n=sample_size, random_state=random_state) if sample_size else frame
        columns = [
            column
            for column in ["toponym", "type", "parent_city", "doc_id", "topic_id", "sentiment", "text"]
            if column in sampled
        ]
        frames.append(sampled[columns])
    if not frames:
        return pd.DataFrame(columns=["toponym", "type", "parent_city", "doc_id", "topic_id", "sentiment", "text"])
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
    return _with_meta(result)


def _parse_toponyms(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if pd.isna(value):
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(";") if part.strip()]
    return []


def _with_meta(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["type"] = result["toponym"].map(lambda value: _meta_value(value, "type"))
    result["parent_city"] = result["toponym"].map(lambda value: _meta_value(value, "parent_city"))
    return result


def _meta_value(toponym: Any, key: str) -> str | None:
    return TOPONYM_META.get(str(toponym), {}).get(key)


def _safe_filename(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip().lower())
    return normalized.strip("_") or "toponym"
