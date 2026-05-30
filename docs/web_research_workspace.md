# Web Research Workspace: Technical Reference / Техническая справка

## EN

## Purpose

This file documents stable technical behavior of the local web workspace (`src/webapp`) for maintainers and reviewers.

For day-to-day researcher usage, see [web_guide.md](web_guide.md).

## Core capabilities

- Registry-only experiment execution (`experiments/registry.yaml`).
- Run lifecycle tracking (`started/completed/failed`) with run log view.
- Run manifest inspection and run-manifest comparison export (MD/JSON/CSV).
- Run-focused artifact navigation (reports, tables, evidence).
- Report bundle assembly from selected local reports.
- Hypothesis-oriented views:
  - hypothesis sessions;
  - hypothesis matrix;
  - A/B hypothesis comparison;
  - hypothesis outcomes board.

## Output artifact helpers

Web-generated helper exports are written to preferred `data/output/web_*` directories with fallback to `tmp_write_check/web_*` when required:

- run packet exports;
- run comparison exports;
- run series exports;
- hypothesis session/matrix/compare/outcomes exports;
- report bundle exports.

## Safety model

- no arbitrary shell command API;
- experiment execution only through registry IDs;
- report bundles are extractive references, not autonomous interpretation;
- evidence review remains mandatory for final claims.

## Local run

```bash
python -B -m src.webapp.app
```

URL:

- `http://127.0.0.1:8765/`

## RU

## Назначение

Файл описывает стабильное техническое поведение локального web workspace (`src/webapp`) для поддержки и ревью.

Для повседневной работы исследователя используйте [web_guide.md](web_guide.md).

## Ключевые возможности

- запуск экспериментов только из реестра (`experiments/registry.yaml`);
- контроль жизненного цикла run (`started/completed/failed`) и просмотр run log;
- просмотр manifest и экспорт сравнения manifest (MD/JSON/CSV);
- run-focused навигация по отчетам, таблицам и evidence;
- сборка report bundle из выбранных локальных отчетов;
- гипотезные представления:
  - hypothesis sessions;
  - hypothesis matrix;
  - A/B hypothesis comparison;
  - hypothesis outcomes board.

## Служебные выходы Web

Служебные web-экспорты пишутся в приоритетные `data/output/web_*` и при необходимости в fallback `tmp_write_check/web_*`:

- run packet;
- run comparison;
- run series;
- hypothesis session/matrix/compare/outcomes;
- report bundle.

## Модель безопасности

- нет API для произвольных shell-команд;
- запуск экспериментов только по ID из реестра;
- report bundle — это extractive-референс, а не автоматическая интерпретация;
- финальные исследовательские утверждения требуют ручной проверки evidence.

## Локальный запуск

```bash
python -B -m src.webapp.app
```

Адрес:

- `http://127.0.0.1:8765/`
