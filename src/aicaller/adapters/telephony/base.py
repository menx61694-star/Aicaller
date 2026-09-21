from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class TelephonyEventType(StrEnum):
    INCOMING_CALL = "INCOMING_CALL"
    RINGING = "RINGING"
    ANSWERED = "ANSWERED"
    HANGUP = "HANGUP"
    TRANSFER = "TRANSFER"
    FAILURE = "FAILURE"


@dataclass(frozen=True)
class TelephonyEvent:
    event_type: TelephonyEventType
    provider_call_id: str
    caller_number: str | None = None
    raw_status: str | None = None


class TelephonyAdapter(Protocol):
    def verify_request(payload: bytes, headers: dict[str, str]) -> bool: ...
    def parse_event(payload: bytes, headers: dict[str, str]) -> TelephonyEvent: ...
