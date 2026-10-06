"""Small typed-message contract used by all agents."""
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class AgentMessage:
    run_id: str
    message_id: str
    sender: str
    recipient: str
    message_type: str
    payload: dict[str, Any]
    status: str = "complete"
    schema_version: str = "1.0"

    @classmethod
    def create(cls, run_id: str, sender: str, recipient: str,
               message_type: str, payload: dict[str, Any]) -> "AgentMessage":
        return cls(run_id, str(uuid4()), sender, recipient, message_type, payload)

    def validate(self) -> None:
        required = ("run_id", "message_id", "sender", "recipient", "message_type", "payload")
        if any(not getattr(self, key) for key in required):
            raise ValueError("Message is missing a required field")
        if not isinstance(self.payload, dict):
            raise ValueError("Message payload must be an object")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunState:
    run_id: str
    review: str
    domain: str
    step_limit: int = 8
    steps: int = 0
    reports: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
