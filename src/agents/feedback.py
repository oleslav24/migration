from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .audit import AuditTrail


@dataclass
class FeedbackSensorReport:
    contract_fit: bool
    context_coverage: bool
    test_signal: bool
    risk_signal: bool
    messages: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.contract_fit and self.context_coverage and self.test_signal and not self.risk_signal


def evaluate_feedback_sensors(audit: AuditTrail, expected_outputs: list[str] | None = None) -> FeedbackSensorReport:
    event_types = [event.type for event in audit.events]
    messages: list[str] = []

    contract_fit = "contract_loaded" in event_types and "action_denied" not in event_types
    context_coverage = "context_checked" in event_types
    failed_gates = any(event.type == "quality_gate_failed" for event in audit.events)
    test_signal = not failed_gates
    risk_signal = "action_denied" in event_types

    if contract_fit:
        messages.append("Contract loaded without access violations")
    else:
        messages.append("Contract fit failed or access violation recorded")

    if context_coverage:
        messages.append("Allowed context was checked")
    else:
        messages.append("Allowed context was not checked")

    if test_signal:
        messages.append("No failed quality gates recorded")
    else:
        messages.append("At least one quality gate failed")

    for output in expected_outputs or []:
        if Path(output).exists():
            messages.append(f"Expected output exists: {output}")
        else:
            messages.append(f"Expected output missing: {output}")
            test_signal = False

    return FeedbackSensorReport(
        contract_fit=contract_fit,
        context_coverage=context_coverage,
        test_signal=test_signal,
        risk_signal=risk_signal,
        messages=messages,
    )

