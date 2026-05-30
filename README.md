# Migration Research Stand

## EN

### Project Scope

This repository provides a local research stand for migration-focused text analysis:

- baseline corpus pipeline for Telegram/YouTube CSV datasets;
- toponym and urban-space analysis;
- migration narrative and place-perception analysis;
- reproducible sampling for manual coding;
- local literature retrieval/summarization over `articles/`;
- scholarly article discovery via open APIs;
- registry-driven web workspace for controlled experiment runs.

The stand is designed for **evidence-first research workflows** and stores reproducibility artifacts (manifests, context/evidence packs, audit traces).

### Repository Layout

```text
migration/
├── config.yaml
├── run_pipeline.py
├── src/
│   ├── pipeline modules (preprocess, language, topics, metrics, export)
│   ├── agents/            # controlled experiment runtime and research agents
│   ├── webapp/            # local web research workspace
│   ├── literature/        # local RAG-style retrieval over articles/
│   └── discovery/         # scholarly article discovery (OA-only download policy)
├── experiments/registry.yaml
├── queries/
├── articles/
├── data/
├── docs/
└── tests/
```

### Requirements

- Python 3.11+ (3.11/3.12 recommended for stable NLP stack behavior)
- local CSV datasets in paths configured in `config.yaml`
- optional internet access for discovery providers (Crossref/OpenAlex/etc.)
- note: `DS/` is gitignored and intended for local/private dataset files

Install:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Quickstart

1) Run baseline pipeline:

```bash
python run_pipeline.py --config config.yaml
```

2) Start web workspace:

```bash
python -B -m src.webapp.app
```

Open `http://127.0.0.1:8765/`.

3) Run a registry experiment from CLI (example):

```bash
python -m src.agents.cli run-experiment --id toponym_research_workflow --params "{\"hypothesis\":\"Bangkok districts are overrepresented in adaptation-related posts\",\"dataset_scope\":\"all\",\"top_n_toponyms\":10,\"samples_per_toponym\":5,\"max_texts_per_toponym\":500,\"random_state\":42,\"report_language\":\"en\"}"
```

### Main Run Modes

- **Pipeline**: `python run_pipeline.py --config config.yaml`
- **Web workspace**: `python -B -m src.webapp.app`
- **Agent CLI**: `python -m src.agents.cli ...`
- **Literature CLI**: `python -m src.literature.cli ...`
- **Discovery CLI**: `python -m src.discovery.cli ...`

### Where Results Are Written

- Baseline pipeline: `data/output/`
- Discovery: `data/discovery/`
- Literature index: `data/literature_index/`
- Agent outputs: `data/agent_*/<agent_id>/` (fallback: `tmp_write_check/agent_*/<agent_id>/`)
- Experiment manifests: `tmp_write_check/agent_experiments/<experiment_id>/run_manifest.json`
- Web packets/comparisons (if writable): `data/output/web_*` (fallback: `tmp_write_check/web_*`)

### Reproducibility and Audit

- `config.yaml` stores baseline pipeline settings.
- `random_state` is used across pipeline/agents for deterministic sampling.
- Every registry run stores:
  - `run_manifest.json` (parameters + outputs);
  - `experiment_config.json` (resolved experiment parameters).
- Controlled agent runtime emits audit artifacts to `data/agent_audit/` (fallback: `tmp_write_check/agent_audit/`).

See full reproducibility checklist: [docs/reproducibility.md](docs/reproducibility.md).

### Constraints and Assumptions

- CSV inputs must include: `datetime,author,group,comment`.
- Discovery module is **OA-only** and does not bypass paywalls.
- Literature module is local retrieval/summarization support, not autonomous final review writing.
- Web workspace executes registry-defined experiments only (no arbitrary shell execution from UI).

### Documentation Map

- Documentation index: [docs/index.md](docs/index.md)
- Researcher runbook: [docs/researcher_runbook.md](docs/researcher_runbook.md)
- Web guide: [docs/web_guide.md](docs/web_guide.md)
- Discovery guide: [docs/discovery_guide.md](docs/discovery_guide.md)
- Literature guide: [docs/literature_guide.md](docs/literature_guide.md)

---

## RU

### Назначение проекта

Этот репозиторий — локальный исследовательский стенд для анализа миграционных текстов:

