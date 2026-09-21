from __future__ import annotations

from abc import ABC, abstractmethod

from aicaller.domain.call import CallSession


class CallRepository(ABC):
    """Persistence boundary for call sessions."""

    @abstractmethod
    def get(self, call_id: str) -> CallSession | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, session: CallSession) -> CallSession:
        raise NotImplementedError


class InMemoryCallRepository(CallRepository):
    """Ephemeral repository used by local/unit tests."""

    def __init__(self) -> None:
        self._items: dict[str, CallSession] = {}

    def get(self, call_id: str) -> CallSession | None:
        return self._items.get(call_id)

    def save(self, session: CallSession) -> CallSession:
        self._items[session.call_id] = session
        return session
