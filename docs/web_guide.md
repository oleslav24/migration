# Web Guide / Гайд по Web UI

## EN

## Purpose

`src/webapp` is a local researcher workspace for running registry-defined experiments and reviewing outputs/evidence without shell scripting.

The UI does not allow arbitrary command execution.

## Start

```bash
python -B -m src.webapp.app
```

Open:

- `http://127.0.0.1:8765/`

## Language options

- Interface language switch is available in header (`EN` / `RU`).
- Experiment output language is controlled by `report_language` parameter (`en|ru`) per run.

## Core tabs (research flow)

1) `Overview`  
   quick project state and dataset/output readiness.

2) `Experiments`  
   run experiments from `experiments/registry.yaml`.

3) `Runs`  
   inspect run timeline, run logs, and run manifest comparisons.

4) `Reports`  
   run-focused report review, report bundles, run packets, run comparisons, hypothesis sessions/matrix/outcomes.

5) `Evidence`  
   filtered evidence inspection with source/toponym/sentiment/driver/topic/text controls.

6) `Toponym Research`  
   guided workflow view for hypothesis-driven toponym research steps.

## Typical workflow in UI

1. Define hypothesis and parameters in `Experiments`.
2. Run `toponym_research_workflow` or `research_story_e2e`.
3. Open `Runs` for log + manifest check.
4. Open `Reports` for main report and key tables.
5. Open `Evidence` for source-level verification.
6. Export run packet / comparison / hypothesis packet if needed.
7. Launch `sampling_coding` for manual coding sample.

## Main run artifacts to verify

- `run_manifest.json`
- primary report (`*.md`)
- key tables (`*.csv`)
- evidence files (`*_evidence*.json` / `*_samples*.csv`)

## Troubleshooting

- `Run log is empty`: refresh run list and open the latest run; verify process status is not still `running`.
- `CSV not found or path is not allowed`: use files inside allowed roots (`data/`, `DS/`, `queries/`, `tmp_write_check/`).
- permission errors on output directories: check write rights; fallback outputs may appear under `tmp_write_check/`.

## RU

## Назначение

`src/webapp` — локальный интерфейс исследователя для запуска экспериментов из реестра и проверки отчетов/evidence без работы через shell.

UI не позволяет выполнять произвольные команды.

## Запуск

```bash
python -B -m src.webapp.app
```

Открыть:

- `http://127.0.0.1:8765/`

## Языковые режимы

- В шапке доступен переключатель языка интерфейса (`EN` / `RU`).
- Язык экспериментальных отчетов задается параметром запуска `report_language` (`en|ru`).

## Ключевые вкладки (исследовательский поток)

1) `Overview`  
   быстрая сводка состояния проекта и доступности данных/выходов.

2) `Experiments`  
   запуск экспериментов из `experiments/registry.yaml`.

3) `Runs`  
   просмотр таймлайна запусков, логов и сравнения manifest.

4) `Reports`  
   run-focused просмотр отчетов, сборка bundle, run packet, run comparison, блоки hypothesis sessions/matrix/outcomes.

5) `Evidence`  
   фильтрация evidence по source/toponym/sentiment/driver/topic/text.

6) `Toponym Research`  
   пошаговый сценарий для гипотезного исследования топонимов.

## Типовой сценарий в UI

1. Задайте гипотезу и параметры во вкладке `Experiments`.
2. Запустите `toponym_research_workflow` или `research_story_e2e`.
3. Во вкладке `Runs` проверьте лог и manifest.
4. Во вкладке `Reports` откройте основной отчет и ключевые таблицы.
5. Во вкладке `Evidence` проверьте источники на уровне фрагментов.
6. При необходимости экспортируйте run packet / comparison / hypothesis packet.
7. Для ручной разметки запустите `sampling_coding`.

## Основные артефакты проверки

- `run_manifest.json`
- основной отчет (`*.md`)
- ключевые таблицы (`*.csv`)
- evidence-файлы (`*_evidence*.json` / `*_samples*.csv`)

## Troubleshooting

- `Run log is empty`: обновите список запусков и откройте актуальный run; проверьте, что статус процесса не `running`.
- `CSV not found or path is not allowed`: используйте файлы только внутри разрешенных root (`data/`, `DS/`, `queries/`, `tmp_write_check/`).
- ошибки прав доступа на output: проверьте права записи; fallback-результаты могут быть в `tmp_write_check/`.
