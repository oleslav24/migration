# Sprint 3 Context-First Corpus Agent

Sprint 3 adds a context-first layer for local corpus analysis. The agent prepares context and evidence artifacts before any analytical interpretation.

## Goal

Create a controlled agent that can inspect allowed local data and exports, summarize available context, collect bounded evidence, and produce a human-readable report.

This is not an autonomous interpretation agent. It prepares reviewable research artifacts.

## Implemented Artifacts

- `agents/examples/corpus_analysis_agent_contract.yaml`
- `src/agents/context_pack.py`
- `src/agents/evidence_pack.py`
- `src/agents/corpus_agent.py`
- `src/agents/reporting.py`
- `tests/test_agent_context_pack.py`

## CLI

Prepare context only:

```powershell
python -m src.agents.cli prepare-context --contract agents/examples/corpus_analysis_agent_contract.yaml
```

Prepare context and evidence:

```powershell
python -m src.agents.cli analyze-corpus --contract agents/examples/corpus_analysis_agent_contract.yaml
```

## Outputs

The agent writes:

- `context_pack.json`
- `evidence_pack.json`
- `context_report.md`

When `data/agent_context/` is not writable, outputs fall back to `tmp_write_check/agent_context/`.

## Quality Gates

The current Sprint 3 tests check that:

- local datasets are discovered;
- schema and row counts are recorded;
- evidence items keep source paths;
- aggregate signals are produced from bounded samples;
- Markdown reports include sources;
- empty context produces an explicit limitation.

## Limitations

- Evidence aggregates are intentionally bounded samples unless precomputed exports are available.
- The agent does not produce final research conclusions.
- External sources are disabled by default.

