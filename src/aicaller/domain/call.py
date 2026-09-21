from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class CallState(StrEnum):
    INCOMING = "INCOMING"
    RINGING = "RINGING"
    AI_ANSWERING = "AI_ANSWERING"
    AI_CALL = "AI_CALL"
    TAKEOVER_REQUESTED = "TAKEOVER_REQUESTED"
    HUMAN_CALL = "HUMAN_CALL"
    FAILURE = "FAILURE"
    CALL_ENDED = "CALL_ENDED"
    POST_PROCESSING = "POST_PROCESSING"


@dataclass(frozen=True)
class CallSession:
    call_id: str
    caller_number: str | None
    state: CallState
    created_at: datetime
    updated_at: datetime
    failure_reason: str | None = None
    provider_call_id: str | None = None
    last_provider_event: str | None = None

    @classmethod
    def incoming(cls, call_id: str, caller_number: str | None, provider_call_id: str | None = None) -> "CallSession":
        now = datetime.now(timezone.utc)
        return cls(call_id, caller_number, CallState.INCOMING, now, now, provider_call_id=provider_call_id)
