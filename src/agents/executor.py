from __future__ import annotations

import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .access import AccessDenied, assert_shell_allowed
from .contracts import AgentContract


DANGEROUS_ACTION_PATTERNS = [
    "git reset --hard",
    "git checkout --",
    "remove-item -recurse",
    "rm -rf",
    "del /",
    "format ",
    "sci-hub",
]


@dataclass
class ActionResult:
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def assert_not_forbidden(command: str, contract: AgentContract) -> None:
    normalized = command.lower()
    for pattern in DANGEROUS_ACTION_PATTERNS:
        if pattern in normalized:
            raise AccessDenied(f"Command matches dangerous action pattern: {pattern}")
    for forbidden in contract.forbidden_actions:
        if forbidden and forbidden.lower() in normalized:
            raise AccessDenied(f"Command matches forbidden action: {forbidden}")


def run_allowed_action(command: str, contract: AgentContract, workspace: str | Path) -> ActionResult:
    assert_shell_allowed(command, contract)
    assert_not_forbidden(command, contract)
    args = shlex.split(command)
    if args and args[0].lower() == "python":
        # Keep allowlisted commands portable while ensuring they run in the active interpreter env.
        args[0] = sys.executable
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(Path(workspace).resolve()) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        args,
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        timeout=contract.max_runtime_seconds,
        check=False,
    )
    return ActionResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout[-4000:],
        stderr=completed.stderr[-4000:],
    )

