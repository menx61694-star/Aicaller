import base64
import json

import pytest

from aicaller.ai.intent_routing_service import IntentRoutingService
from aicaller.ai.session import RealtimeAISession
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.mulaw import (
    encode_pcm16le_to_mulaw,
    encode_utterance_pcm16le_to_mulaw,
)
from aicaller.audio.utterance import AudioUtterance
from aicaller.domain.call import CallState
from aicaller.services.call_repository import InMemoryCallRepository
from aicaller.services.call_service import CallService
from aicaller.services.intent_call_coordinator import IntentCallCoordinator
from aicaller.services.realtime_call_worker import (
    RealtimeCallWorker,
    RealtimeCallWorkerError,
)
from aicaller.services.realtime_intent_event_handler import RealtimeIntentEventHandler


class FakeRealtimeTransport:
    def __init__(self, incoming: list[str | bytes] | None = None) -> None:
        self.sent: list[str] = []
        self.incoming = list(incoming or [])

    async def send(self, payload: str) -> None:
        self.sent.append(payload)

    async def receive(self) -> str | bytes:
        if not self.incoming:
            raise RuntimeError("no queued realtime event")
        return self.incoming.pop(0)


def make_worker(incoming: list[str | bytes] | None = None, *, use_mulaw: bool = False):
    calls = CallService(InMemoryCallRepository())
    call = calls.create_incoming("call-worker-1", "+911")
    calls.transition(call.call_id, CallState.RINGING)
    calls.transition(call.call_id, CallState.AI_ANSWERING)
    calls.transition(call.call_id, CallState.AI_CALL)
    session = RealtimeAISession("worker-stream-1")
    routing = IntentRoutingService()
    coordinator = IntentCallCoordinator(
        call.call_id,
        session.stream_sid,
        calls,
        routing,
    )
    handler = RealtimeIntentEventHandler(session, coordinator)
    transport = FakeRealtimeTransport(incoming)
    encoder = encode_utterance_pcm16le_to_mulaw if use_mulaw else None
    return RealtimeCallWorker(session, handler, transport, encoder), transport, calls, call.call_id


def sample_utterance(stream_sid: str = "worker-stream-1") -> AudioUtterance:
    audio_format = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    frame = NormalizedAudioFrame(stream_sid, 1, 20, b"\x01\x02", audio_format)
    return AudioUtterance(stream_sid, (frame,), 20, 40)


@pytest.mark.asyncio
async def test_worker_sends_audio_append_then_commit() -> None:
    worker, transport, _, _ = make_worker()

    await worker.send_utterance(sample_utterance())

    assert len(transport.sent) == 2
    append, commit = map(json.loads, transport.sent)
    assert append["type"] == "input_audio_buffer.append"
    assert base64.b64decode(append["audio"]) == b"\x01\x02"
    assert commit["type"] == "input_audio_buffer.commit"


@pytest.mark.asyncio
async def test_worker_can_encode_pcm16_8khz_to_mulaw_for_openai_transport() -> None:
    worker, transport, _, _ = make_worker(use_mulaw=True)

    await worker.send_utterance(sample_utterance())

    append = json.loads(transport.sent[0])
    assert base64.b64decode(append["audio"]) == encode_pcm16le_to_mulaw(b"\x01\x02")
    assert len(base64.b64decode(append["audio"])) == 1
    assert json.loads(transport.sent[1])["type"] == "input_audio_buffer.commit"


@pytest.mark.asyncio
async def test_worker_rejects_utterance_from_another_stream() -> None:
    worker, transport, _, _ = make_worker()

    with pytest.raises(RealtimeCallWorkerError, match="does not match"):
        await worker.send_utterance(sample_utterance("foreign-stream"))

    assert transport.sent == []


@pytest.mark.asyncio
async def test_worker_routes_final_transcript_from_transport() -> None:
    final_event = json.dumps(
        {
            "type": "conversation.item.input_audio_transcription.completed",
            "transcript": "This is an emergency",
            "language": "en",
        }
    )
    worker, _, calls, call_id = make_worker([final_event])

    result = await worker.receive_and_route()

    assert result is not None
    assert result.call_session.state is CallState.TAKEOVER_REQUESTED
    assert calls.get(call_id).state is CallState.TAKEOVER_REQUESTED


@pytest.mark.asyncio
async def test_worker_does_not_route_partial_transcript() -> None:
    partial_event = json.dumps(
        {
            "type": "conversation.item.input_audio_transcription.delta",
            "delta": "This is an emergency",
        }
    )
    worker, _, calls, call_id = make_worker([partial_event])

    result = await worker.receive_and_route()

    assert result is None
    assert calls.get(call_id).state is CallState.AI_CALL


@pytest.mark.asyncio
async def test_worker_surfaces_transport_receive_failure() -> None:
    worker, _, _, _ = make_worker()

    with pytest.raises(RealtimeCallWorkerError, match="failed to receive"):
        await worker.receive_and_route()
