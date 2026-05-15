# Web Research Workspace

The web console is a local researcher interface for controlled experiments over the migration corpus.

## What It Supports

- Inspect configured Telegram and YouTube datasets.
- Run only experiments declared in `experiments/registry.yaml`.
- Try local text processing methods on a pasted sample.
- Browse CSV results with a text filter and row limit.
- Browse evidence CSV/JSON artifacts with source, toponym, sentiment, driver, topic, and text filters.
- Inspect run logs and compare `run_manifest.json` files.
- Build a Markdown report bundle from selected local artifacts.

## Recent UX Updates

- Research Session block in Toponym Research with workflow step statuses and next-step action.
- Run lifecycle notifications (`started/completed/failed`) without full panel redraw.
- Artifact file filters in Reports and Evidence (name/path filter) with shown/total counters per experiment.

## Safety Model

- The UI does not execute arbitrary shell commands.
- Experiment buttons are backed by the registry, not free-form commands.
- Report bundles are extractive collections of local artifacts and are marked for human review.
- Network access, web scraping, paywall bypass, and unsupported LLM claims are outside the UI scope.

## Local Run

```bash
python -B -m src.webapp.app
```

Open `http://127.0.0.1:8765/`.
