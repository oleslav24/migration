from __future__ import annotations

import json

import pandas as pd
from sklearn.metrics import cohen_kappa_score


def compute_pairwise_agreement(
    annotations_a: pd.DataFrame,
    annotations_b: pd.DataFrame,
    fields: list[str],
) -> dict:
    merged = annotations_a.merge(
        annotations_b,
        on="annotation_id",
        suffixes=("_a", "_b"),
        how="inner",
    )
    report: dict[str, dict] = {}
    for field in fields:
        left = merged.get(f"{field}_a")
        right = merged.get(f"{field}_b")
        if left is None or right is None:
            continue
        if _is_multi_field(left, right):
            report[field] = _multi_metrics(left, right)
        else:
            report[field] = _category_metrics(left, right)
    return report


def _is_multi_field(left: pd.Series, right: pd.Series) -> bool:
    return left.astype(str).str.contains(";|\\[", regex=True).any() or right.astype(str).str.contains(";|\\[", regex=True).any()


def _category_metrics(left: pd.Series, right: pd.Series) -> dict:
    a = left.fillna("").astype(str)
    b = right.fillna("").astype(str)
    n = len(a)
    agreement = float((a == b).mean()) if n else 0.0
    labels = sorted(set(a) | set(b))
    kappa = float(cohen_kappa_score(a, b, labels=labels)) if n else 0.0
    confusion = pd.crosstab(a, b, dropna=False)
    return {
        "n_items": int(n),
        "percent_agreement": agreement,
        "cohens_kappa": kappa,
        "confusion_matrix": confusion.to_dict(),
    }


def _multi_metrics(left: pd.Series, right: pd.Series) -> dict:
    a_sets = left.map(_to_set)
    b_sets = right.map(_to_set)
    n = len(a_sets)
    exact = float((a_sets == b_sets).mean()) if n else 0.0
    jaccard_values = []
    for a, b in zip(a_sets, b_sets):
        if not a and not b:
            jaccard_values.append(1.0)
            continue
        union = a | b
        jaccard_values.append(len(a & b) / len(union) if union else 0.0)
    return {
        "n_items": int(n),
        "exact_match_rate": exact,
        "jaccard_similarity": float(sum(jaccard_values) / len(jaccard_values)) if jaccard_values else 0.0,
    }


def _to_set(value: object) -> set[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return set()
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    text = str(value).strip()
    if not text:
        return set()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return {str(item).strip() for item in parsed if str(item).strip()}
        except Exception:
            pass
    return {item.strip() for item in text.split(";") if item.strip()}