- базовый пайплайн корпуса Telegram/YouTube CSV;
- анализ топонимов и городского пространства;
- анализ миграционных нарративов и place perception;
- воспроизводимая выборка для ручного кодирования;
- локальный retrieval/summary по научным статьям из `articles/`;
- поиск научных публикаций через открытые API;
- web-интерфейс с запуском только реестровых экспериментов.

Стенд ориентирован на **evidence-first workflow** и сохраняет артефакты воспроизводимости (manifest, context/evidence pack, audit).

### Структура репозитория

```text
migration/
├── config.yaml
├── run_pipeline.py
├── src/
│   ├── модули пайплайна (preprocess, language, topics, metrics, export)
│   ├── agents/            # контролируемый runtime экспериментов и агенты
│   ├── webapp/            # локальный web workspace исследователя
│   ├── literature/        # локальный retrieval по articles/
│   └── discovery/         # поиск статей (скачивание только OA PDF)
├── experiments/registry.yaml
├── queries/
├── articles/
├── data/
├── docs/
└── tests/
```

### Требования

- Python 3.11+ (рекомендовано 3.11/3.12 для стабильной NLP-совместимости)
- локальные CSV-датасеты по путям из `config.yaml`
- опционально интернет для discovery-провайдеров (Crossref/OpenAlex и др.)
- папка `DS/` игнорируется git и предназначена для локальных/приватных датасетов

Установка:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Быстрый старт

1) Запустить базовый пайплайн:

```bash
python run_pipeline.py --config config.yaml
```

2) Запустить web workspace:

```bash
python -B -m src.webapp.app
```

Открыть `http://127.0.0.1:8765/`.

3) Запустить эксперимент из реестра через CLI (пример):

```bash
python -m src.agents.cli run-experiment --id toponym_research_workflow --params "{\"hypothesis\":\"Районы Бангкока чаще связаны с сообщениями об адаптации\",\"dataset_scope\":\"all\",\"top_n_toponyms\":10,\"samples_per_toponym\":5,\"max_texts_per_toponym\":500,\"random_state\":42,\"report_language\":\"ru\"}"
```

### Основные режимы запуска

- **Pipeline**: `python run_pipeline.py --config config.yaml`
- **Web workspace**: `python -B -m src.webapp.app`
- **Agent CLI**: `python -m src.agents.cli ...`
- **Literature CLI**: `python -m src.literature.cli ...`
- **Discovery CLI**: `python -m src.discovery.cli ...`

### Где смотреть результаты

- Базовый пайплайн: `data/output/`
- Discovery: `data/discovery/`
- Literature index: `data/literature_index/`
- Выходы агентов: `data/agent_*/<agent_id>/` (fallback: `tmp_write_check/agent_*/<agent_id>/`)
- Манифесты запусков: `tmp_write_check/agent_experiments/<experiment_id>/run_manifest.json`
- Web packet/comparison (если директория доступна на запись): `data/output/web_*` (fallback: `tmp_write_check/web_*`)

### Воспроизводимость и аудит

- `config.yaml` хранит параметры базового пайплайна.
- `random_state` используется для детерминированных выборок.
- Каждый запуск эксперимента сохраняет:
  - `run_manifest.json` (параметры + выходы);
  - `experiment_config.json` (резолв параметров эксперимента).
- Контролируемый agent runtime пишет audit в `data/agent_audit/` (fallback: `tmp_write_check/agent_audit/`).

Подробно: [docs/reproducibility.md](docs/reproducibility.md).

### Ограничения и допущения

- Входные CSV должны содержать: `datetime,author,group,comment`.
- Модуль discovery работает только с open-access логикой и не обходит paywall.
- Модуль literature — это локальный retrieval/summarization для поддержки обзора, а не автогенерация итогового review без проверки.
- Web UI запускает только эксперименты из реестра (без произвольных команд из интерфейса).

### Карта документации

- Индекс документации: [docs/index.md](docs/index.md)
- Runbook исследователя: [docs/researcher_runbook.md](docs/researcher_runbook.md)
- Гайд по web-интерфейсу: [docs/web_guide.md](docs/web_guide.md)
- Гайд по discovery: [docs/discovery_guide.md](docs/discovery_guide.md)
- Гайд по literature: [docs/literature_guide.md](docs/literature_guide.md)
