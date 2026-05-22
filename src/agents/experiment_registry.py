from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .corpus_agent import analyze_corpus_context
from .literature_bridge_agent import run_literature_bridge_agent
from .migration_narrative_agent import run_migration_narrative_agent
from .place_perception_agent import run_place_perception_agent
from .sampling_agent import run_sampling_coding_agent
from .toponym_agent import run_toponym_urban_space_agent
from .report_i18n import normalize_report_language


RUNNERS = {
    "analyze-corpus": analyze_corpus_context,
    "toponym-agent": run_toponym_urban_space_agent,
    "place-perception": run_place_perception_agent,
    "sampling-coding": run_sampling_coding_agent,
    "migration-narrative": run_migration_narrative_agent,
    "literature-bridge": run_literature_bridge_agent,
    "research-story-e2e": None,
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
        parameters = item.setdefault("parameters", [])
        if not any(param.get("name") == "report_language" for param in parameters):
            parameters.append({"name": "report_language", "type": "string", "default": "ru", "choices": ["ru", "en"]})
    return experiments


def inspect_experiment(experiment_id: str, registry_path: str | Path = "experiments/registry.yaml") -> dict[str, Any]:
    for item in load_registry(registry_path):
        if item["id"] == experiment_id:
            return item
    raise ValueError(f"Experiment not found: {experiment_id}")


def run_experiment(experiment_id: str, registry_path: str | Path = "experiments/registry.yaml", workspace: str | Path = ".", params: dict[str, Any] | None = None) -> dict[str, Any]:
    experiment = inspect_experiment(experiment_id, registry_path)
    runner_name = experiment.get("runner")
    if runner_name not in RUNNERS:
        raise ValueError(f"Unknown experiment runner: {runner_name}")
    safe_params = validate_experiment_params(experiment, params or {})
    result = _run_with_params(runner_name, experiment, workspace, safe_params)
    manifest = {"experiment": experiment, "params": safe_params, "result": result}
    output_dir = Path(workspace) / "tmp_write_check" / "agent_experiments" / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "run_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    result["run_manifest_path"] = str(path)
    config_path = output_dir / "experiment_config.json"
    config_path.write_text(json.dumps({"id": experiment_id, "params": safe_params}, ensure_ascii=False, indent=2), encoding="utf-8")
    result["experiment_config_path"] = str(config_path)
    return result


def validate_experiment_params(experiment: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    schema = {item["name"]: item for item in experiment.get("parameters", [])}
    schema.setdefault("report_language", {"name": "report_language", "type": "string", "default": "ru", "choices": ["ru", "en"]})
    schema.setdefault("hypothesis", {"name": "hypothesis", "type": "string", "default": ""})
    unknown = sorted(set(params) - set(schema))
    if unknown:
        raise ValueError(f"Unsupported experiment parameters: {unknown}")
    result: dict[str, Any] = {}
    for name, spec in schema.items():
        value = params.get(name, spec.get("default"))
        if spec.get("type") == "int":
            value = int(value)
            if "min" in spec and value < int(spec["min"]):
                raise ValueError(f"Parameter {name} is below minimum {spec['min']}")
            if "max" in spec and value > int(spec["max"]):
                raise ValueError(f"Parameter {name} is above maximum {spec['max']}")
        elif spec.get("type") == "string":
            value = str(value)
            if spec.get("choices") and value not in spec["choices"]:
                raise ValueError(f"Parameter {name} must be one of {spec['choices']}")
            if name == "report_language":
                value = normalize_report_language(value)
        result[name] = value
    return result


def _run_with_params(runner_name: str, experiment: dict[str, Any], workspace: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    contract = str(experiment.get("agent_contract") or "")
    report_language = params.get("report_language", "ru")
    if runner_name == "research-story-e2e":
        return _run_research_story_e2e(experiment, workspace, params, report_language)
    if runner_name == "sampling-coding":
        return run_sampling_coding_agent(
            contract,
            workspace,
            sample_size=params.get("sample_size", 100),
            random_state=params.get("random_state", 42),
            report_language=report_language,
            toponym=params.get("toponym", ""),
            stratify_by=params.get("stratify_by", "source"),
        )
    if runner_name == "toponym-agent":
        return run_toponym_urban_space_agent(
            contract,
            workspace,
            random_state=params.get("random_state", 42),
            report_language=report_language,
            hypothesis=params.get("hypothesis", ""),
            dataset_scope=params.get("dataset_scope", "all"),
            top_n_toponyms=params.get("top_n_toponyms", 10),
            samples_per_toponym=params.get("samples_per_toponym", 3),
            max_texts_per_toponym=params.get("max_texts_per_toponym", 500),
        )
    if runner_name == "analyze-corpus":
        return analyze_corpus_context(contract, workspace, report_language=report_language)
    return RUNNERS[runner_name](contract, workspace, report_language=report_language)


def _run_research_story_e2e(experiment: dict[str, Any], workspace: str | Path, params: dict[str, Any], report_language: str) -> dict[str, Any]:
    contracts = experiment.get("contracts", {}) if isinstance(experiment.get("contracts"), dict) else {}
    toponym_contract = str(contracts.get("toponym") or experiment.get("agent_contract") or "agents/examples/toponym_urban_space_agent_contract.yaml")
    place_contract = str(contracts.get("place_perception") or "agents/examples/place_perception_agent_contract.yaml")
    narrative_contract = str(contracts.get("migration_narrative") or "agents/examples/migration_narrative_agent_contract.yaml")
    sampling_contract = str(contracts.get("sampling") or "agents/examples/sampling_coding_agent_contract.yaml")

    toponym_result = run_toponym_urban_space_agent(
        toponym_contract,
        workspace,
        random_state=int(params.get("random_state", 42)),
        report_language=report_language,
        hypothesis=str(params.get("hypothesis", "")),
        dataset_scope=str(params.get("dataset_scope", "all")),
        top_n_toponyms=int(params.get("top_n_toponyms", 10)),
        samples_per_toponym=int(params.get("samples_per_toponym", 5)),
        max_texts_per_toponym=int(params.get("max_texts_per_toponym", 200)),
    )
    place_result = run_place_perception_agent(place_contract, workspace, report_language=report_language)
    narrative_result = run_migration_narrative_agent(narrative_contract, workspace, report_language=report_language)

    toponym_for_sampling = str(params.get("sampling_toponym", "")).strip()
    if not toponym_for_sampling:
        toponym_for_sampling = _pick_toponym_for_sampling(toponym_result.get("output_dir"))
    sampling_result = run_sampling_coding_agent(
        sampling_contract,
        workspace,
        sample_size=int(params.get("sample_size", 150)),
        random_state=int(params.get("random_state", 42)),
        report_language=report_language,
        toponym=toponym_for_sampling,
        stratify_by=str(params.get("stratify_by", "source")),
    )

    root = Path(workspace) / "tmp_write_check" / "agent_experiments" / str(experiment.get("id") or "research_story_e2e")
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / "research_story_e2e_report.md"
    summary_path = root / "research_story_e2e_summary.json"
    steps_path = root / "research_story_e2e_steps.csv"

    steps = [
        {"step": "toponym", "report_path": toponym_result.get("report_path"), "output_dir": toponym_result.get("output_dir"), "evidence_items": toponym_result.get("evidence_items")},
        {"step": "place_perception", "report_path": place_result.get("report_path"), "output_dir": place_result.get("output_dir"), "evidence_items": place_result.get("evidence_items")},
        {"step": "migration_narrative", "report_path": narrative_result.get("report_path"), "output_dir": narrative_result.get("output_dir"), "evidence_items": narrative_result.get("evidence_items")},
        {"step": "sampling", "report_path": "", "output_dir": sampling_result.get("output_dir"), "evidence_items": sampling_result.get("sample_size")},
    ]
    pd.DataFrame(steps).to_csv(steps_path, index=False, encoding="utf-8")
    summary = {
        "experiment_id": experiment.get("id"),
        "report_language": report_language,
        "parameters": params,
        "sampling_toponym": toponym_for_sampling,
        "steps": steps,
        "outputs": {
            "toponym_report": toponym_result.get("report_path"),
            "place_report": place_result.get("report_path"),
            "narrative_report": narrative_result.get("report_path"),
            "coding_sample": str(Path(sampling_result.get("output_dir", "")) / "coding_sample_by_toponym.csv"),
            "steps_csv": str(steps_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Research Story E2E Report",
        "",
        "Controlled one-click run for researcher workflow:",
        "hypothesis -> toponyms -> place perception -> migration narratives -> manual coding sample.",
        "",
        "## Parameters",
        "",
        "```json",
        json.dumps(params, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sampling Toponym",
        "",
        f"`{toponym_for_sampling}`",
        "",
        "## Step Outputs",
        "",
        "| Step | Report | Output dir | Evidence/Sample count |",
        "| --- | --- | --- | ---: |",
    ]
    for row in steps:
        lines.append(
            f"| {row['step']} | `{row['report_path'] or ''}` | `{row['output_dir'] or ''}` | {row['evidence_items'] or 0} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Summary JSON: `{summary_path}`",
            f"- Steps CSV: `{steps_path}`",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "output_dir": str(root),
        "report_path": str(report_path),
        "evidence_items": int(
            (toponym_result.get("evidence_items") or 0)
            + (place_result.get("evidence_items") or 0)
            + (narrative_result.get("evidence_items") or 0)
        ),
        "sample_size": sampling_result.get("sample_size", 0),
        "sampling_toponym": toponym_for_sampling,
        "step_outputs": steps,
        "summary_path": str(summary_path),
    }


def _pick_toponym_for_sampling(output_dir: object) -> str:
    if not output_dir:
        return ""
    path = Path(str(output_dir)) / "toponym_frequency.csv"
    if not path.exists():
        return ""
    try:
        frame = pd.read_csv(path, nrows=1)
    except Exception:
        return ""
    if frame.empty or "toponym" not in frame:
        return ""
    return str(frame.iloc[0]["toponym"]).strip()
