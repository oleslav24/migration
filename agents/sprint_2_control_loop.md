# Sprint 2 Control Loop

Sprint 2 introduces the minimal control loop for agents that generate or modify code.

## Implemented Control Points

1. Load a task contract in the unified agent format.
2. Validate required contract sections.
3. Check allowed local context before actions.
4. Enforce exact allowlisted shell actions.
5. Block forbidden and dangerous actions.
6. Evaluate static quality gates.
7. Execute allowlisted quality actions.
8. Stop on access violations or failed quality gates.
9. Write JSON audit trail.
10. Write Markdown audit report.
11. Evaluate feedback sensors.

## CLI

```powershell
python -m src.agents.cli run --contract agents/examples/coding_agent_contract.yaml
python -m src.agents.cli run --contract agents/examples/code_generation_agent_contract.yaml
```

## Current Scope

This is a controlled local runtime, not an autonomous coding agent. It creates the engineering guardrails that future specialized agents must use.

