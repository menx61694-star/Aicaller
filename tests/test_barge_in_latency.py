import pytest

from aicaller.audio.barge_in_latency import (
    BargeInLatencyError,
    BargeInLatencyRecorder,
)


def test_barge_in_latency_records_detection_to_flush() -> None:
    latency = BargeInLatencyRecorder().record(
        detected_at_ms=1000,
        cancellation_at_ms=1050,
        flush_at_ms=1100,
    )

    assert latency.detection_to_cancellation_ms == 50
    assert latency.detection_to_flush_ms == 100


def test_barge_in_latency_rejects_reversed_events() -> None:
    with pytest.raises(BargeInLatencyError, match="cancellation cannot"):
        BargeInLatencyRecorder().record(
            detected_at_ms=100,
            cancellation_at_ms=90,
            flush_at_ms=100,
        )


def test_barge_in_latency_rejects_negative_timestamps() -> None:
    with pytest.raises(BargeInLatencyError, match="non-negative"):
        BargeInLatencyRecorder().record(
            detected_at_ms=-1,
            cancellation_at_ms=0,
            flush_at_ms=0,
        )
