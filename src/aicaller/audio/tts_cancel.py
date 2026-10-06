from __future__ import annotations

from dataclasses import dataclass


class TTSCancellationError(RuntimeError):
    pass


@dataclass(frozen=True)
class TTSCancellation:
    reason: str
    sequence: int


class TTSCancellationController:
    """Idempotent cancellation signal for an active TTS stream."""

    def __init__(self) -> None:
        self._cancelled = False
        self._signal: TTSCancellation | None = None

    def cancel(self, *, reason: str, sequence: int) -> TTSCancellation:
        if not reason.strip():
            raise TTSCancellationError("cancellation reason must not be empty")
        if sequence < 0:
            raise TTSCancellationError("cancellation sequence must be non-negative")
        if self._signal is None:
            self._signal = TTSCancellation(reason=reason, sequence=sequence)
            self._cancelled = True
        return self._signal

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def signal(self) -> TTSCancellation | None:
        return self._signal

    def reset(self) -> None:
        self._cancelled = False
        self._signal = None
