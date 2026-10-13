import asyncio
import base64
import json
import time

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

import aicaller.api.routes.exotel_stream as stream_route
from aicaller.adapters.telephony.exotel_stream import ExotelStreamAdapter
from aicaller.audio.utterance import AudioUtterance
from aicaller.main import app


def auth_header(key: str, token: str) -> str:
    value = base64.b64encode(f"{key}:{token}".encode()).decode()
    return f"Basic {value}"


def test_agentstream_websocket_accepts_start_media_dtmf_and_stop() -> None:
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
    with pytest.raises(WebSocketDisconnect) as exc_info, client.websocket_connect(
        "/api/ws/exotel/agentstream",
        headers={"Authorization": auth_header("key", "wrong")},
    ):
        raise AssertionError("websocket should have been rejected")
    assert exc_info.value.code == 1008


def test_agentstream_hands_completed_utterance_to_openai_worker(monkeypatch) -> None:
    stream_route.adapter = ExotelStreamAdapter("key", "token")
    monkeypatch.setattr(stream_route.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(stream_route.settings, "human_phone_number", "")

    class FakeRealtimeTransport:
        def __init__(self) -> None:
            self.sent: list[str] = []
            self.committed = asyncio.Event()
            self.closed = False

        async def send(self, payload: str) -> None:
            self.sent.append(payload)
            if json.loads(payload)["type"] == "input_audio_buffer.commit":
                self.committed.set()

        async def receive(self) -> str:
            await self.committed.wait()
            await asyncio.Future()

        async def close(self) -> None:
            self.closed = True

    fake_transport = FakeRealtimeTransport()

    class FakeTransportFactory:
        @classmethod
        async def connect(cls, api_key: str):
            assert api_key == "test-key"
            return fake_transport

    class OneFrameUtteranceBuffer:
        def __init__(self) -> None:
            self.emitted = False

        def process(self, frame, vad_result):
            if self.emitted:
                return None
            self.emitted = True
            return AudioUtterance(
                frame.stream_sid,
                (frame,),
                frame.timestamp_ms,
                (frame.timestamp_ms or 0) + 20,
            )

    monkeypatch.setattr(
        stream_route,
        "OpenAIRealtimeTranscriptionTransport",
        FakeTransportFactory,
    )
    monkeypatch.setattr(stream_route, "UtteranceBuffer", OneFrameUtteranceBuffer)

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
                        "stream_sid": "stream-live-worker",
                        "call_sid": "call-live-worker",
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
                    "stream_sid": "stream-live-worker",
                    "sequence_number": "1",
                    "media": {"chunk": "1", "timestamp": "0", "payload": "AQI="},
                }
            )
        )
        websocket.send_text(
            json.dumps(
                {
                    "event": "stop",
                    "stream_sid": "stream-live-worker",
                    "call_sid": "call-live-worker",
                    "stop": {"reason": "hangup"},
                }
            )
        )

    assert [json.loads(payload)["type"] for payload in fake_transport.sent] == [
        "input_audio_buffer.append",
        "input_audio_buffer.commit",
    ]
    encoded_audio = json.loads(fake_transport.sent[0])["audio"]
    assert len(base64.b64decode(encoded_audio)) == 1
    assert fake_transport.closed



def test_agentstream_routes_final_urgent_transcript_through_coordinator(monkeypatch) -> None:
    stream_route.adapter = ExotelStreamAdapter("key", "token")
    monkeypatch.setattr(stream_route.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(stream_route.settings, "human_phone_number", "+911234567890")

    class FakeRealtimeTransport:
        def __init__(self) -> None:
            self.sent: list[str] = []
            self.committed = asyncio.Event()
            self.final_sent = False
            self.closed = False

        async def send(self, payload: str) -> None:
            self.sent.append(payload)
            if json.loads(payload)["type"] == "input_audio_buffer.commit":
                self.committed.set()

        async def receive(self) -> str:
            await self.committed.wait()
            if not self.final_sent:
                self.final_sent = True
                return json.dumps(
                    {
                        "type": "conversation.item.input_audio_transcription.completed",
                        "transcript": "This is an emergency, please send a human",
                        "language": "en",
                    }
                )
            await asyncio.Future()

        async def close(self) -> None:
            self.closed = True

    fake_transport = FakeRealtimeTransport()

    class FakeTransportFactory:
        @classmethod
        async def connect(cls, api_key: str):
            assert api_key == "test-key"
            return fake_transport

    escalation_actions: list[tuple[str, str, str]] = []

    class FakeHumanEscalationAdapter:
        def start_human_ring(self, provider_call_id: str, destination: str) -> None:
            assert provider_call_id == "call-live-routing"
            assert destination == "+911234567890"
            escalation_actions.append(("ring", provider_call_id, destination))

        def request_human_takeover(self, provider_call_id: str, destination: str) -> None:
            assert provider_call_id == "call-live-routing"
            assert destination == "+911234567890"
            escalation_actions.append(("takeover", provider_call_id, destination))

    class OneFrameUtteranceBuffer:
        def __init__(self) -> None:
            self.emitted = False

        def process(self, frame, vad_result):
            if self.emitted:
                return None
            self.emitted = True
            return AudioUtterance(
                frame.stream_sid,
                (frame,),
                frame.timestamp_ms,
                (frame.timestamp_ms or 0) + 20,
            )

    monkeypatch.setattr(
        stream_route,
        "OpenAIRealtimeTranscriptionTransport",
        FakeTransportFactory,
    )
    monkeypatch.setattr(stream_route, "ExotelAdapter", FakeHumanEscalationAdapter)
    monkeypatch.setattr(stream_route, "UtteranceBuffer", OneFrameUtteranceBuffer)

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
                        "stream_sid": "stream-live-routing",
                        "call_sid": "call-live-routing",
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
                    "stream_sid": "stream-live-routing",
                    "sequence_number": "1",
                    "media": {"chunk": "1", "timestamp": "0", "payload": "AQI="},
                }
            )
        )

        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            call = stream_route.call_service.get("call-live-routing")
            if call is not None and call.state.value == "TAKEOVER_REQUESTED":
                break
            time.sleep(0.01)
        else:
            pytest.fail("final urgent transcript did not reach the call coordinator")

        websocket.send_text(
            json.dumps(
                {
                    "event": "stop",
                    "stream_sid": "stream-live-routing",
                    "call_sid": "call-live-routing",
                    "stop": {"reason": "hangup"},
                }
            )
        )

    assert stream_route.call_service.get("call-live-routing").state.value == "TAKEOVER_REQUESTED"
    assert fake_transport.closed
    assert escalation_actions == [("takeover", "call-live-routing", "+911234567890")]
