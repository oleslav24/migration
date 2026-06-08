from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from .codebook import flatten_codes, load_codebook


INSTRUCTIONS_TEXT = """1. Прочитайте текст сообщения/фрагмента.
2. Определите основной миграционный драйвер, если он есть.
3. Определите тип сообщения: вопрос, совет, личный опыт, жалоба и т.д.
4. Если сообщение содержит описание места, укажите функцию места.
5. Оцените ручную тональность.
6. Если сообщение нерелевантно, отметьте usefulness = off_topic или low_information.
7. В memo кратко поясните сложные случаи.
8. uncertainty: 0 — уверенно, 1 — есть сомнения, 2 — сложно классифицировать.
"""


def create_annotation_template(
    sample: pd.DataFrame,
    schema_path: str,
    codebook_path: str,
    output_path: str,
    coder_id: str | None = None,
) -> None:
    schema = _load_schema(schema_path)
    template = _build_template(sample, schema, coder_id)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".xlsx":
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template.to_excel(writer, sheet_name="annotations", index=False)
            flatten_codes(load_codebook(codebook_path)).to_excel(writer, sheet_name="codebook", index=False)
            pd.DataFrame({"instructions": INSTRUCTIONS_TEXT.splitlines()}).to_excel(
                writer, sheet_name="instructions", index=False
            )
    else:
        template.to_csv(output, index=False, encoding="utf-8")


def _build_template(sample: pd.DataFrame, schema: dict, coder_id: str | None) -> pd.DataFrame:
    rows = sample.copy()
    rows["annotation_id"] = [f"ann_{index:08d}" for index in range(len(rows))]
    if "toponyms" not in rows:
        rows["toponyms"] = ""
    for field in _schema_fields(schema):
        name = field["name"]
        if name not in rows.columns:
            rows[name] = ""
    if coder_id:
        rows["coder_id"] = coder_id
    ordered = [field["name"] for field in _schema_fields(schema)]
    return rows[ordered]


def _load_schema(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        schema = yaml.safe_load(handle) or {}
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a YAML mapping.")
    if "fields" not in schema or not isinstance(schema["fields"], list):
        raise ValueError("Schema must contain a list under 'fields'.")
    return schema


def _schema_fields(schema: dict) -> list[dict]:
    fields = [item for item in schema.get("fields", []) if isinstance(item, dict) and item.get("name")]
    return fields

