from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from src.config import PipelineConfig
from src.pipeline import run_pipeline

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
            toponym_output_dir=params.get("toponym_output_dir", ""),
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
    root = Path(workspace) / "tmp_write_check" / "agent_experiments" / str(experiment.get("id") or "research_story_e2e")
    root.mkdir(parents=True, exist_ok=True)
    ensure_corpus = str(params.get("ensure_corpus", "true")).strip().lower() in {"1", "true", "yes", "y", "on"}
    corpus_info: dict[str, Any] | None = None
    if ensure_corpus:
        corpus_info = _ensure_research_corpus(workspace, params)

    contracts = experiment.get("contracts", {}) if isinstance(experiment.get("contracts"), dict) else {}
    toponym_contract = str(contracts.get("toponym") or experiment.get("agent_contract") or "agents/examples/toponym_urban_space_agent_contract.yaml")
    place_contract = str(contracts.get("place_perception") or "agents/examples/place_perception_agent_contract.yaml")
    narrative_contract = str(contracts.get("migration_narrative") or "agents/examples/migration_narrative_agent_contract.yaml")
    sampling_contract = str(contracts.get("sampling") or "agents/examples/sampling_coding_agent_contract.yaml")
    read_overrides = [str(corpus_info["output_dir"])] if corpus_info and corpus_info.get("output_dir") else []
    toponym_contract = _augment_read_paths_for_run(toponym_contract, workspace, root, read_overrides)
    place_contract = _augment_read_paths_for_run(place_contract, workspace, root, read_overrides)
    narrative_contract = _augment_read_paths_for_run(narrative_contract, workspace, root, read_overrides)
    sampling_contract = _augment_read_paths_for_run(sampling_contract, workspace, root, read_overrides)

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
        candidates = toponym_result.get("top_toponyms") if isinstance(toponym_result.get("top_toponyms"), list) else []
        if candidates:
            toponym_for_sampling = str(candidates[0]).strip()
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
        toponym_output_dir=str(toponym_result.get("output_dir", "")),
    )

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
    sampling_output_dir = Path(str(sampling_result.get("output_dir", "")))
    coding_sample_path = sampling_output_dir / ("coding_sample_by_toponym.csv" if toponym_for_sampling else "coding_sample.csv")
    limitations = _collect_limitations(toponym_result, place_result, narrative_result, sampling_result)
    if not toponym_for_sampling:
        limitations.append("No toponym candidate was found in the current run; sampling used full corpus context.")
    summary = {
        "experiment_id": experiment.get("id"),
        "report_language": report_language,
        "parameters": params,
        "corpus_preparation": corpus_info,
        "sampling_toponym": toponym_for_sampling,
        "steps": steps,
        "limitations": limitations,
        "outputs": {
            "toponym_report": toponym_result.get("report_path"),
            "place_report": place_result.get("report_path"),
            "narrative_report": narrative_result.get("report_path"),
            "coding_sample": str(coding_sample_path),
            "steps_csv": str(steps_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    section = _report_labels(report_language)
    lines = [f"# {section['title']}", "", section["intro"], "", f"## {section['hypothesis']}", "", params.get("hypothesis", ""), ""]
    lines.extend([f"## {section['params']}", "", "```json", json.dumps(params, ensure_ascii=False, indent=2), "```", ""])
    if corpus_info:
        lines.extend([f"## {section['corpus']}", ""])
        lines.append(f"- status: `{corpus_info.get('status')}`")
        lines.append(f"- output_dir: `{corpus_info.get('output_dir')}`")
        lines.append(f"- documents: `{corpus_info.get('documents', 0)}`")
        lines.append(f"- messages: `{corpus_info.get('messages', 0)}`")
        lines.append("")
    lines.extend([f"## {section['sampling_toponym']}", "", f"`{toponym_for_sampling or section['none']}`", ""])
    lines.extend([f"## {section['steps']}", "", "| Step | Report | Output dir | Evidence/Sample count |", "| --- | --- | --- | ---: |"])
    for row in steps:
        lines.append(
            f"| {row['step']} | `{row['report_path'] or ''}` | `{row['output_dir'] or ''}` | {row['evidence_items'] or 0} |"
        )
    lines.extend(["", f"## {section['observed_places']}", ""])
    _append_csv_table(lines, _read_csv(Path(str(toponym_result.get("output_dir", ""))) / "toponym_frequency.csv"), 10, section["no_data"])
    lines.extend(["", f"## {section['source_comparison']}", ""])
    _append_csv_table(lines, _read_csv(Path(str(toponym_result.get("output_dir", ""))) / "source_comparison.csv"), 10, section["no_data"])
    lines.extend(["", f"## {section['place_distribution']}", ""])
    _append_csv_table(lines, _read_csv(Path(str(place_result.get("output_dir", ""))) / "place_perception_distribution.csv"), 10, section["no_data"])
    lines.extend(["", f"## {section['narrative_distribution']}", ""])
    _append_csv_table(lines, _read_csv(Path(str(narrative_result.get("output_dir", ""))) / "migration_narrative_matrix.csv"), 20, section["no_data"])
    lines.extend(
        [
            "",
            f"## {section['artifacts']}",
            "",
            f"- Summary JSON: `{summary_path}`",
            f"- Steps CSV: `{steps_path}`",
            f"- Coding sample: `{coding_sample_path}`",
            "",
            f"## {section['limitations']}",
            "",
        ]
    )
    if limitations:
        lines.extend([f"- {item}" for item in limitations])
    else:
        lines.append(f"- {section['none']}")
    lines.append("")
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
        "limitations": limitations,
        "corpus_preparation": corpus_info or {},
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


def _ensure_research_corpus(workspace: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    workspace_path = Path(workspace)
    output_dir = workspace_path / "tmp_write_check" / "research_output"
    interim_dir = workspace_path / "tmp_write_check" / "research_interim"
    output_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)
    docs_path = output_dir / "documents_enriched.csv"
    force_rebuild = str(params.get("rebuild_corpus", "false")).strip().lower() in {"1", "true", "yes", "y", "on"}
    if docs_path.exists() and not force_rebuild:
        return {"status": "reused", "output_dir": str(output_dir), "documents": _csv_row_count(docs_path), "messages": None}
    config_path = workspace_path / "config.yaml"
    if config_path.exists():
        config = PipelineConfig.from_yaml(config_path)
    else:
        config = PipelineConfig(
            input_path="DS/telegram_comments_12.25.csv",
            input_paths=[
                {"path": "DS/telegram_comments_12.25.csv", "source": "telegram"},
                {"path": "DS/youtube_comments_12.25.csv", "source": "youtube"},
            ],
        )
    config.output_dir = str(output_dir)
    config.interim_dir = str(interim_dir)
    config.embedding_backend = str(params.get("embedding_backend", "hash"))
    config.max_rows = int(params.get("max_rows", 300000))
    config.make_plots = False
    config.save_interim_parquet = False
    result = run_pipeline(config)
    return {
        "status": "rebuilt",
        "output_dir": str(output_dir),
        "documents": int(len(result.get("documents", []))),
        "messages": int(len(result.get("messages", []))),
    }


def _augment_read_paths_for_run(contract_path: str, workspace: str | Path, run_root: Path, extra_read_paths: list[str]) -> str:
    if not extra_read_paths:
        return contract_path
    source_path = Path(contract_path)
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    allowed = payload.setdefault("allowed_context", {})
    read_paths = [str(item) for item in allowed.get("read", [])]
    for item in extra_read_paths:
        if item not in read_paths:
            read_paths.append(item)
    allowed["read"] = read_paths
    contracts_dir = run_root / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    target = contracts_dir / source_path.name
    target.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return str(target)


def _csv_row_count(path: Path) -> int:
    try:
        total = 0
        for chunk in pd.read_csv(path, usecols=[0], chunksize=200_000, encoding="utf-8", on_bad_lines="skip"):
            total += len(chunk)
        return int(total)
    except Exception:
        try:
            with path.open("rb") as handle:
                rows = sum(1 for _ in handle)
        except Exception:
            return 0
        return max(rows - 1, 0)
    except BaseException:
        return 0


def _collect_limitations(*results: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for result in results:
        for item in result.get("limitations", []):
            text = str(item).strip()
            if text and text not in items:
                items.append(text)
    return items


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _append_csv_table(lines: list[str], frame: pd.DataFrame, max_rows: int, empty_message: str) -> None:
    if frame.empty:
        lines.append(empty_message)
        return
    lines.extend(["```csv", frame.head(max_rows).to_csv(index=False).strip(), "```"])


def _report_labels(report_language: str) -> dict[str, str]:
    if normalize_report_language(report_language) == "ru":
        return {
            "title": "E2E отчет исследовательского сценария",
            "intro": "Контролируемый прогон сценария: гипотеза -> топонимы -> place perception -> migration narratives -> выборка для ручного кодирования.",
            "hypothesis": "Исследовательская гипотеза",
            "params": "Параметры запуска",
            "corpus": "Подготовка корпуса",
            "sampling_toponym": "Топоним для выборки кодирования",
            "steps": "Шаги и артефакты",
            "observed_places": "Ключевые наблюдаемые места",
            "source_comparison": "Сравнение источников (Telegram vs YouTube)",
            "place_distribution": "Распределение place perception",
            "narrative_distribution": "Матрица миграционных нарративов",
            "artifacts": "Экспортированные артефакты",
            "limitations": "Ограничения",
            "no_data": "Нет данных для отображения.",
            "none": "нет",
        }
    return {
        "title": "Research Story E2E Report",
        "intro": "Controlled run of the researcher workflow: hypothesis -> toponyms -> place perception -> migration narratives -> manual coding sample.",
        "hypothesis": "Research hypothesis",
        "params": "Run parameters",
        "corpus": "Corpus preparation",
        "sampling_toponym": "Toponym for coding sample",
        "steps": "Steps and artifacts",
        "observed_places": "Key observed places",
        "source_comparison": "Source comparison (Telegram vs YouTube)",
        "place_distribution": "Place perception distribution",
        "narrative_distribution": "Migration narrative matrix",
        "artifacts": "Exported artifacts",
        "limitations": "Limitations",
        "no_data": "No data available.",
        "none": "none",
    }
