import base64
import json

import pytest

from aicaller.adapters.telephony.base import TelephonyEventType
from aicaller.adapters.telephony.exotel_stream import ExotelStreamAdapter


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

    start = adapter.parse_start(json.dumps(payload).encode())
    event = adapter.to_telephony_event(start)

    assert start.provider_call_id == "call-1"
    assert start.stream_sid == "stream-1"
    assert start.caller_number == "+919999999999"
    assert start.sample_rate == 8000
    assert event.event_type is TelephonyEventType.INCOMING_CALL
    assert event.provider_call_id == "call-1"


def test_non_start_event_is_rejected() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    with pytest.raises(ValueError, match="start event"):
        adapter.parse_start(b'{"event":"media"}')


def test_start_without_call_id_is_rejected() -> None:
    adapter = ExotelStreamAdapter("key", "token")
    payload = {"event": "start", "start": {"stream_sid": "stream-1"}}
    with pytest.raises(ValueError, match="call_sid"):
        adapter.parse_start(json.dumps(payload).encode())
