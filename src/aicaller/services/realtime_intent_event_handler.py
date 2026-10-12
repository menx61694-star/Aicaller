from __future__ import annotations

from aicaller.ai.session import RealtimeAISession
from aicaller.services.intent_call_coordinator import (
    CoordinatedIntentResult,
    IntentCallCoordinator,
    IntentCallCoordinatorError,
)


class RealtimeIntentEventHandlerError(ValueError):
    pass


class RealtimeIntentEventHandler:
    """Bridge parsed realtime transcript events into the call coordinator.

    This handler is transport-neutral: the realtime WebSocket owner feeds
    provider event payloads here. Partial transcripts update session context
    but never drive routing or call-state transitions.
    """

    def __init__(
        self,
        session: RealtimeAISession,
        coordinator: IntentCallCoordinator,
    ) -> None:
        if session.stream_sid != coordinator.stream_sid:
            raise RealtimeIntentEventHandlerError(
                "AI session and call coordinator stream ids do not match"
            )
        self.session = session
        self.coordinator = coordinator

    def handle(
        self,
        payload: bytes | str,
    ) -> CoordinatedIntentResult | None:
        try:
            event = self.session.consume_event(payload)
        except ValueError as exc:
            raise RealtimeIntentEventHandlerError(str(exc)) from exc
        if event is None or not event.is_final:
            return None
        try:
            return self.coordinator.process_final_event(event)
        except IntentCallCoordinatorError as exc:
            raise RealtimeIntentEventHandlerError(str(exc)) from exc
