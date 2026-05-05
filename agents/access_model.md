# Agent Access Model

The access model defines what an agent may read, write, execute, and fetch. It is a first-class engineering artifact, not an implementation detail.

The default policy is deny-by-default. Access is granted only through the task contract.

## Access Classes

| Class | Description | Default |
|---|---|---|
| `read` | Local files and directories the agent may inspect | Deny |
| `write` | Local files and directories the agent may create or modify | Deny |
| `external` | Approved external APIs, domains, or repositories | Deny |
| `allowed_actions` | Exact commands or runtime operations the agent may execute | Deny |
| `evidence_source` | Datasets, article chunks, or code references that may support claims | Deny |

## Policy Rules

1. Deny by default.
2. Allow only paths, commands, and external sources listed in the contract.
3. Writes must stay inside `allowed_context.write`.
4. External access must include the domain/source and purpose.
5. Downloaded files are untrusted until format and provenance are checked.
6. Audit logs must record allowed actions, denied actions, quality gates, and stop conditions.
7. Source datasets under `DS/` are read-only research inputs unless a contract explicitly says otherwise.

## Recommended Access for Coding Agents

Read:

- `src/`
- `tests/`
- `config.yaml`
- `queries/`
- `agents/`

Write:

- explicitly assigned files under `src/`
- explicitly assigned tests under `tests/`
- agent contracts or documentation under `agents/`
- temporary outputs under `tmp_write_check/`
- audit output under `data/agent_audit/` when writable

Actions:

- run focused tests;
- inspect git status and diffs;
- write audit entries;
- produce human-readable reports.

Forbidden by default:

- destructive git commands;
- broad recursive deletion;
- deleting data directories;
- modifying source datasets;
- uncontrolled network downloads;
- paywall bypass;
- automated Google Scholar scraping.

## Rationale

The project contains research data, generated outputs, article corpora, and code. A narrow access model reduces accidental data loss, unsupported external disclosure, and irreproducible changes.

