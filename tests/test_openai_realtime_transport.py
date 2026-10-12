import json

import pytest

import aicaller.ai.openai_realtime_transport as realtime_transport
from aicaller.ai.openai_realtime_transport import (
    OpenAIRealtimeTranscriptionTransport,
    OpenAIRealtimeTransportError,
)


class FakeSocket:
    def __init__(self, events: list[str]) -> None:
        self.events = list(events)
        self.sent: list[str] = []
        self.closed = False

    async def send(self, payload: str) -> None:
        self.sent.append(payload)

    async def recv(self) -> str:
        if not self.events:
            raise RuntimeError("no event queued")
        return self.events.pop(0)

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_connect_authenticates_and_configures_pcmu_transcription(monkeypatch) -> None:
    socket = FakeSocket(
        [
            json.dumps({"type": "session.created"}),
            json.dumps({"type": "session.updated"}),
        ]
    )
    captured: dict[str, object] = {}

    async def fake_connect(uri: str, **kwargs):
        captured["uri"] = uri
        captured["kwargs"] = kwargs
        return socket

    monkeypatch.setattr(realtime_transport, "connect", fake_connect)

    transport = await OpenAIRealtimeTranscriptionTransport.connect(
        "secret-api-key",
        languages=("en", "hi"),
    )

    assert isinstance(transport, OpenAIRealtimeTranscriptionTransport)
    assert captured["uri"] == (
        "wss://api.openai.com/v1/realtime?model=gpt-realtime-2.1"
    )
    kwargs = captured["kwargs"]
    assert kwargs["additional_headers"] == {
        "Authorization": "Bearer secret-api-key"
    }
    assert len(socket.sent) == 1
    update = json.loads(socket.sent[0])
    assert update["type"] == "session.update"
    assert update["session"]["type"] == "transcription"
    audio_input = update["session"]["audio"]["input"]
    assert audio_input["format"] == {"type": "audio/pcmu"}
    assert audio_input["transcription"] == {
        "model": "gpt-live-transcribe",
        "languages": ["en", "hi"],
    }
    assert audio_input["turn_detection"] is None
    assert not socket.closed
    await transport.close()
    assert socket.closed


@pytest.mark.asyncio
async def test_connect_rejects_missing_api_key_before_network(monkeypatch) -> None:
    async def forbidden_connect(*args, **kwargs):
        raise AssertionError("network should not be opened")

    monkeypatch.setattr(realtime_transport, "connect", forbidden_connect)

    with pytest.raises(OpenAIRealtimeTransportError, match="API key is required"):
        await OpenAIRealtimeTranscriptionTransport.connect("  ")


@pytest.mark.asyncio
async def test_provider_error_closes_socket_and_fails_initialization(monkeypatch) -> None:
    socket = FakeSocket(
        [
            json.dumps({"type": "session.created"}),
            json.dumps({"type": "error", "error": {"message": "invalid model"}}),
        ]
    )

    async def fake_connect(uri: str, **kwargs):
        return socket

    monkeypatch.setattr(realtime_transport, "connect", fake_connect)

    with pytest.raises(OpenAIRealtimeTransportError, match="invalid model"):
        await OpenAIRealtimeTranscriptionTransport.connect("key")

    assert socket.closed


@pytest.mark.asyncio
async def test_malformed_provider_handshake_closes_socket(monkeypatch) -> None:
    socket = FakeSocket(["not-json"])

    async def fake_connect(uri: str, **kwargs):
        return socket

    monkeypatch.setattr(realtime_transport, "connect", fake_connect)

    with pytest.raises(OpenAIRealtimeTransportError, match="invalid JSON"):
        await OpenAIRealtimeTranscriptionTransport.connect("key")

    assert socket.closed
