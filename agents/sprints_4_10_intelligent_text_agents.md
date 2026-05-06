# Sprints 4-10 Intelligent Text Agents

Sprints 4-10 add bounded, local, evidence-first research agents. They follow the shared agent contract, deny external access by default, and produce reviewable artifacts rather than final autonomous interpretations.

## Implemented Agents

- Toponym and urban-space agent.
- Place perception baseline agent.
- Manual coding sample agent.
- Migration narrative evidence agent.
- Literature-to-corpus bridge agent.
- Experiment registry runner.
- Registry-backed Web Agent Console.

## CLI

```powershell
python -m src.agents.cli analyze-toponyms --contract agents/examples/toponym_urban_space_agent_contract.yaml
python -m src.agents.cli analyze-place-perception --contract agents/examples/place_perception_agent_contract.yaml
python -m src.agents.cli prepare-coding-sample --contract agents/examples/sampling_coding_agent_contract.yaml
python -m src.agents.cli analyze-migration-narratives --contract agents/examples/migration_narrative_agent_contract.yaml
python -m src.agents.cli bridge-literature-corpus --contract agents/examples/literature_bridge_agent_contract.yaml
python -m src.agents.cli list-experiments
python -m src.agents.cli run-experiment --id toponym_urban_space
```

## Web Console

The web console reads `experiments/registry.yaml`. It starts only registered experiments and does not expose arbitrary command execution.

## Validation

The implementation is covered by tests for toponym evidence, place perception labels, manual sampling reproducibility, narrative evidence IDs, literature bridge fallback behavior, registry validation, and registry-backed web summary.

