from dataclasses import dataclass
from enum import StrEnum
class CallState(StrEnum):
    INCOMING="INCOMING"; RINGING="RINGING"; AI_ANSWERING="AI_ANSWERING"; AI_CALL="AI_CALL"; TAKEOVER_REQUESTED="TAKEOVER_REQUESTED"; HUMAN_CALL="HUMAN_CALL"; FAILURE="FAILURE"; CALL_ENDED="CALL_ENDED"; POST_PROCESSING="POST_PROCESSING"
@dataclass(frozen=True)
class CallSession:
    call_id: str
    caller_number: str | None
    state: CallState
