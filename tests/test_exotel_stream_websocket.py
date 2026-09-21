import base64
import json

from fastapi.testclient import TestClient

from aicaller.adapters.telephony.exotel_stream import ExotelStreamAdapter
from aicaller.main import app
import aicaller.api.routes.exotel_stream as stream_route


def auth_header(key: str, token: str) -> str:
    value = base64.b64encode(f"{key}:{token}".encode()).decode()
    return f"Basic {value}"


def test_agentstream_websocket_accepts_start_media_dtmf_and_stop(monkeypatch) -> None:
    stream_route.adapter = ExotelStreamAdapter("key", "token")

    client = TestClient(app)
    with client.websocket_connect(
        "/api/ws/exotel/agentstream",
        headers={"Authorization": auth_header("key", "token")},
    ) as websocket:
        websocket.send_text(
            json.dumps(
                {
                    "event": "start",
                    "start": {
                        "stream_sid": "stream-1",
                        "call_sid": "call-1",
                        "from": "+919999999999",
                        "to": "+911111111111",
                        "media_format": {"encoding": "base64", "sample_rate": 8000},
                    },
                }
            )
        )
        websocket.send_text(
            json.dumps(
                {
                    "event": "media",
                    "stream_sid": "stream-1",
                    "sequence_number": "1",
                    "media": {"chunk": "1", "timestamp": "0", "payload": "AQID"},
                }
            )
        )
        websocket.send_text(
            json.dumps(
                {
                    "event": "dtmf",
                    "stream_sid": "stream-1",
                    "call_sid": "call-1",
                    "dtmf": {"digit": "5"},
                }
            )
        )
        websocket.send_text(
            json.dumps(
                {
                    "event": "stop",
                    "stream_sid": "stream-1",
                    "call_sid": "call-1",
                    "stop": {"reason": "hangup"},
                }
            )
        )


def test_agentstream_websocket_rejects_invalid_auth() -> None:
    stream_route.adapter = ExotelStreamAdapter("key", "token")

    client = TestClient(app)
    try:
        with client.websocket_connect(
            "/api/ws/exotel/agentstream",
            headers={"Authorization": auth_header("key", "wrong")},
        ):
            raise AssertionError("websocket should have been rejected")
    except Exception as exc:
        assert "1008" in str(exc) or getattr(exc, "code", None) == 1008
