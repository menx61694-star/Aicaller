import base64
import json

import pytest

from aicaller.adapters.telephony.exotel_media import (
    ExotelMediaAdapter,
    ExotelMediaConfig,
    ExotelMediaError,
)
from aicaller.audio.output import AudioOutputFrame


def frame(payload: bytes = b"x" * 320) -> AudioOutputFrame:
    return AudioOutputFrame("stream-1", 7, payload, 100)


def test_encode_media_creates_bidirectional_agentstream_event() -> None:
    message = json.loads(
        ExotelMediaAdapter().encode_media(frame(), sequence_number=8)
    )
    assert message["event"] == "media"
    assert message["stream_sid"] == "stream-1"
    assert message["sequence_number"] == 8
    assert message["media"]["chunk"] == 7
    assert message["media"]["timestamp"] == "100"
    assert base64.b64decode(message["media"]["payload"]) == b"x" * 320


def test_encode_media_rejects_invalid_chunk_size() -> None:
    adapter = ExotelMediaAdapter()
    with pytest.raises(ExotelMediaError):
        adapter.encode_media(frame(b"x" * 321), sequence_number=8)


def test_encode_media_supports_configured_chunk_bounds() -> None:
    adapter = ExotelMediaAdapter(
        ExotelMediaConfig(min_chunk_bytes=160, required_chunk_multiple=160)
    )
    message = json.loads(
        adapter.encode_media(frame(b"x" * 160), sequence_number=8)
    )
    assert message["media"]["payload"]


def test_encode_mark() -> None:
    message = json.loads(
        ExotelMediaAdapter().encode_mark("stream-1", sequence_number=9, name="tts-1")
    )
    assert message["event"] == "mark"
    assert message["mark"]["name"] == "tts-1"


def test_encode_clear() -> None:
    message = json.loads(ExotelMediaAdapter().encode_clear("stream-1"))
    assert message == {"event": "clear", "stream_sid": "stream-1"}
