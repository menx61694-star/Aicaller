import json

from aicaller.adapters.telephony.base import TelephonyEventType
from aicaller.adapters.telephony.exotel import ExotelAdapter


def test_parse_incoming_event():
    adapter = ExotelAdapter()
    payload = json.dumps({"event_type": "INCOMING_CALL", "call_id": "ex-1", "caller_number": "+91123"}).encode()
    event = adapter.parse_event(payload, {})
    assert event.event_type is TelephonyEventType.INCOMING_CALL
    assert event.provider_call_id == "ex-1"
    assert event.caller_number == "+91123"


def test_exotel_adapter_is_fail_closed_before_auth_config():
    assert ExotelAdapter().verify_request(b"{}", {}) is False
