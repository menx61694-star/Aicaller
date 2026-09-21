from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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


class StreamingSTT(Protocol):
    async def transcribe(self, utterance: AudioUtterance) -> Transcript: ...


class UnconfiguredSTT:
    """Explicit placeholder until a realtime STT provider is configured."""

    async def transcribe(self, utterance: AudioUtterance) -> Transcript:
        raise STTError("STT provider is not configured")
