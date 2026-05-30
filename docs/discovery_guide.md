# Discovery Guide / Гайд по discovery

## EN

## Purpose

`src/discovery` collects candidate scholarly articles for migration research using open providers, scores relevance, and downloads only legally accessible full-text PDFs.

Supported providers (configurable in `config.yaml`):

- Crossref
- OpenAlex
- Semantic Scholar
- arXiv
- manual seed list (`queries/seed_sources.yaml`)

Google Scholar scraping is intentionally out of scope.

## Required configuration

Update `config.yaml`:

- `discovery.user_agent` (include a valid contact email)
- `discovery.year_from`, `year_to`
- `discovery.max_results_per_query`, `max_pdf_downloads`
- `discovery.relevance.min_score`
- `discovery.download.only_open_access` (expected to stay `true`)

Search tasks are stored in:

- `queries/article_discovery_queries.yaml`

Manual additions:

- `queries/seed_sources.yaml`

## Commands

Search and score candidates:

```bash
python -m src.discovery.cli search --config config.yaml --queries queries/article_discovery_queries.yaml
```

Download selected candidate PDFs:

```bash
python -m src.discovery.cli download --config config.yaml --candidates data/discovery/selected_articles.csv
```

Run full discovery flow:

```bash
python -m src.discovery.cli run --config config.yaml --queries queries/article_discovery_queries.yaml
```

Run discovery and trigger literature reindex:

```bash
python -m src.discovery.cli run --config config.yaml --queries queries/article_discovery_queries.yaml --reindex
```

Add manual seed entries:

```bash
python -m src.discovery.cli add-seed --config config.yaml --seed queries/seed_sources.yaml
```

## Outputs

`data/discovery/`:

- `candidates.csv`, `candidates.parquet`
- `selected_articles.csv`
- `rejected_articles.csv`
- `discovery_report.md`
- `raw/<provider>/*.json` (raw provider responses)

Downloaded files:

- PDFs: `articles/discovered/pdf/`
- metadata JSON: `articles/discovered/metadata/`

## Selection logic (high level)

- deduplication by DOI, fallback by normalized title;
- relevance score from title/abstract/terms/citation/open-access signals;
- explicit `reason` field for manual review;
- only OA-compatible or explicitly accessible PDF links are downloaded.

## Limitations

- provider APIs may change rate limits or fields;
- completeness differs across providers;
- low-score rejections require manual spot-checking for edge cases.

## RU

## Назначение

`src/discovery` собирает кандидатов научных статей по теме миграции через открытые провайдеры, считает релевантность и скачивает только легально доступные PDF.

Поддерживаемые провайдеры (настраиваются в `config.yaml`):

- Crossref
- OpenAlex
- Semantic Scholar
- arXiv
- ручной seed-файл (`queries/seed_sources.yaml`)

Автоскрейпинг Google Scholar намеренно не реализуется.

## Обязательная настройка

Проверьте `config.yaml`:

- `discovery.user_agent` (укажите валидный контактный email)
- `discovery.year_from`, `year_to`
- `discovery.max_results_per_query`, `max_pdf_downloads`
- `discovery.relevance.min_score`
- `discovery.download.only_open_access` (ожидается `true`)

Файл поисковых задач:

- `queries/article_discovery_queries.yaml`

Ручное добавление источников:

- `queries/seed_sources.yaml`

## Команды

Поиск и оценка кандидатов:

```bash
python -m src.discovery.cli search --config config.yaml --queries queries/article_discovery_queries.yaml
```

Скачивание PDF для отобранных кандидатов:

```bash
python -m src.discovery.cli download --config config.yaml --candidates data/discovery/selected_articles.csv
```

Полный запуск discovery:

```bash
python -m src.discovery.cli run --config config.yaml --queries queries/article_discovery_queries.yaml
```

Запуск discovery с переиндексацией literature:

```bash
python -m src.discovery.cli run --config config.yaml --queries queries/article_discovery_queries.yaml --reindex
```

Добавление ручных seed-источников:

```bash
python -m src.discovery.cli add-seed --config config.yaml --seed queries/seed_sources.yaml
```

## Выходы

`data/discovery/`:

- `candidates.csv`, `candidates.parquet`
- `selected_articles.csv`
- `rejected_articles.csv`
- `discovery_report.md`
- `raw/<provider>/*.json` (сырые ответы API)

Скачанные файлы:

- PDF: `articles/discovered/pdf/`
- metadata JSON: `articles/discovered/metadata/`

## Логика отбора (кратко)

- дедупликация по DOI, fallback по нормализованному title;
- релевантность на основе title/abstract/terms/citations/open-access сигналов;
- явное поле `reason` для ручной верификации;
- скачиваются только OA-совместимые или явно доступные PDF.

## Ограничения

- у API провайдеров могут меняться лимиты и поля;
- полнота выдачи различается между источниками;
- low-score отклонения нужно выборочно перепроверять вручную.
