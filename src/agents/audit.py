from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AuditEvent:
    timestamp: str
    type: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditTrail:
    run_id: str
    agent_id: str
    task_objective: str
    started_at: str
    events: list[AuditEvent] = field(default_factory=list)
    status: str = "running"

    @classmethod
    def start(cls, agent_id: str, task_objective: str) -> "AuditTrail":
        return cls(
            run_id=uuid4().hex,
            agent_id=agent_id,
            task_objective=task_objective,
            started_at=utc_now(),
        )

    def add(self, event_type: str, message: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append(
            AuditEvent(
                timestamp=utc_now(),
                type=event_type,
                message=message,
                payload=payload or {},
            )
        )

    def write_json(self, output_dir: str | Path) -> Path:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        output_path = path / f"{self.run_id}.json"
        payload = asdict(self)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def write_markdown(self, output_dir: str | Path) -> Path:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        output_path = path / f"{self.run_id}.md"
        lines = [
            f"# Agent Audit: {self.agent_id}",
            "",
            f"Run ID: `{self.run_id}`",
            f"Status: `{self.status}`",
            f"Started: `{self.started_at}`",
            "",
            "## Task Objective",
            "",
            self.task_objective,
            "",
            "## Events",
            "",
        ]
        for event in self.events:
            lines.append(f"### {event.type}")
            lines.append("")
            lines.append(f"Time: `{event.timestamp}`")
            lines.append("")
            lines.append(event.message)
            if event.payload:
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(event.payload, ensure_ascii=False, indent=2))
                lines.append("```")
            lines.append("")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
