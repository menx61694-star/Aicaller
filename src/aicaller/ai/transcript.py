from __future__ import annotations

from dataclasses import dataclass


class TranscriptError(ValueError):
    """Raised when a transcript update is invalid."""


@dataclass(frozen=True)
class TranscriptUpdate:
    stream_sid: str
    text: str
    is_final: bool
    sequence: int
    language: str | None = None


class TranscriptState:
    """Maintains monotonic partial/final transcript state for one stream."""

    def __init__(self, stream_sid: str) -> None:
        if not stream_sid:
            raise TranscriptError("stream_sid is required")
        self.stream_sid = stream_sid
        self._last_sequence = -1
        self._partial = ""
        self._final_segments: list[str] = []

    def apply(self, update: TranscriptUpdate) -> None:
        if update.stream_sid != self.stream_sid:
            raise TranscriptError("transcript stream mismatch")
        if update.sequence <= self._last_sequence:
            raise TranscriptError("transcript sequence must increase")
        if not update.text.strip():
            raise TranscriptError("transcript text cannot be empty")

        self._last_sequence = update.sequence
        if update.is_final:
            self._final_segments.append(update.text.strip())
            self._partial = ""
        else:
            self._partial = update.text.strip()

    @property
    def partial(self) -> str:
        return self._partial

    @property
    def final_text(self) -> str:
        return " ".join(self._final_segments)

    @property
    def current_text(self) -> str:
        if self._partial:
            return f"{self.final_text} {self._partial}".strip()
        return self.final_text

    @property
    def last_sequence(self) -> int:
        return self._last_sequence

    def reset(self) -> None:
        self._last_sequence = -1
        self._partial = ""
        self._final_segments.clear()
