from __future__ import annotations

from dataclasses import dataclass


class BargeInLatencyError(ValueError):
    pass


@dataclass(frozen=True)
class BargeInLatency:
    detected_at_ms: int
    cancellation_at_ms: int
    flush_at_ms: int

    @property
    def detection_to_cancellation_ms(self) -> int:
        return self.cancellation_at_ms - self.detected_at_ms

    @property
    def detection_to_flush_ms(self) -> int:
        return self.flush_at_ms - self.detected_at_ms


class BargeInLatencyRecorder:
    """Records deterministic event timestamps for barge-in latency budgets."""

    def record(
        self,
        *,
        detected_at_ms: int,
        cancellation_at_ms: int,
        flush_at_ms: int,
    ) -> BargeInLatency:
        values = (detected_at_ms, cancellation_at_ms, flush_at_ms)
        if any(value < 0 for value in values):
            raise BargeInLatencyError("timestamps must be non-negative")
        if cancellation_at_ms < detected_at_ms:
            raise BargeInLatencyError("cancellation cannot precede detection")
        if flush_at_ms < cancellation_at_ms:
            raise BargeInLatencyError("flush cannot precede cancellation")
        return BargeInLatency(
            detected_at_ms=detected_at_ms,
            cancellation_at_ms=cancellation_at_ms,
            flush_at_ms=flush_at_ms,
        )
