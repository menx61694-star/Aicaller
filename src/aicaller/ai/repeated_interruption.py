from __future__ import annotations

from dataclasses import dataclass


class RepeatedInterruptionError(ValueError):
    """Raised when interruption tracking receives invalid metadata."""


@dataclass(frozen=True)
class RepeatedInterruptionConfig:
    max_interruptions_per_response: int = 3

    def __post_init__(self) -> None:
        if self.max_interruptions_per_response < 1:
            raise RepeatedInterruptionError(
                "max_interruptions_per_response must be positive"
            )


@dataclass(frozen=True)
class InterruptionDecision:
    generation: int
    sequence: int
    count: int
    accepted: bool
    limit_reached: bool


class RepeatedInterruptionGuard:
    """Bounds repeated barge-ins during one assistant response generation.

    Duplicate event sequences are idempotent. Once the configured limit is
    reached, further unique interruptions are rejected until the response
    generation is explicitly reset by the caller.
    """

    def __init__(self, config: RepeatedInterruptionConfig | None = None) -> None:
        self.config = config or RepeatedInterruptionConfig()
        self._generation: int | None = None
        self._last_sequence = -1
        self._count = 0
        self._limit_reached = False
        self._last_decision: InterruptionDecision | None = None

    def observe(self, *, generation: int, sequence: int) -> InterruptionDecision:
        if generation < 0:
            raise RepeatedInterruptionError("generation must be non-negative")
        if sequence < 0:
            raise RepeatedInterruptionError("sequence must be non-negative")
        if self._generation is None:
            self._generation = generation
        elif generation != self._generation:
            raise RepeatedInterruptionError(
                "reset is required before changing response generation"
            )

        if sequence == self._last_sequence and self._last_decision is not None:
            return self._last_decision
        if sequence < self._last_sequence:
            raise RepeatedInterruptionError("sequence must not move backwards")

        self._last_sequence = sequence
        if self._limit_reached:
            decision = InterruptionDecision(
                generation, sequence, self._count, False, True
            )
        else:
            self._count += 1
            self._limit_reached = self._count >= self.config.max_interruptions_per_response
            decision = InterruptionDecision(
                generation, sequence, self._count, True, self._limit_reached
            )
        self._last_decision = decision
        return decision

    def reset(self, *, generation: int) -> None:
        if generation < 0:
            raise RepeatedInterruptionError("generation must be non-negative")
        if self._generation is not None and generation <= self._generation:
            raise RepeatedInterruptionError("generation must increase on reset")
        self._generation = generation
        self._last_sequence = -1
        self._count = 0
        self._limit_reached = False
        self._last_decision = None

    @property
    def interruption_count(self) -> int:
        return self._count

    @property
    def limit_reached(self) -> bool:
        return self._limit_reached
