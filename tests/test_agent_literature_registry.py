from pathlib import Path
from uuid import uuid4

import pytest

from src.agents.experiment_registry import inspect_experiment, load_registry, run_experiment
from src.agents.literature_bridge_agent import run_literature_bridge_agent
from src.webapp.app import AGENT_RUNNERS, summary_payload


def _contract(work_dir: Path) -> Path:
    path = work_dir / "contract.yaml"
    path.write_text(
        """
agent_id: test_bridge
purpose: "Test literature bridge."
task_contract: {inputs: [data, config.yaml], outputs: [bridge], invariants: [graceful]}
allowed_context:
  read: [data, config.yaml]
  write: [out, tmp_write_check]
  external: []
allowed_actions: []
forbidden_actions: [web search]
quality_gates: {required_tests: []}
stop_conditions: {stop_on_failed_quality_gate: true, stop_on_access_violation: true, stop_on_empty_context: false}
audit_trail: {output_dir: out/audit}
feedback_sensors: {evidence_traceability: true}
access_model: {default_policy: deny}
threat_lens: {zero_trust: true}
metrics: {primary: [traceability]}
""".strip(),
        encoding="utf-8",
    )
    return path


def test_literature_bridge_missing_index_graceful():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    data = work_dir / "data"
    data.mkdir(parents=True)
    (data / "documents.csv").write_text("text\nBangkok migration social media\n", encoding="utf-8")
    (work_dir / "config.yaml").write_text("input_path: x.csv\nliterature:\n  index_dir: missing_index\n", encoding="utf-8")

    result = run_literature_bridge_agent(_contract(work_dir), work_dir, "out", "config.yaml")

    report = (Path(result["output_dir"]) / "literature_corpus_bridge.md").read_text(encoding="utf-8")
    assert "Corpus evidence" in report
    assert result["limitations"]


def test_registry_loads_and_rejects_duplicates():
    experiments = load_registry("experiments/registry.yaml")
    assert inspect_experiment("toponym_urban_space", "experiments/registry.yaml")["runner"] == "toponym-agent"

    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    registry = work_dir / "registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text("experiments:\n  - id: x\n  - id: x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_registry(registry)


def test_run_experiment_creates_manifest():
    result = run_experiment("corpus_context", "experiments/registry.yaml", ".")

    assert Path(result["run_manifest_path"]).exists()


def test_web_summary_exposes_registry_not_legacy_presets():
    payload = summary_payload()

    assert payload["presets"] == {}
    assert payload["experiments"]
    assert all(item["runner"] in AGENT_RUNNERS for item in payload["experiments"])
