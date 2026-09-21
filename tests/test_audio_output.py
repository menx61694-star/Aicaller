from aicaller.audio.output import (
    AudioOutputConfig,
    AudioOutputFrame,
    OutboundAudioPipeline,
)


def frame(sequence: int, payload: bytes = b"x") -> AudioOutputFrame:
    return AudioOutputFrame("stream-1", sequence, payload, sequence)


def test_output_pipeline_releases_contiguous_frames_in_order() -> None:
    pipeline = OutboundAudioPipeline()
    assert pipeline.enqueue(frame(1)) == "queued"
    assert pipeline.enqueue(frame(3)) == "queued"
    assert pipeline.enqueue(frame(2)) == "queued"
    assert [item.sequence_number for item in pipeline.pop_ready()] == [1, 2, 3]


def test_output_pipeline_deduplicates_already_released_frames() -> None:
    pipeline = OutboundAudioPipeline()
    item = frame(1)
    assert pipeline.enqueue(item) == "queued"
    assert pipeline.pop_ready() == [item]
    assert pipeline.enqueue(item) == "duplicate"


def test_output_pipeline_applies_bounded_capacity() -> None:
    pipeline = OutboundAudioPipeline(AudioOutputConfig(max_frames=1))
    assert pipeline.enqueue(frame(1)) == "queued"
    try:
        pipeline.enqueue(frame(2))
    except BufferError:
        pass
    else:
        raise AssertionError("expected bounded output buffer to reject overflow")


def test_output_pipeline_clear_resets_cursor_and_pending_frames() -> None:
    pipeline = OutboundAudioPipeline()
    pipeline.enqueue(frame(2))
    pipeline.enqueue(frame(3))
    cleared = pipeline.clear()
    assert [item.sequence_number for item in cleared] == [2, 3]
    assert pipeline.pending_count == 0
    assert pipeline.next_sequence is None


def test_output_pipeline_pop_limit_preserves_remaining_order() -> None:
    pipeline = OutboundAudioPipeline()
    for sequence in (1, 2, 3):
        pipeline.enqueue(frame(sequence))
    assert [item.sequence_number for item in pipeline.pop_ready(limit=2)] == [1, 2]
    assert [item.sequence_number for item in pipeline.pop_ready()] == [3]
