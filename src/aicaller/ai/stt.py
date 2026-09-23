from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aicaller.ai.transcript import TranscriptUpdate
from aicaller.audio.utterance import AudioUtterance


class STTError(RuntimeError):
    """Raised when speech-to-text processing fails."""


@dataclass(frozen=True)
class Transcript:
    text: str
    is_final: bool
    stream_sid: str
    started_at_ms: int | None
    ended_at_ms: int | None
    language: str | None = None


@dataclass(frozen=True)
class StreamingTranscriptEvent:
    """Provider-neutral partial/final transcript event."""

    stream_sid: str
    text: str
    is_final: bool
    sequence: int
    language: str | None = None


class StreamingSTT(Protocol):
    async def transcribe(self, utterance: AudioUtterance) -> Transcript: ...


class StreamingSTTEventSink(Protocol):
    """Consumes provider-neutral streaming transcript events."""

    def apply(self, event: StreamingTranscriptEvent) -> None: ...


class UnconfiguredSTT:
    """Explicit placeholder until a realtime STT provider is configured."""

    async def transcribe(self, utterance: AudioUtterance) -> Transcript:
        raise STTError("STT provider is not configured")


class TranscriptEventAdapter:
    """Validates and normalizes streaming STT events before the AI layer."""

    def __init__(self, stream_sid: str) -> None:
        if not stream_sid:
            raise STTError("stream_sid is required")
        self.stream_sid = stream_sid
        self._last_sequence = -1

    def consume(self, update: TranscriptUpdate) -> StreamingTranscriptEvent:
        if update.stream_sid != self.stream_sid:
            raise STTError("transcript stream mismatch")
        if update.sequence <= self._last_sequence:
            raise STTError("transcript sequence must increase")
        if not update.text.strip():
            raise STTError("transcript text cannot be empty")
        self._last_sequence = update.sequence
        return StreamingTranscriptEvent(
            stream_sid=update.stream_sid,
            text=update.text.strip(),
            is_final=update.is_final,
            sequence=update.sequence,
        )
