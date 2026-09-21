from datetime import datetime, timezone

from aicaller.domain.call import CallSession, CallState
from aicaller.domain.transitions import can_transition


class InvalidCallTransition(Exception):
    pass


class CallService:
    def __init__(self) -> None:
        self._sessions: dict[str, CallSession] = {}

    def create_incoming(self, call_id: str, caller_number: str | None) -> CallSession:
        if not call_id:
            raise ValueError("call_id is required")
        if call_id in self._sessions:
            return self._sessions[call_id]
        session = CallSession.incoming(call_id, caller_number)
        self._sessions[call_id] = session
        return session

    def transition(self, call_id: str, target: CallState, failure_reason: str | None = None) -> CallSession:
        current = self._sessions[call_id]
        if current.state == target:
            return current
        if not can_transition(current.state, target):
            raise InvalidCallTransition(f"{current.state} -> {target} is not allowed")
        updated = CallSession(
            call_id=current.call_id,
            caller_number=current.caller_number,
            state=target,
            created_at=current.created_at,
            updated_at=datetime.now(timezone.utc),
            failure_reason=failure_reason,
        )
        self._sessions[call_id] = updated
        return updated

    def get(self, call_id: str) -> CallSession | None:
        return self._sessions.get(call_id)
