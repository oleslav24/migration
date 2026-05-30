# Reproducibility Guide / Гайд по воспроизводимости

## EN

## Why this matters

The repository is intended for research workflows where every claim should be traceable to data, parameters, and evidence artifacts.

## Minimum reproducibility package per experiment run

Keep these files together:

1. `run_manifest.json`  
   parameters, experiment metadata, and output references.

2. `experiment_config.json`  
   resolved parameter set used by runtime.

3. Main report and supporting tables/evidence  
   markdown report + CSV/JSON artifacts used in interpretation.

4. Dataset version references  
   dataset paths and row-level references (`source_path`, `row_index`) from evidence/sample exports.

5. Seed values  
   at minimum `random_state`.

## Environment capture

Save local environment details for publication supplements:

```bash
python --version
pip freeze > requirements.lock.txt
```

If you use GPU/CPU-specific embedding stacks, record that in your methods notes.

## Data and config controls

- Source configuration: `config.yaml`
- Registry experiment definition: `experiments/registry.yaml`
- Query task files: `queries/*.yaml`

Do not change these silently between iterative hypothesis runs without recording diff.

## Audit artifacts

Controlled agent runtime writes audit traces:

- preferred: `data/agent_audit/`
- fallback: `tmp_write_check/agent_audit/`

Audit outputs include JSON and Markdown reports with quality gate and stop-condition events.

## Pre-publication checklist

- Same hypothesis + same params + same seed reproduces materially equivalent outputs.
- Reported claims are linked to explicit evidence items.
- Unsupported claims are not present in final text.
- Experiment language (`report_language`) is explicitly recorded.
- Primary dataset scope (`all|telegram|youtube`) is recorded.

## RU

## Зачем это нужно

Репозиторий рассчитан на исследовательский процесс, где каждый вывод должен быть трассируемым до данных, параметров и evidence-артефактов.

## Минимальный пакет воспроизводимости для каждого запуска

Сохраняйте вместе:

1. `run_manifest.json`  
   параметры, метаданные эксперимента, ссылки на выходы.

2. `experiment_config.json`  
   фактически использованный набор параметров.

3. Основной отчет и поддерживающие таблицы/evidence  
   markdown-отчет + CSV/JSON файлы, на которых основана интерпретация.

4. Ссылки на версии данных  
   пути к датасетам и построчные ссылки (`source_path`, `row_index`) из evidence/sample.

5. Значения seed  
   минимум `random_state`.

## Фиксация окружения

Для приложений к публикации сохраните локальное окружение:

```bash
python --version
pip freeze > requirements.lock.txt
```

Если используются разные стек/режимы embedding (CPU/GPU), зафиксируйте это в разделе методов.

## Контроль данных и конфигурации

- Базовая конфигурация: `config.yaml`
- Реестр экспериментов: `experiments/registry.yaml`
- Файлы задач/запросов: `queries/*.yaml`

Не меняйте их между итерациями гипотез без явной фиксации изменений.

## Audit-артефакты

Контролируемый runtime агентов пишет audit:

- приоритетный путь: `data/agent_audit/`
- fallback: `tmp_write_check/agent_audit/`

Форматы: JSON и Markdown с событиями quality gates и stop conditions.

## Чеклист перед публикацией

- Одинаковая гипотеза + одинаковые параметры + одинаковый seed дают эквивалентный результат.
- Каждый тезис отчета привязан к явным evidence items.
- В финальном тексте отсутствуют неподтвержденные утверждения.
- Язык эксперимента (`report_language`) явно зафиксирован.
- Область корпуса (`all|telegram|youtube`) явно зафиксирована.
