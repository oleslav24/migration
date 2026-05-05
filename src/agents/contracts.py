from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ContractError(ValueError):
    """Raised when an agent task contract is missing required fields."""


def _get_nested(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ContractError(f"Missing required contract field: {dotted_path}")
        current = current[part]
    return current


def _get_first_nested(payload: dict[str, Any], dotted_paths: list[str], default: Any = None) -> Any:
    for dotted_path in dotted_paths:
        try:
            return _get_nested(payload, dotted_path)
        except ContractError:
            continue
    return default


@dataclass
class AgentContract:
    path: Path
    raw: dict[str, Any]

    @property
    def agent_id(self) -> str:
        value = _get_first_nested(self.raw, ["agent_id", "agent.id"])
        if value is None:
            raise ContractError("Missing required contract field: agent_id")
        return str(value)

    @property
    def objective(self) -> str:
        value = _get_first_nested(self.raw, ["purpose", "task_contract.objective"])
        if value is None:
            raise ContractError("Missing required contract field: purpose")
        return str(value)

    @property
    def read_paths(self) -> list[str]:
        context = self.raw.get("allowed_context", {})
        return list(context.get("read", context.get("read_paths", [])))

    @property
    def write_paths(self) -> list[str]:
        context = self.raw.get("allowed_context", {})
        return list(context.get("write", context.get("write_paths", [])))

    @property
    def allowed_shell_commands(self) -> list[str]:
        actions = self.raw.get("allowed_actions", [])
        if isinstance(actions, dict):
            return list(actions.get("shell_commands", []))
        return [str(action) for action in actions]

    @property
    def forbidden_actions(self) -> list[str]:
        return [str(action) for action in self.raw.get("forbidden_actions", [])]

    @property
    def required_tests(self) -> list[str]:
        return list(self.raw.get("quality_gates", {}).get("required_tests", []))

    @property
    def required_checks(self) -> list[str]:
        return list(self.raw.get("quality_gates", {}).get("required_checks", []))

    @property
    def expected_outputs(self) -> list[str]:
        return [str(output) for output in self.raw.get("task_contract", {}).get("outputs", [])]

    @property
    def audit_output_dir(self) -> str:
        return str(self.raw.get("audit_trail", {}).get("output_dir", "data/agent_audit"))

    @property
    def max_runtime_seconds(self) -> int:
        return int(self.raw.get("stop_conditions", {}).get("max_runtime_seconds", 600))

    @property
    def stop_on_failed_quality_gate(self) -> bool:
        return bool(self.raw.get("stop_conditions", {}).get("stop_on_failed_quality_gate", True))

    @property
    def stop_on_empty_context(self) -> bool:
        return bool(self.raw.get("stop_conditions", {}).get("stop_on_empty_context", False))

    def validate(self) -> None:
        required = [
            "agent_id",
            "purpose",
            "task_contract.inputs",
            "task_contract.outputs",
            "task_contract.invariants",
            "allowed_context.read",
            "allowed_context.write",
            "allowed_context.external",
            "allowed_actions",
            "forbidden_actions",
            "quality_gates",
            "stop_conditions",
            "audit_trail",
            "feedback_sensors",
            "access_model",
            "threat_lens",
            "metrics",
        ]
        for field in required:
            _get_nested(self.raw, field)
        if not isinstance(self.read_paths, list):
            raise ContractError("allowed_context.read_paths must be a list")
        if not isinstance(self.write_paths, list):
            raise ContractError("allowed_context.write_paths must be a list")


def load_contract(path: str | Path) -> AgentContract:
    contract_path = Path(path)
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ContractError("Contract root must be a mapping")
    contract = AgentContract(path=contract_path, raw=payload)
    contract.validate()
    return contract
