from __future__ import annotations

from typing import Protocol

from aicaller.ai.session import RealtimeAISession
from aicaller.audio.utterance import AudioUtterance
from aicaller.services.intent_call_coordinator import CoordinatedIntentResult
from aicaller.services.realtime_intent_event_handler import RealtimeIntentEventHandler


class RealtimeTransport(Protocol):
    """Minimal async transport contract for a provider-owned realtime socket."""

    async def send(self, payload: str) -> None: ...

    async def receive(self) -> str | bytes: ...


class RealtimeCallWorkerError(RuntimeError):
    pass


class RealtimeCallWorker:
    """Join utterance submission and transcript routing for one call stream.

    Socket creation and authentication are deliberately injected through the
    transport contract, keeping API credentials and network lifecycle outside
    the deterministic call coordinator.
    """

    def __init__(
        self,
        session: RealtimeAISession,
        event_handler: RealtimeIntentEventHandler,
        transport: RealtimeTransport,
    ) -> None:
        if session.stream_sid != event_handler.session.stream_sid:
            raise RealtimeCallWorkerError("worker session and event handler mismatch")
        self.session = session
        self.event_handler = event_handler
        self.transport = transport

    async def send_utterance(self, utterance: AudioUtterance) -> None:
        if utterance.stream_sid != self.session.stream_sid:
            raise RealtimeCallWorkerError("utterance stream does not match worker stream")
        append_message, commit_message = self.session.build_audio_messages(utterance)
        try:
            await self.transport.send(append_message)
            await self.transport.send(commit_message)
        except Exception as exc:
            raise RealtimeCallWorkerError("failed to submit utterance to realtime transport") from exc

    async def receive_and_route(self) -> CoordinatedIntentResult | None:
        try:
            payload = await self.transport.receive()
        except Exception as exc:
            raise RealtimeCallWorkerError("failed to receive realtime event") from exc
        try:
            return self.event_handler.handle(payload)
        except ValueError as exc:
            raise RealtimeCallWorkerError("failed to process realtime event") from exc
