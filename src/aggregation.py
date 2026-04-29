from __future__ import annotations

import json

import pandas as pd


def aggregate_messages(df: pd.DataFrame, time_window: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "doc_id",
                "group",
                "window_start",
                "window_end",
                "period",
                "text",
                "message_count",
                "lang_distribution",
            ]
        )

    work = df.sort_values("datetime").copy()
    grouped = work.groupby(["group", pd.Grouper(key="datetime", freq=time_window)])
    docs = grouped.agg(
        text=("clean_text", lambda values: "\n".join(values.astype(str))),
        message_count=("clean_text", "size"),
        period=("period", "first"),
        lang_distribution=("lang", _lang_distribution),
    ).reset_index()
    docs = docs.rename(columns={"datetime": "window_start"})
    docs["window_end"] = docs["window_start"] + pd.to_timedelta(time_window)
    docs = docs[docs["message_count"] > 0].reset_index(drop=True)
    docs.insert(0, "doc_id", docs.index.map(lambda idx: f"doc_{idx:08d}"))
    return docs[
        [
            "doc_id",
            "group",
            "window_start",
            "window_end",
            "period",
            "text",
            "message_count",
            "lang_distribution",
        ]
    ]


def _lang_distribution(values: pd.Series) -> str:
    counts = values.value_counts(normalize=True).round(4).to_dict()
    return json.dumps(counts, ensure_ascii=False, sort_keys=True)

