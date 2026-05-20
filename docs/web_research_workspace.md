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
- Workflow Results Navigator in Toponym Research for one-click access to step-level report/table/evidence.
- Collapsible experiment cards in Reports/Evidence with sensible defaults (collapsed by default, expand-all toggle).
- Report/Evidence controls include `Only workflow experiments` and `Reset filters` for fast noise reduction.
- Reports tab includes **Key Workflow Artifacts** with quick actions per workflow step (open report, preview table, jump to reports/evidence).
- Report/Evidence controls include quick presets: `Workflow focus` and `All experiments`.
- Reports tab includes **Recent Artifacts** cache (open/remove/clear) for quick return to previously viewed files.
- Report Studio includes quick actions: `Add workflow reports` and `Clear selected`.
- Report Studio supports `Add visible reports` (from current report filters) for fast bundle assembly.
- Report Studio supports manual bundle ordering (`Move up` / `Move down`) before export.
- Report Studio persists selected bundle files between reloads (`webapp.reportBundleSelection`).
- Report/Evidence filter state is persisted locally (`webapp.uiFilters`) between page reloads.
- Reports/Evidence support run-level filtering (`run_id`) and run-centric grouping for faster review of one launch at a time.
- Reports tab includes a run-focused summary block with direct access to linked report/table/evidence artifacts.
- Runs tab includes a timeline panel (latest runs with status/duration and quick jump to reports/evidence).
- Run-focused summary includes direct shortcut to the manual coding step in Toponym Research.
- Run-focused summary includes `Evidence digest` (top snippets with metadata) for fast qualitative inspection.
- Report/Evidence preset controls include `Current run` for one-click filtering of artifacts by run id.
- Experiments tab shows last run status/id/time and quick actions for latest report/table/evidence per experiment.
- Experiments tab includes quick `Current run` actions (reports/evidence), and for toponym workflow also direct jump to manual coding from the latest run.
- Experiment parameter drafts (including hypothesis) are persisted locally (`webapp.experimentParamDrafts`) and restored after UI refresh.

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
