from aicaller.domain.call import CallSession


class InMemoryCallRepository:
    """Phase-1 repository boundary; PostgreSQL adapter will replace this."""

    def __init__(self) -> None:
        self._items: dict[str, CallSession] = {}

    def get(self, call_id: str) -> CallSession | None:
        return self._items.get(call_id)

    def save(self, session: CallSession) -> CallSession:
        self._items[session.call_id] = session
        return session
