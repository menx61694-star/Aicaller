import pytest

from aicaller.audio.frame import AudioFrame
from aicaller.audio.jitter_buffer import JitterBuffer, JitterBufferConfig


def frame(sequence: int) -> AudioFrame:
    return AudioFrame(
        stream_sid="stream-1",
        sequence_number=sequence,
        timestamp_ms=sequence,
        payload=bytes([sequence]),
    )


def test_jitter_buffer_releases_only_contiguous_frames() -> None:
    buffer = JitterBuffer()

    assert buffer.push(frame(1)) == "buffered"
    assert buffer.push(frame(3)) == "buffered"
    assert [item.sequence_number for item in buffer.pop_ready()] == [1]
    assert buffer.pending_count == 1

    assert buffer.push(frame(2)) == "buffered"
    assert [item.sequence_number for item in buffer.pop_ready()] == [2, 3]
    assert buffer.pending_count == 0


def test_jitter_buffer_deduplicates_old_or_duplicate_frames() -> None:
    buffer = JitterBuffer()

    assert buffer.push(frame(1)) == "buffered"
    assert buffer.push(frame(1)) == "duplicate"
    assert [item.sequence_number for item in buffer.pop_ready()] == [1]
    assert buffer.push(frame(1)) == "duplicate"


def test_jitter_buffer_keeps_unsequenced_frames_separate() -> None:
    buffer = JitterBuffer()
    item = AudioFrame("stream-1", None, None, b"x")

    assert buffer.push(item) == "unsequenced"
    assert buffer.pop_unsequenced() == item
    assert buffer.pop_unsequenced() is None


def test_jitter_buffer_has_bounded_capacity() -> None:
    buffer = JitterBuffer(JitterBufferConfig(max_frames=1))

    buffer.push(frame(1))
    with pytest.raises(BufferError, match="capacity"):
        buffer.push(frame(2))
