# Literature Guide / Гайд по literature

## EN

## Purpose

`src/literature` provides local retrieval and controlled summarization over files in `articles/` for migration research support.

Supported formats:

- `.pdf`
- `.docx`
- `.txt`
- `.md`

This module is retrieval-first: it returns traceable snippets and evidence-linked summaries.

## Build local index

```bash
python -m src.literature.cli build-index --config config.yaml
```

Expected index directory (from `config.yaml`, default `data/literature_index/`):

- `chunks.parquet` (or pickle fallback)
- `embeddings.npy`
- `metadata.json`
- `index.pkl` / `index.json` (backend metadata)

## Search

Single query:

```bash
python -m src.literature.cli search --config config.yaml --query "digital traces migration social media urban space"
```

Batch queries from YAML:

```bash
python -m src.literature.cli run-queries --config config.yaml --queries queries/literature_queries.yaml
```

Default search exports:

- `data/output/literature_search_results.csv`
- `data/output/literature_search_results.md`

Batch exports:

- `data/output/literature/<query_id>.csv`
- `data/output/literature/<query_id>.md`

## Summarization tasks

Single task:

```bash
python -m src.literature.cli summarize --config config.yaml --task digital_traces_and_migration_decisions
```

All tasks:

```bash
python -m src.literature.cli summarize-all --config config.yaml --tasks queries/summarization_tasks.yaml
```

Outputs:

- `data/output/literature_summaries/<task_id>.md`
- `data/output/literature_summaries/<task_id>.json`

Current default mode is extractive summarization (configurable in `config.yaml`):

- `literature.summarization.mode: extractive`

LLM mode is intentionally not used as default in this stage.

## Failure handling

- Missing index raises a clear error in search step.
- Empty retrieval results still produce partial/empty-safe summaries in batch mode.
- Corrupted or unreadable article files are skipped with warnings during indexing.

## RU

## Назначение

`src/literature` реализует локальный retrieval и контролируемый summarize по файлам из `articles/` для задач миграционного исследования.

Поддерживаемые форматы:

- `.pdf`
- `.docx`
- `.txt`
- `.md`

Модуль работает в логике retrieval-first: выдает трассируемые фрагменты и summary с явными ссылками на evidence.

## Построение локального индекса

```bash
python -m src.literature.cli build-index --config config.yaml
```

Ожидаемая директория индекса (из `config.yaml`, по умолчанию `data/literature_index/`):

- `chunks.parquet` (или fallback pickle)
- `embeddings.npy`
- `metadata.json`
- `index.pkl` / `index.json` (метаданные backend)

## Поиск

Одиночный запрос:

```bash
python -m src.literature.cli search --config config.yaml --query "digital traces migration social media urban space"
```

Пакетные запросы из YAML:

```bash
python -m src.literature.cli run-queries --config config.yaml --queries queries/literature_queries.yaml
```

Выходы одиночного поиска:

- `data/output/literature_search_results.csv`
- `data/output/literature_search_results.md`

Выходы пакетного поиска:

- `data/output/literature/<query_id>.csv`
- `data/output/literature/<query_id>.md`

## Задачи суммаризации

Одна задача:

```bash
python -m src.literature.cli summarize --config config.yaml --task digital_traces_and_migration_decisions
```

Все задачи:

```bash
python -m src.literature.cli summarize-all --config config.yaml --tasks queries/summarization_tasks.yaml
```

Выходы:

- `data/output/literature_summaries/<task_id>.md`
- `data/output/literature_summaries/<task_id>.json`

Текущий режим по умолчанию — extractive summary (настраивается в `config.yaml`):

- `literature.summarization.mode: extractive`

LLM-режим на этом этапе по умолчанию не включен.

## Поведение при ошибках

- При отсутствии индекса поиск возвращает понятную ошибку.
- При пустой выдаче batch summarize не падает и формирует частичный безопасный результат.
- Поврежденные/нечитаемые файлы статей пропускаются с предупреждением на этапе индексации.
