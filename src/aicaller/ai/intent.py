from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IntentError(ValueError):
    pass


class CallIntent(StrEnum):
    UNKNOWN = "unknown"
    URGENT = "urgent"
    IMPORTANT = "important"
    ROUTINE = "routine"
    SPAM = "spam"
    VOICEMAIL = "voicemail"
    HUMAN_REQUEST = "human_request"


@dataclass(frozen=True)
class IntentContext:
    intent: CallIntent
    confidence: float
    source_sequence: int
    reason: str | None = None


class IntentContextStore:
    """Deterministic, provider-neutral intent state for an active call."""

    def __init__(self) -> None:
        self._context = IntentContext(
            intent=CallIntent.UNKNOWN,
            confidence=0.0,
            source_sequence=-1,
        )

    def update(
        self,
        intent: CallIntent,
        confidence: float,
        *,
        source_sequence: int,
        reason: str | None = None,
    ) -> None:
        if not 0.0 <= confidence <= 1.0:
            raise IntentError("confidence must be between 0 and 1")
        if source_sequence <= self._context.source_sequence:
            raise IntentError("intent sequence must increase")
        if not isinstance(intent, CallIntent):
            raise IntentError("intent must be a CallIntent")
        self._context = IntentContext(
            intent=intent,
            confidence=confidence,
            source_sequence=source_sequence,
            reason=reason,
        )

    def get(self) -> IntentContext:
        return self._context
