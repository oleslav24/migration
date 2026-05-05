from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class QualityGateResult:
    passed: bool
    messages: list[str] = field(default_factory=list)


def evaluate_static_quality_gates(required_tests: list[str], workspace: str | Path) -> QualityGateResult:
    messages: list[str] = []
    passed = True
    for test_path in required_tests:
        resolved = Path(workspace) / test_path
        if not resolved.exists():
            passed = False
            messages.append(f"Missing required test path: {test_path}")
        else:
            messages.append(f"Required test path exists: {test_path}")
    return QualityGateResult(passed=passed, messages=messages)

