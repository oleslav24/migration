# Feedback Sensors

Feedback sensors convert an agent run into observable lifecycle signals. They help reviewers decide whether an agent output is useful, risky, incomplete, or ready for further human inspection.

## Sensor Categories

| Sensor | Review Question | Example Signal |
|---|---|---|
| `contract_fit` | Did the run stay inside the task contract? | no access violations |
| `context_coverage` | Did the agent inspect the declared context? | context paths checked |
| `evidence_traceability` | Are analytical claims linked to sources? | evidence IDs, file paths, or chunk IDs present |
| `test_signal` | Did relevant tests or checks pass? | focused pytest target passed |
| `output_completeness` | Were expected outputs created? | declared files or reports exist |
| `reviewability` | Can a human inspect the result efficiently? | concise audit trail and explicit limitations |
| `risk_signal` | Did risky or denied actions occur? | denied command, failed gate, blocked external access |

## Lifecycle Placement

1. Before execution: validate the contract and access model.
2. During execution: record context checks, actions, denials, and intermediate failures.
3. After execution: evaluate quality gates and output completeness.
4. Review: inspect audit trail, residual risks, and evidence coverage.

## Interpretation

Feedback sensors are not a substitute for review. They are a structured checklist for deciding what needs attention.

A run can be useful even if it stops early, provided that it explains why it stopped and preserves enough audit information for diagnosis.

## Explicit Non-Metric

Generated lines of code are not a success metric. They may be recorded as descriptive metadata, but they must not be used as the primary measure of agent value.

