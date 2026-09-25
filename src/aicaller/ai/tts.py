from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


class TTSError(RuntimeError):
    pass


@dataclass(frozen=True)
class TTSChunk:
    payload: bytes
    sequence: int
    is_final: bool = False


class StreamingTTS(Protocol):
    async def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
    ) -> AsyncIterator[TTSChunk]: ...


class UnconfiguredStreamingTTS:
    """Fail-closed provider boundary until a live TTS transport is configured."""

    async def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
    ) -> AsyncIterator[TTSChunk]:
        raise TTSError("streaming TTS provider is not configured")


class TTSStreamState:
    """Validates and accumulates provider-neutral streamed TTS audio."""

    def __init__(self) -> None:
        self._sequence = -1
        self._chunks: list[bytes] = []
        self._finished = False

    def apply(self, chunk: TTSChunk) -> None:
        if self._finished:
            raise TTSError("TTS stream is already finished")
        if chunk.sequence <= self._sequence:
            raise TTSError("TTS sequence must increase")
        if not chunk.payload:
            raise TTSError("TTS chunk must not be empty")
        self._sequence = chunk.sequence
        self._chunks.append(chunk.payload)
        if chunk.is_final:
            self._finished = True

    @property
    def audio(self) -> bytes:
        return b"".join(self._chunks)

    @property
    def finished(self) -> bool:
        return self._finished
