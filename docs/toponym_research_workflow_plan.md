# Plan Tracking: Toponym Research Workflow (A-F)

Updated: `2026-05-14 10:24:41 +07:00`

## Rules of execution

1. Work strictly by sprint order: `A -> B -> C -> D -> E -> F`.
2. Before starting a sprint, re-check this file against current code/tests.
3. After sprint completion:
   - update sprint status here;
   - add closure note with date/time;
   - run `python -m pytest`;
   - open a dedicated PR for that sprint.

## Status overview

| Sprint | Status | Notes |
|---|---|---|
| A | done | `toponym_research_workflow` exists in registry/UI; hypothesis + params saved to manifest. |
| B | done | `texts_by_toponym/<toponym>.csv` + `texts_by_toponym_manifest.json` implemented; includes source path/row index and configured max export limit. |
| C | done | Report V2 structure implemented with required research sections, explicit observed evidence vs interpretation notes, and RU/EN support. |
| D | done | Dedicated Toponym Research tab includes run setup, grouped artifacts, workflow steps, and explicit manual coding next-step actions. |
| E | done | `sampling_coding` now supports toponym-scoped sampling from `texts_by_toponym` with `stratify_by` controls and dedicated toponym exports/manifests. |
| F | planned | Partially covered by existing tests; missing full A-F-specific validation checklist and smoke/report documentation closure. |

## Sprint definitions and completion checklist

### Sprint A - Toponym Workflow Contract

Scope:
- experiment `toponym_research_workflow`;
- params: `hypothesis`, `dataset_scope`, `top_n_toponyms`, `samples_per_toponym`, `report_language`, `random_state`;
- workflow runner bound to `toponym_urban_space_agent`.

DoD:
- experiment visible in Web UI;
- hypothesis can be entered before run;
- params stored in manifest.

Checklist:
- [x] Experiment in registry.
- [x] Params are exposed in UI.
- [x] Params saved in `toponym_research_manifest.json`.

### Sprint B - Full Texts By Toponym Export

Scope:
- export `texts_by_toponym/<toponym>.csv`;
- required fields: `source`, `source_path`, `row_index`, `datetime`, `group`, `text`, `toponym`, `parent_city`, `type`, `sentiment`, `topic_id`, `migration_driver`;
- cap: `max_texts_per_toponym`;
- summary: `texts_by_toponym_manifest.json`.

DoD:
- one CSV per top-N toponym;
- source path and row index present;
- reproducible export.

Checklist:
- [x] `texts_by_toponym/` export created.
- [x] `texts_by_toponym_manifest.json` created.
- [x] Required traceability fields present (`source_path`, `row_index`).
- [x] `max_texts_per_toponym` applied.

### Sprint C - Research Report V2

Scope (required report structure):
- Research hypothesis;
- Corpus and method;
- Key observed places;
- City-level summary;
- District-level summary;
- Source comparison (Telegram vs YouTube);
- Topics per toponym;
- Sentiment per toponym;
- Migration drivers per toponym;
- Evidence examples;
- Text samples exported;
- Interpretation notes;
- Limitations;
- RU/EN support.

Checklist:
- [x] Full required section structure implemented.
- [x] Observed evidence and interpretation notes separated.
- [x] RU/EN verified for report text.

### Sprint D - Web UI Research Result View

Scope:
- dedicated `Toponym Research` section;
- blocks: hypothesis, scope, run params, run, main report, key tables, evidence, texts by toponym, manual coding next step;
- grouped outputs in reports/evidence.

Current state:
- dedicated tab exists and shows grouped outputs + run controls;
- workflow step cards added;
- button interaction layer moved to delegated `data-action` handlers.

Checklist:
- [x] Dedicated Toponym Research tab exists.
- [x] Main report and grouped artifacts accessible.
- [x] Manual coding next-step block explicit in UI copy/actions.
- [x] Final one-screen researcher UX validation completed.

### Sprint E - Manual Coding Bridge

Scope:
- run `sampling_coding` over `texts_by_toponym` subset;
- params: `toponym`, `sample_size`, `stratify_by` (`source|month|sentiment|topic_id|migration_driver`);
- outputs: `coding_sample_by_toponym.csv`, `coding_codebook_toponym.md`, `coding_manifest_toponym.json`.

Checklist:
- [x] Toponym-filtered coding sample pipeline implemented.
- [x] Required outputs exported.
- [x] Manual coding columns present.
- [x] Manifest records parameters.

### Sprint F - Quality And Validation

Scope tests:
- texts_by_toponym for top-N;
- dangerous aliases excluded;
- district -> parent city mapping;
- source comparison separated for Telegram/YouTube;
- report contains hypothesis;
- report avoids unsupported claims;
- toponym sampling reproducible;
- Web UI grouped result visible.

Checklist:
- [ ] Sprint-specific tests added/updated.
- [ ] Full `python -m pytest` green.
- [ ] Smoke run for workflow documented.
- [ ] Docs updated for researcher flow.

## Closure log

- `2026-05-13 19:04:48 +07:00` - Tracker created; sprint statuses normalized to A-F.
- `2026-05-13 19:04:48 +07:00` - Sprint A marked done (validated against registry/runner/UI/manifest).
- `2026-05-13 19:04:48 +07:00` - Sprint B marked done (validated against exports/manifest/params).
- `2026-05-13 19:12:04 +07:00` - Sprint C closed: report structure upgraded to research format; required sections and evidence/interpretation separation added; tests green and smoke run executed.
- `2026-05-14 09:55:33 +07:00` - Sprint D closed: Toponym Research UI refined into one-screen researcher flow, grouped artifacts preserved, and manual coding next-step actions added.
- `2026-05-14 10:24:41 +07:00` - Sprint E closed: implemented toponym-scoped coding bridge with `toponym` + `stratify_by` parameters, new `*_toponym` exports, UI controls, and validation tests.
