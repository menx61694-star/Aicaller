from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from aicaller.domain.call import CallSession, CallState
from aicaller.services.call_repository import CallRepository
from aicaller.db.models import CallSessionModel


class PostgresCallRepository(CallRepository):
    """Durable PostgreSQL implementation of the call repository boundary."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    @staticmethod
    def _to_domain(row: CallSessionModel) -> CallSession:
        return CallSession(
            call_id=row.call_id,
            caller_number=row.caller_number,
            state=CallState(row.state),
            created_at=row.created_at,
            updated_at=row.updated_at,
            failure_reason=row.failure_reason,
            provider_call_id=row.provider_call_id,
            last_provider_event=row.last_provider_event,
        )

    def get(self, call_id: str) -> CallSession | None:
        with self.session_factory() as db:
            row = db.get(CallSessionModel, call_id)
            return self._to_domain(row) if row else None

    def save(self, session: CallSession) -> CallSession:
        with self.session_factory.begin() as db:
            row = db.get(CallSessionModel, session.call_id)
            if row is None:
                row = CallSessionModel(call_id=session.call_id)
                db.add(row)

            row.caller_number = session.caller_number
            row.state = session.state.value
            row.created_at = session.created_at
            row.updated_at = session.updated_at
            row.failure_reason = session.failure_reason
            row.provider_call_id = session.provider_call_id
            row.last_provider_event = session.last_provider_event

        return session
