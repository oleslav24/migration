from __future__ import annotations

from pathlib import Path

from .contracts import AgentContract


class AccessDenied(PermissionError):
    """Raised when an agent action exceeds its declared access model."""


def resolve_workspace_path(path: str | Path, workspace: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(workspace) / candidate
    return candidate.resolve()


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def check_read_context(contract: AgentContract, workspace: str | Path) -> list[Path]:
    existing: list[Path] = []
    for item in contract.read_paths:
        resolved = resolve_workspace_path(item, workspace)
        if resolved.exists():
            existing.append(resolved)
    if not existing and contract.stop_on_empty_context:
        raise AccessDenied("No allowed context paths exist")
    return existing


def assert_write_allowed(path: str | Path, contract: AgentContract, workspace: str | Path) -> Path:
    target = resolve_workspace_path(path, workspace)
    allowed_roots = [resolve_workspace_path(item, workspace) for item in contract.write_paths]
    if not any(target == root or _is_inside(target, root) for root in allowed_roots):
        raise AccessDenied(f"Write path is not allowed by contract: {target}")
    return target


def assert_shell_allowed(command: str, contract: AgentContract) -> None:
    allowed = contract.allowed_shell_commands
    if command not in allowed:
        raise AccessDenied(f"Shell command is not allowed by contract: {command}")

