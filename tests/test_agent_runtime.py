from pathlib import Path
from uuid import uuid4

import pytest

from src.agents.access import AccessDenied, assert_write_allowed
from src.agents.contracts import ContractError, load_contract
from src.agents.feedback import evaluate_feedback_sensors
from src.agents.runtime import run_contract


def _write_contract(work_dir: Path, body: str) -> Path:
    path = work_dir / "contract.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_contract_loads_and_validates():
    contract = load_contract("agents/examples/coding_agent_contract.yaml")

    assert contract.agent_id == "coding_agent_minimal"
    assert "Inspect allowed code context" in contract.objective


def test_contract_rejects_missing_required_field():
    work_dir = Path("tmp_write_check") / "agent_tests" / uuid4().hex
    path = _write_contract(work_dir, "agent:\n  id: broken\n")

    with pytest.raises(ContractError):
        load_contract(path)


def test_access_model_denies_unlisted_write_path():
    contract = load_contract("agents/examples/coding_agent_contract.yaml")

    with pytest.raises(AccessDenied):
        assert_write_allowed("README.md", contract, ".")


def test_runtime_writes_audit_log():
    work_dir = Path("tmp_write_check") / "agent_tests" / uuid4().hex
    (work_dir / "src").mkdir(parents=True)
    (work_dir / "tests").mkdir()
    (work_dir / "config.yaml").write_text("input_path: test.csv\n", encoding="utf-8")
    (work_dir / "tests" / "test_placeholder_agent.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    contract_path = _write_contract(
        work_dir,
        """
agent_id: test_agent
purpose: "Validate local runtime."
task_contract:
  inputs:
    - config.yaml
  outputs:
    - audit log
  invariants:
    - contract validates
allowed_context:
  read:
    - src
    - tests
    - config.yaml
  write:
    - data/agent_audit
  external: []
allowed_actions:
  - "python -m pytest tests/test_placeholder_agent.py"
forbidden_actions: []
quality_gates:
  required_tests:
    - tests/test_placeholder_agent.py
stop_conditions:
  stop_on_failed_quality_gate: true
  stop_on_empty_context: true
audit_trail:
  output_dir: data/agent_audit
feedback_sensors:
  contract_fit: true
access_model:
  default_policy: deny
threat_lens:
  zero_trust: true
metrics:
  primary:
    - correctness
""".strip(),
    )

    result = run_contract(contract_path, work_dir)

    assert result.status == "completed"
    assert result.audit_path.exists()
    assert "completed" in result.audit_path.read_text(encoding="utf-8")
    assert result.report_path and result.report_path.exists()


def test_feedback_sensors_pass_on_completed_audit():
    result = run_contract("agents/examples/coding_agent_contract.yaml", ".")
    text = result.audit_path.read_text(encoding="utf-8")

    assert "Feedback sensors evaluated" in text


def test_forbidden_action_is_denied():
    work_dir = Path("tmp_write_check") / "agent_tests" / uuid4().hex
    (work_dir / "src").mkdir(parents=True)
    contract_path = _write_contract(
        work_dir,
        """
agent_id: deny_agent
purpose: "Validate forbidden action handling."
task_contract:
  inputs: []
  outputs:
    - audit log
  invariants:
    - forbidden actions are denied
allowed_context:
  read:
    - src
  write:
    - tmp_write_check
  external: []
allowed_actions:
  - "git reset --hard"
forbidden_actions:
  - git reset --hard
quality_gates:
  required_tests: []
stop_conditions:
  stop_on_failed_quality_gate: true
  stop_on_empty_context: true
audit_trail:
  output_dir: tmp_write_check/agent_audit
feedback_sensors:
  risk_signal: true
access_model:
  default_policy: deny
threat_lens:
  zero_trust: true
metrics:
  primary:
    - correctness
""".strip(),
    )

    result = run_contract(contract_path, work_dir)

    assert result.status == "failed"
    assert "forbidden" in result.message.lower() or "dangerous" in result.message.lower()
