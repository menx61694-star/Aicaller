from datetime import datetime, timezone

from aicaller.domain.call import CallSession, CallState
from aicaller.domain.transitions import can_transition
from aicaller.services.call_repository import InMemoryCallRepository


class InvalidCallTransition(Exception):
    pass


class CallService:
    def __init__(self, repository: InMemoryCallRepository | None = None) -> None:
        self.repository = repository or InMemoryCallRepository()

    def create_incoming(self, call_id: str, caller_number: str | None) -> CallSession:
        if not call_id:
            raise ValueError("call_id is required")
        existing = self.repository.get(call_id)
        if existing:
            return existing
        session = CallSession.incoming(call_id, caller_number, provider_call_id=call_id)
        return self.repository.save(session)

    def transition(self, call_id: str, target: CallState, failure_reason: str | None = None) -> CallSession:
        current = self.repository.get(call_id)
        if current is None:
            raise KeyError(call_id)
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
            provider_call_id=current.provider_call_id,
            last_provider_event=current.last_provider_event,
        )
        return self.repository.save(updated)

    def get(self, call_id: str) -> CallSession | None:
        return self.repository.get(call_id)
