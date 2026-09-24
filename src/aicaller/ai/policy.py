from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PolicyError(ValueError):
    pass


class PolicyAction(StrEnum):
    CONTINUE_AI = "continue_ai"
    REQUEST_HUMAN = "request_human"
    END_CALL = "end_call"
    BLOCK = "block"


@dataclass(frozen=True)
class PolicyContext:
    action: PolicyAction
    reason: str
    source_sequence: int


class PolicyContextStore:
    """Deterministic policy decision boundary; no provider or LLM authority."""

    def __init__(self) -> None:
        self._context = PolicyContext(
            action=PolicyAction.CONTINUE_AI,
            reason="default",
            source_sequence=-1,
        )

    def update(
        self,
        action: PolicyAction,
        reason: str,
        *,
        source_sequence: int,
    ) -> None:
        if not reason.strip():
            raise PolicyError("policy reason must not be empty")
        if source_sequence <= self._context.source_sequence:
            raise PolicyError("policy sequence must increase")
        if not isinstance(action, PolicyAction):
            raise PolicyError("action must be a PolicyAction")
        self._context = PolicyContext(
            action=action,
            reason=reason,
            source_sequence=source_sequence,
        )

    def get(self) -> PolicyContext:
        return self._context
