from __future__ import annotations

from dataclasses import dataclass


class RepeatedBargeInError(ValueError):
    pass


@dataclass(frozen=True)
class InterruptionEvent:
    generation: int
    sequence: int


class RepeatedBargeInController:
    """Tracks repeated interruptions without reusing stale TTS state."""

    def __init__(self, max_interruptions: int = 3) -> None:
        if max_interruptions < 1:
            raise RepeatedBargeInError("max_interruptions must be positive")
        self.max_interruptions = max_interruptions
        self._count = 0
        self._generation = 0

    def begin(self, *, sequence: int) -> InterruptionEvent:
        if sequence < 0:
            raise RepeatedBargeInError("sequence must be non-negative")
        self._count += 1
        self._generation += 1
        if self._count > self.max_interruptions:
            raise RepeatedBargeInError("maximum interruptions exceeded")
        return InterruptionEvent(self._generation, sequence)

    def reset(self) -> None:
        self._count = 0
        self._generation += 1

    @property
    def count(self) -> int:
        return self._count

    @property
    def generation(self) -> int:
        return self._generation
