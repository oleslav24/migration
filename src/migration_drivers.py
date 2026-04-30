from __future__ import annotations

import re
from collections.abc import Iterable

import pandas as pd


DRIVER_CATEGORIES = [
    "visa/legal",
    "work/income",
    "climate/lifestyle",
    "family/relationships",
    "housing/location",
    "safety/politics",
    "adaptation/problems",
    "tourism/temporary stay",
]

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "visa/legal": (
        "visa",
        "виза",
        "визу",
        "permit",
        "residence",
        "legal",
        "law",
        "document",
        "documents",
        "паспорт",
        "документ",
        "immigration",
        "border",
        "граница",
    ),
    "work/income": (
        "work",
        "job",
        "income",
        "salary",
        "remote",
        "работа",
        "зарплата",
        "доход",
        "налог",
        "tax",
        "business",
        "freelance",
    ),
    "climate/lifestyle": (
        "climate",
        "weather",
        "sea",
        "lifestyle",
        "warm",
        "климат",
        "погода",
        "море",
        "тепло",
        "жизнь",
    ),
    "family/relationships": (
        "family",
        "children",
        "school",
        "wife",
        "husband",
        "relationship",
        "семья",
        "дети",
        "школа",
        "жена",
        "муж",
        "родители",
    ),
    "housing/location": (
        "rent",
        "apartment",
        "condo",
        "housing",
        "location",
        "area",
        "аренда",
        "квартира",
        "дом",
        "район",
        "жилье",
        "локация",
    ),
    "safety/politics": (
        "safe",
        "safety",
        "politics",
        "war",
        "mobilization",
        "sanction",
        "безопасно",
        "безопасность",
        "политика",
        "война",
        "мобилизация",
        "санкции",
    ),
    "adaptation/problems": (
        "problem",
        "issue",
        "hard",
        "difficult",
        "adapt",
        "language barrier",
        "проблема",
        "сложно",
        "трудно",
        "адаптация",
        "барьер",
        "ошибка",
    ),
    "tourism/temporary stay": (
        "tourist",
        "tourism",
        "temporary",
        "vacation",
        "holiday",
        "trip",
        "турист",
        "туризм",
        "временно",
        "отпуск",
        "поездка",
        "зимовка",
    ),
}

_PATTERNS = {
    category: tuple(re.compile(rf"(?<!\w){re.escape(keyword)}(?!\w)", re.IGNORECASE) for keyword in keywords)
    for category, keywords in _KEYWORDS.items()
}


def classify_migration_driver(text: str) -> str:
    value = "" if text is None else str(text)
    scores = {
        category: sum(1 for pattern in patterns if pattern.search(value))
        for category, patterns in _PATTERNS.items()
    }
    best_category = max(DRIVER_CATEGORIES, key=lambda category: scores[category])
    if scores[best_category] == 0:
        return "adaptation/problems"
    return best_category


def add_migration_driver_column(df: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    result = df.copy()
    if text_column not in result:
        result["migration_driver"] = pd.Series(dtype="string")
        return result
    result["migration_driver"] = result[text_column].map(classify_migration_driver)
    return result


def migration_driver_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "migration_driver" not in df:
        return pd.DataFrame(columns=["migration_driver", "count", "share"])
    counts = (
        df["migration_driver"]
        .value_counts()
        .reindex(DRIVER_CATEGORIES, fill_value=0)
        .rename_axis("migration_driver")
        .reset_index(name="count")
    )
    total = counts["count"].sum()
    counts["share"] = counts["count"] / total if total else 0.0
    return counts


def driver_temporal_dynamics(df: pd.DataFrame) -> pd.DataFrame:
    return _driver_breakdown(df, ["period"], ["period", "migration_driver", "count", "share"])


def driver_by_group(df: pd.DataFrame) -> pd.DataFrame:
    return _driver_breakdown(df, ["group"], ["group", "migration_driver", "count", "share"])


def _driver_breakdown(df: pd.DataFrame, keys: Iterable[str], columns: list[str]) -> pd.DataFrame:
    key_list = list(keys)
    if df.empty or "migration_driver" not in df or any(key not in df for key in key_list):
        return pd.DataFrame(columns=columns)
    counts = df.groupby([*key_list, "migration_driver"]).size().reset_index(name="count")
    totals = counts.groupby(key_list)["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return counts.sort_values([*key_list, "migration_driver"]).reset_index(drop=True)
