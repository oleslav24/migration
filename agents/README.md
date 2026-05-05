# Agents

This directory contains the governance and runtime contracts for controlled agents used in the migration research stand.

## Core Documents

- `shared_instructions.md`: common rules for all agents.
- `agent_template.yaml`: canonical contract template.
- `access_model.md`: least-privilege access model.
- `threat_model.md`: zero-trust and ATLAS-style threat lens.
- `feedback_sensors.md`: lifecycle review signals.
- `task_contract.schema.yaml`: lightweight schema description.
- `audit_log.schema.yaml`: audit event schema.

## Examples

- `examples/coding_agent_contract.yaml`: minimal coding-agent contract.
- `examples/code_generation_agent_contract.yaml`: bounded code-generation contract.

## Use

Run a contract through the local runtime:

```powershell
python -m src.agents.cli run --contract agents/examples/coding_agent_contract.yaml
```

The runtime writes JSON and Markdown audit outputs. If `data/agent_audit/` is not writable in the current environment, it falls back to `tmp_write_check/agent_audit/`.

## Status

These documents define Sprint 1 of the agent framework: shared instructions, unified agent format, access model, feedback sensors, threat lens, and evaluation metrics.

