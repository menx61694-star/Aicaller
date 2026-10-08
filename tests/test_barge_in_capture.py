import pytest

from aicaller.audio.barge_in_capture import (
    BargeInCaptureError,
    BargeInSpeechCapture,
)
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame


FORMAT = AudioFormat(AudioEncoding.PCM16_LE, 8000)


def frame(sequence: int, timestamp: int, stream: str = "s1") -> NormalizedAudioFrame:
    return NormalizedAudioFrame(
        stream_sid=stream,
        sequence_number=sequence,
        timestamp_ms=timestamp,
        payload=b"\x00\x01",
        format=FORMAT,
    )


def test_capture_preserves_caller_audio_and_timing() -> None:
    capture = BargeInSpeechCapture()
    capture.start(frame(1, 100))
    capture.append(frame(2, 120))
    result = capture.finish(frame(3, 140))

    assert result.stream_sid == "s1"
    assert result.started_at_ms == 100
    assert result.ended_at_ms == 140
    assert result.payload == b"\x00\x01" * 3
    assert not capture.active


def test_capture_rejects_append_before_start() -> None:
    with pytest.raises(BargeInCaptureError, match="has not started"):
        BargeInSpeechCapture().append(frame(1, 100))


def test_capture_rejects_stream_mismatch() -> None:
    capture = BargeInSpeechCapture()
    capture.start(frame(1, 100))
    with pytest.raises(BargeInCaptureError, match="stream_sid mismatch"):
        capture.append(frame(2, 120, "other"))


def test_capture_is_bounded() -> None:
    capture = BargeInSpeechCapture(max_frames=1)
    capture.start(frame(1, 100))
    with pytest.raises(BufferError):
        capture.append(frame(2, 120))
