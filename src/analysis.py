from __future__ import annotations

import pandas as pd

from .migration_drivers import (
    driver_by_group,
    driver_temporal_dynamics,
    migration_driver_distribution,
)


def compute_analysis(enriched_docs: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "topic_distribution": topic_distribution(enriched_docs),
        "temporal_dynamics": temporal_dynamics(enriched_docs),
        "group_comparison": group_comparison(enriched_docs),
        "migration_driver_distribution": migration_driver_distribution(enriched_docs),
        "driver_temporal_dynamics": driver_temporal_dynamics(enriched_docs),
        "driver_by_group": driver_by_group(enriched_docs),
    }


def topic_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["topic_id", "count", "share"])
    counts = df["topic_id"].value_counts().sort_index().rename_axis("topic_id").reset_index(name="count")
    counts["share"] = counts["count"] / counts["count"].sum()
    return counts


def temporal_dynamics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["period", "topic_id", "count", "share"])
    counts = df.groupby(["period", "topic_id"]).size().reset_index(name="count")
    totals = counts.groupby("period")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return counts.sort_values(["period", "topic_id"]).reset_index(drop=True)


def group_comparison(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["group", "topic_id", "count", "share"])
    counts = df.groupby(["group", "topic_id"]).size().reset_index(name="count")
    totals = counts.groupby("group")["count"].transform("sum")
    counts["share"] = counts["count"] / totals
    return counts.sort_values(["group", "topic_id"]).reset_index(drop=True)
