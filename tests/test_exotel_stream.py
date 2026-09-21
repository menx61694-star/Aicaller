import base64
import json

import pytest

from aicaller.adapters.telephony.base import TelephonyEventType
from aicaller.adapters.telephony.exotel_stream import (
    ExotelStreamAdapter,
    ExotelStreamEventType,
)


def auth_header(key: str, token: str) -> str:
    value = base64.b64encode(f"{key}:{token}".encode()).decode()
    return f"Basic {value}"


def test_exotel_stream_basic_auth() -> None:
    adapter = ExotelStreamAdapter("key", "token")

    assert adapter.verify_request(
        {"authorization": auth_header("key", "token")}
    )
    assert not adapter.verify_request(
        {"authorization": auth_header("key", "wrong")}
    )
    assert not adapter.verify_request({})
    assert not ExotelStreamAdapter("", "").verify_request({})


def test_exotel_start_event_is_parsed_and_correlated() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    payload = {
        "event": "start",
        "stream_sid": "stream-1",
        "start": {
            "stream_sid": "stream-1",
            "call_sid": "call-1",
            "account_sid": "account-1",
            "from": "+919999999999",
            "to": "+911111111111",
            "media_format": {"encoding": "base64", "sample_rate": 8000},
        },
    }

    event = adapter.parse_event(json.dumps(payload).encode())

    assert event.event_type is ExotelStreamEventType.START
    assert event.start is not None
    assert event.start.provider_call_id == "call-1"
    assert event.start.stream_sid == "stream-1"
    assert event.start.caller_number == "+919999999999"
    assert event.start.sample_rate == 8000

    telephony_event = adapter.to_telephony_event(event.start)
    assert telephony_event.event_type is TelephonyEventType.INCOMING_CALL
    assert telephony_event.provider_call_id == "call-1"


def test_media_event_preserves_payload_and_metadata() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    payload = {
        "event": "media",
        "stream_sid": "stream-1",
        "sequence_number": "7",
        "media": {
            "chunk": "3",
            "timestamp": "120",
            "payload": "AQIDBA==",
        },
    }

    event = adapter.parse_event(json.dumps(payload).encode())

    assert event.event_type is ExotelStreamEventType.MEDIA
    assert event.media is not None
    assert event.media.payload == "AQIDBA=="
    assert event.media.sequence_number == "7"
    assert event.media.chunk == "3"
    assert event.media.timestamp == "120"


def test_media_without_payload_is_rejected() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    with pytest.raises(ValueError, match="media payload"):
        adapter.parse_event(b'{"event":"media","media":{}}')


def test_stop_event_preserves_reason() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    payload = {
        "event": "stop",
        "stream_sid": "stream-1",
        "call_sid": "call-1",
        "stop": {"reason": "hangup"},
    }

    event = adapter.parse_event(json.dumps(payload).encode())

    assert event.event_type is ExotelStreamEventType.STOP
    assert event.stop is not None
    assert event.stop.provider_call_id == "call-1"
    assert event.stop.reason == "hangup"


def test_dtmf_event_preserves_digit() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    payload = {
        "event": "dtmf",
        "stream_sid": "stream-1",
        "call_sid": "call-1",
        "dtmf": {"digit": "5"},
    }

    event = adapter.parse_event(json.dumps(payload).encode())

    assert event.event_type is ExotelStreamEventType.DTMF
    assert event.dtmf is not None
    assert event.dtmf.digit == "5"


def test_unknown_event_is_rejected() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    with pytest.raises(ValueError, match="unsupported"):
        adapter.parse_event(b'{"event":"unknown"}')


def test_non_start_event_is_rejected_by_parse_start() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    with pytest.raises(ValueError, match="start event"):
        adapter.parse_start(b'{"event":"media"}')


def test_start_without_call_id_is_rejected() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    payload = {"event": "start", "start": {"stream_sid": "stream-1"}}
    with pytest.raises(ValueError, match="call_sid"):
        adapter.parse_start(json.dumps(payload).encode())
