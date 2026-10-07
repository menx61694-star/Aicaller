from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.utterance import AudioUtterance


class BargeInContextError(ValueError):
    """Raised when caller speech context is invalid."""


@dataclass(frozen=True)
class BargeInContext:
    """Preserves the interrupted caller utterance for AI continuation."""

    utterance: AudioUtterance
    interrupted_tts_generation: int
    sequence: int

    def __post_init__(self) -> None:
        if self.interrupted_tts_generation < 0:
            raise BargeInContextError("interrupted_tts_generation cannot be negative")
        if self.sequence < 0:
            raise BargeInContextError("sequence cannot be negative")
        if not self.utterance.payload:
            raise BargeInContextError("utterance payload cannot be empty")


class BargeInContextStore:
    """Single active interruption context with deterministic replacement."""

    def __init__(self) -> None:
        self._context: BargeInContext | None = None

    def capture(
        self,
        utterance: AudioUtterance,
        *,
        interrupted_tts_generation: int,
        sequence: int,
    ) -> BargeInContext:
        context = BargeInContext(
            utterance=utterance,
            interrupted_tts_generation=interrupted_tts_generation,
            sequence=sequence,
        )
        self._context = context
        return context

    def peek(self) -> BargeInContext | None:
        return self._context

    def consume(self) -> BargeInContext | None:
        context = self._context
        self._context = None
        return context

    def clear(self) -> None:
        self._context = None
