from aicaller.audio.output import AudioOutputFrame
from aicaller.audio.tts_buffer import TTSOutputBuffer


def frame(sequence: int) -> AudioOutputFrame:
    return AudioOutputFrame("stream-1", sequence, b"x", sequence)


def test_tts_buffer_flush_discards_pending_audio_and_advances_generation() -> None:
    buffer = TTSOutputBuffer()
    assert buffer.enqueue(frame(1)) == "queued"
    assert buffer.enqueue(frame(2)) == "queued"

    result = buffer.flush()

    assert result.discarded_frames == 2
    assert result.generation == 1
    assert buffer.generation == 1
    assert buffer.pipeline.pending_count == 0


def test_tts_buffer_rejects_frames_from_previous_generation() -> None:
    buffer = TTSOutputBuffer()
    generation = buffer.generation
    assert buffer.enqueue(frame(1), generation) == "queued"

    buffer.flush()

    assert buffer.enqueue(frame(2), generation) == "stale_generation"
    assert buffer.enqueue(frame(2), buffer.generation) == "queued"


def test_tts_buffer_flush_is_safe_when_empty() -> None:
    buffer = TTSOutputBuffer()

    result = buffer.flush()

    assert result.discarded_frames == 0
    assert result.generation == 1
