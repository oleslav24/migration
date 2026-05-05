from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .access import AccessDenied, check_read_context
from .audit import AuditTrail
from .contracts import AgentContract, load_contract
from .executor import run_allowed_action
from .feedback import evaluate_feedback_sensors
from .quality import evaluate_static_quality_gates


@dataclass
class AgentRunResult:
    run_id: str
    status: str
    audit_path: Path
    message: str
    report_path: Path | None = None


def _write_audit(audit: AuditTrail, contract: AgentContract, workspace: str | Path) -> Path:
    requested_dir = Path(workspace) / contract.audit_output_dir
    try:
        return audit.write_json(requested_dir)
    except PermissionError as exc:
        fallback_dir = Path(workspace) / "tmp_write_check" / "agent_audit"
        audit.add(
            "stop_condition",
            "Audit output directory was not writable; using fallback",
            {"requested_dir": str(requested_dir), "fallback_dir": str(fallback_dir), "error": str(exc)},
        )
        return audit.write_json(fallback_dir)


def _write_report(audit: AuditTrail, contract: AgentContract, workspace: str | Path) -> Path | None:
    requested_dir = Path(workspace) / contract.audit_output_dir
    try:
        return audit.write_markdown(requested_dir)
    except PermissionError:
        fallback_dir = Path(workspace) / "tmp_write_check" / "agent_audit"
        return audit.write_markdown(fallback_dir)


def run_contract(contract_path: str | Path, workspace: str | Path = ".") -> AgentRunResult:
    contract = load_contract(contract_path)
    audit = AuditTrail.start(contract.agent_id, contract.objective)
    audit.add("contract_loaded", "Task contract loaded", {"path": str(contract.path)})

    try:
        context_paths = check_read_context(contract, workspace)
        audit.add(
            "context_checked",
            "Allowed context paths checked",
            {"existing_paths": [str(path) for path in context_paths]},
        )

        gate_result = evaluate_static_quality_gates(contract.required_tests, workspace)
        for message in gate_result.messages:
            event_type = "quality_gate_passed" if message.startswith("Required test path exists") else "quality_gate_failed"
            audit.add(event_type, message)

        if not gate_result.passed and contract.stop_on_failed_quality_gate:
            audit.status = "failed"
            audit.add("stop_condition", "Stopped because a required quality gate failed")
            audit_path = _write_audit(audit, contract, workspace)
            report_path = _write_report(audit, contract, workspace)
            return AgentRunResult(audit.run_id, audit.status, audit_path, "Quality gate failed", report_path)

        action_results = []
        for command in contract.allowed_shell_commands:
            audit.add("action_allowed", "Executing allowlisted action", {"command": command})
            result = run_allowed_action(command, contract, workspace)
            action_results.append(result)
            audit.add(
                "quality_gate_passed" if result.passed else "quality_gate_failed",
                "Allowlisted action completed",
                {
                    "command": result.command,
                    "returncode": result.returncode,
                    "stdout_tail": result.stdout,
                    "stderr_tail": result.stderr,
                },
            )

        if any(not result.passed for result in action_results) and contract.stop_on_failed_quality_gate:
            audit.status = "failed"
            audit.add("stop_condition", "Stopped because an allowlisted action failed")
            audit_path = _write_audit(audit, contract, workspace)
            report_path = _write_report(audit, contract, workspace)
            return AgentRunResult(audit.run_id, audit.status, audit_path, "Allowlisted action failed", report_path)

        audit.status = "completed"
        feedback = evaluate_feedback_sensors(audit)
        audit.add(
            "quality_gate_passed" if feedback.passed else "quality_gate_failed",
            "Feedback sensors evaluated",
            {"messages": feedback.messages, "passed": feedback.passed},
        )
        audit.add("completed", "Agent control loop completed")
        audit_path = _write_audit(audit, contract, workspace)
        report_path = _write_report(audit, contract, workspace)
        return AgentRunResult(audit.run_id, audit.status, audit_path, "Completed", report_path)
    except AccessDenied as exc:
        audit.status = "failed"
        audit.add("action_denied", str(exc))
        audit.add("stop_condition", "Stopped because of access violation")
        audit_path = _write_audit(audit, contract, workspace)
        report_path = _write_report(audit, contract, workspace)
        return AgentRunResult(audit.run_id, audit.status, audit_path, str(exc), report_path)
