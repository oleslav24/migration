# Researcher Runbook / Runbook исследователя

## EN

This runbook describes the primary user story:

`hypothesis -> corpus processing -> toponym evidence -> report -> manual coding sample`

### 1) Define a hypothesis

Write a testable statement before running experiments. Example:

`Bangkok districts are overrepresented in adaptation-related migration discourse compared to island destinations.`

### 2) Prepare corpus

Use `config.yaml` to point to current Telegram/YouTube CSV files. Required columns:

`datetime,author,group,comment`

Run baseline pipeline:

```bash
python run_pipeline.py --config config.yaml
```

Expected baseline outputs: `data/output/documents_enriched.csv`, analysis CSV tables, `metrics.json`.

### 3) Run the toponym workflow experiment

Web path:

1. Start UI:
   ```bash
   python -B -m src.webapp.app
   ```
2. Open `http://127.0.0.1:8765/`.
3. Go to `Experiments` and run `toponym_research_workflow` (or `research_story_e2e`).
4. Fill parameters:
   - `hypothesis`
   - `dataset_scope` (`all|telegram|youtube`)
   - `top_n_toponyms`
   - `samples_per_toponym`
   - `max_texts_per_toponym`
   - `random_state`
   - `report_language` (`en|ru`)

CLI path (same logic):

```bash
python -m src.agents.cli run-experiment --id toponym_research_workflow --params "{\"hypothesis\":\"Bangkok districts are overrepresented in adaptation-related migration discourse\",\"dataset_scope\":\"all\",\"top_n_toponyms\":10,\"samples_per_toponym\":5,\"max_texts_per_toponym\":500,\"random_state\":42,\"report_language\":\"en\"}"
```

### 4) Review outputs

Primary artifacts are written under `data/agent_toponyms/<agent_id>/` (or fallback `tmp_write_check/...`):

- `toponym_research_report.md`
- `toponym_research_manifest.json`
- `toponym_frequency.csv`
- `city_level_stats.csv`
- `district_level_stats.csv`
- `source_comparison.csv`
- `topics_per_toponym.csv`
- `sentiment_per_toponym.csv`
- `drivers_per_toponym.csv`
- `toponym_samples.csv`
- `texts_by_toponym_manifest.json`
- `texts_by_toponym/<toponym>.csv`

Use `Reports` and `Evidence` tabs in web UI for run-focused review.

### 5) Build manual coding sample

If you need a coding sample for a specific toponym:

```bash
python -m src.agents.cli run-experiment --id sampling_coding --params "{\"toponym\":\"Sukhumvit\",\"stratify_by\":\"source\",\"sample_size\":120,\"random_state\":42,\"report_language\":\"en\"}"
```

Expected artifacts:

- `coding_sample_by_toponym.csv` (or `coding_sample.csv`)
- `coding_codebook_toponym.md` (or `coding_codebook.md`)
- `coding_manifest_toponym.json` (or `coding_manifest.json`)
- `intercoder_template.csv`

### 6) Reproducibility check before reporting results

For every reported finding, keep:

- run parameters (`run_manifest.json`);
- seed (`random_state`);
- source references (`source_path`, `row_index` in evidence/sample files);
- experiment/report language setting;
- linked evidence/report/table files used for interpretation.

Do not promote model output to conclusions without reading source snippets.

## RU

Этот runbook описывает базовую пользовательскую историю:

`гипотеза -> обработка корпуса -> топонимное evidence -> отчет -> выборка для ручного кодирования`

### 1) Сформулировать гипотезу

Перед запуском экспериментов зафиксируйте проверяемое утверждение. Пример:

`Районы Бангкока упоминаются в сообщениях об адаптации чаще, чем островные локации.`

### 2) Подготовить корпус

Проверьте пути к датасетам в `config.yaml`. Обязательные колонки CSV:

`datetime,author,group,comment`

Запуск базового пайплайна:

```bash
python run_pipeline.py --config config.yaml
```

Базовые выходы: `data/output/documents_enriched.csv`, таблицы анализа, `metrics.json`.

### 3) Запустить эксперимент toponym workflow

Через Web:

1. Запустите UI:
   ```bash
   python -B -m src.webapp.app
   ```
2. Откройте `http://127.0.0.1:8765/`.
3. Во вкладке `Experiments` запустите `toponym_research_workflow` (или `research_story_e2e`).
4. Заполните параметры:
   - `hypothesis`
   - `dataset_scope` (`all|telegram|youtube`)
   - `top_n_toponyms`
   - `samples_per_toponym`
   - `max_texts_per_toponym`
   - `random_state`
   - `report_language` (`en|ru`)

Через CLI (та же логика):

```bash
python -m src.agents.cli run-experiment --id toponym_research_workflow --params "{\"hypothesis\":\"Районы Бангкока чаще связаны с дискурсом адаптации\",\"dataset_scope\":\"all\",\"top_n_toponyms\":10,\"samples_per_toponym\":5,\"max_texts_per_toponym\":500,\"random_state\":42,\"report_language\":\"ru\"}"
```

### 4) Проверить выходы

Основные артефакты записываются в `data/agent_toponyms/<agent_id>/` (или fallback `tmp_write_check/...`):

- `toponym_research_report.md`
- `toponym_research_manifest.json`
- `toponym_frequency.csv`
- `city_level_stats.csv`
- `district_level_stats.csv`
- `source_comparison.csv`
- `topics_per_toponym.csv`
- `sentiment_per_toponym.csv`
- `drivers_per_toponym.csv`
- `toponym_samples.csv`
- `texts_by_toponym_manifest.json`
- `texts_by_toponym/<toponym>.csv`

Для проверки используйте вкладки `Reports` и `Evidence` в web-интерфейсе.

### 5) Сформировать выборку для ручного кодирования

Если нужна выборка по конкретному топониму:

```bash
python -m src.agents.cli run-experiment --id sampling_coding --params "{\"toponym\":\"Sukhumvit\",\"stratify_by\":\"source\",\"sample_size\":120,\"random_state\":42,\"report_language\":\"ru\"}"
```

Ожидаемые артефакты:

- `coding_sample_by_toponym.csv` (или `coding_sample.csv`)
- `coding_codebook_toponym.md` (или `coding_codebook.md`)
- `coding_manifest_toponym.json` (или `coding_manifest.json`)
- `intercoder_template.csv`

### 6) Проверка воспроизводимости перед публикацией

Для каждого вывода зафиксируйте:

- параметры запуска (`run_manifest.json`);
- seed (`random_state`);
- ссылки на исходные строки (`source_path`, `row_index` в evidence/sample);
- язык эксперимента/отчета;
- список report/table/evidence файлов, использованных в интерпретации.

Нельзя переносить модельные результаты в финальные выводы без ручной проверки исходных фрагментов.
