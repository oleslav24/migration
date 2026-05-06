from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .corpus_agent import analyze_corpus_context
from .literature_bridge_agent import run_literature_bridge_agent
from .migration_narrative_agent import run_migration_narrative_agent
from .place_perception_agent import run_place_perception_agent
from .sampling_agent import run_sampling_coding_agent
from .toponym_agent import run_toponym_urban_space_agent


RUNNERS = {
    "analyze-corpus": analyze_corpus_context,
    "toponym-agent": run_toponym_urban_space_agent,
    "place-perception": run_place_perception_agent,
    "sampling-coding": run_sampling_coding_agent,
    "migration-narrative": run_migration_narrative_agent,
    "literature-bridge": run_literature_bridge_agent,
}


def load_registry(path: str | Path = "experiments/registry.yaml") -> list[dict[str, Any]]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    experiments = payload.get("experiments", [])
    seen: set[str] = set()
    for item in experiments:
        exp_id = item.get("id")
        if not exp_id:
            raise ValueError("Experiment id is required")
        if exp_id in seen:
            raise ValueError(f"Duplicate experiment id: {exp_id}")
        seen.add(exp_id)
    return experiments


def inspect_experiment(experiment_id: str, registry_path: str | Path = "experiments/registry.yaml") -> dict[str, Any]:
    for item in load_registry(registry_path):
        if item["id"] == experiment_id:
            return item
    raise ValueError(f"Experiment not found: {experiment_id}")


def run_experiment(experiment_id: str, registry_path: str | Path = "experiments/registry.yaml", workspace: str | Path = ".") -> dict[str, Any]:
    experiment = inspect_experiment(experiment_id, registry_path)
    runner_name = experiment.get("runner")
    if runner_name not in RUNNERS:
        raise ValueError(f"Unknown experiment runner: {runner_name}")
    result = RUNNERS[runner_name](experiment["agent_contract"], workspace)
    manifest = {"experiment": experiment, "result": result}
    output_dir = Path(workspace) / "tmp_write_check" / "agent_experiments" / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "run_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    result["run_manifest_path"] = str(path)
    return result

