import base64

import pytest

from aicaller.audio.frame import AudioFrameError, decode_base64_audio
from aicaller.audio.sequence import AudioSequenceTracker


def test_decode_base64_audio_creates_provider_neutral_frame() -> None:
    frame = decode_base64_audio(
        stream_sid="stream-1",
        sequence_number="7",
        timestamp="120",
        payload=base64.b64encode(b"audio").decode(),
    )

    assert frame.stream_sid == "stream-1"
    assert frame.sequence_number == 7
    assert frame.timestamp_ms == 120
    assert frame.payload == b"audio"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "stream_sid": "stream-1",
                "sequence_number": "1",
                "timestamp": "0",
                "payload": "not-base64",
            },
            "base64",
        ),
        (
            {
                "stream_sid": None,
                "sequence_number": "1",
                "timestamp": "0",
                "payload": "YQ==",
            },
            "stream_sid",
        ),
        (
            {
                "stream_sid": "stream-1",
                "sequence_number": "x",
                "timestamp": "0",
                "payload": "YQ==",
            },
            "sequence",
        ),
    ],
)
def test_invalid_audio_frame_is_rejected(kwargs: dict, message: str) -> None:
    with pytest.raises(AudioFrameError, match=message):
        decode_base64_audio(**kwargs)


def test_sequence_tracker_detects_order_without_reordering() -> None:
    tracker = AudioSequenceTracker()

    assert tracker.observe(1) == "first"
    assert tracker.observe(2) == "in_order"
    assert tracker.observe(4) == "gap"
    assert tracker.observe(4) == "duplicate"
    assert tracker.observe(3) == "out_of_order"
