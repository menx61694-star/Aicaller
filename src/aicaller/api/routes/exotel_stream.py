from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from aicaller.adapters.telephony.exotel import ExotelAdapter
from aicaller.adapters.telephony.exotel_media import ExotelMediaAdapter
from aicaller.adapters.telephony.exotel_stream import (
    ExotelStreamAdapter,
    ExotelStreamEventType,
)
from aicaller.ai.openai_realtime_transport import (
    OpenAIRealtimeTranscriptionTransport,
    OpenAIRealtimeTransportError,
)
from aicaller.ai.session import RealtimeAISession
from aicaller.audio.aec import NLMSAcousticEchoCanceller
from aicaller.audio.aec_reference import AECReferenceBuffer
from aicaller.audio.agc import AGCConfig, AutomaticGainController
from aicaller.audio.format import AudioEncoding, AudioFormat, AudioNormalizer
from aicaller.audio.frame import AudioFrameError, decode_base64_audio
from aicaller.audio.mulaw import encode_utterance_pcm16le_to_mulaw
from aicaller.audio.noise_suppression import (
    AdaptiveNoiseSuppressor,
    NoiseSuppressionConfig,
)
from aicaller.audio.output import OutboundAudioPipeline
from aicaller.audio.pipeline import InboundAudioPipeline
from aicaller.audio.utterance import UtteranceBuffer
from aicaller.audio.vad import EnergyVAD, VADConfig
from aicaller.config import settings
from aicaller.domain.call import CallState
from aicaller.services.call_repository import InMemoryCallRepository
from aicaller.services.call_service import CallService
from aicaller.services.intent_call_coordinator import IntentCallCoordinator
from aicaller.ai.intent_routing_service import IntentRoutingService
from aicaller.services.realtime_call_worker import (
    RealtimeCallWorker,
    RealtimeCallWorkerError,
)
from aicaller.services.realtime_intent_event_handler import RealtimeIntentEventHandler

logger = logging.getLogger(__name__)

router = APIRouter(tags=["telephony"])
adapter = ExotelStreamAdapter(settings.exotel_api_key, settings.exotel_api_token)
call_service = CallService(InMemoryCallRepository())


async def flush_outbound_audio(
    websocket: WebSocket,
    pipeline: OutboundAudioPipeline,
    media_adapter: ExotelMediaAdapter,
    reference_buffer: AECReferenceBuffer,
    audio_format: AudioFormat | None,
) -> int:
    """Send all currently contiguous outbound frames to AgentStream."""
    sent = 0
    for frame in pipeline.pop_ready():
        message = media_adapter.encode_media(
            frame,
            sequence_number=frame.sequence_number,
            timestamp_ms=frame.timestamp_ms,
        )
        await websocket.send_text(message)
        if audio_format is not None:
            reference_buffer.add(frame, audio_format)
        sent += 1
    return sent


async def consume_realtime_events(worker: RealtimeCallWorker, call_id: str) -> None:
    """Read provider events until disconnect/error and log routing outcomes."""
    while True:
        try:
            result = await worker.receive_and_route()
        except RealtimeCallWorkerError:
            logger.exception("realtime transcription worker stopped", extra={"call_id": call_id})
            return
        if result is None:
            continue
        logger.info(
            "realtime intent routing evaluated",
            extra={
                "call_id": call_id,
                "intent": result.evaluation.classification.intent.value,
                "confidence": result.evaluation.classification.confidence,
                "routing_action": result.evaluation.decision.action.value,
                "call_state": result.call_session.state.value,
                "state_transitioned": result.state_transitioned,
                "routing_reason": result.state_transition_reason,
            },
        )


@router.websocket("/ws/exotel/agentstream")
async def exotel_agentstream(websocket: WebSocket) -> None:
    headers = {key.lower(): value for key, value in websocket.headers.items()}
    if not adapter.verify_request(headers):
        await websocket.close(code=1008, reason="invalid telephony authentication")
        return

    await websocket.accept()
    provider_call_id: str | None = None
    stream_sid: str | None = None
    realtime_transport: OpenAIRealtimeTranscriptionTransport | None = None
    realtime_reader_task: asyncio.Task[None] | None = None
    realtime_worker: RealtimeCallWorker | None = None

    # All audio and AI state is scoped to this WebSocket/call.
    outbound_pipeline = OutboundAudioPipeline()
    media_adapter = ExotelMediaAdapter()
    inbound_pipeline = InboundAudioPipeline()
    inbound_normalizer: AudioNormalizer | None = None
    vad = EnergyVAD(VADConfig())
    aec_reference = AECReferenceBuffer()
    aec = NLMSAcousticEchoCanceller()
    noise_suppressor = AdaptiveNoiseSuppressor(NoiseSuppressionConfig())
    agc = AutomaticGainController(AGCConfig())
    utterance_buffer = UtteranceBuffer()

    try:
        while True:
            await flush_outbound_audio(
                websocket,
                outbound_pipeline,
                media_adapter,
                aec_reference,
                inbound_normalizer.target_format if inbound_normalizer else None,
            )

            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                return

            raw_bytes = message.get("bytes")
            raw_text = message.get("text")
            if raw_bytes is not None:
                payload = raw_bytes
            elif raw_text is not None:
                payload = raw_text.encode("utf-8")
            else:
                raise ValueError("AgentStream message has no payload")

            event = adapter.parse_event(payload)

            if event.event_type is ExotelStreamEventType.START:
                if provider_call_id is not None:
                    raise ValueError("duplicate AgentStream start event")
                assert event.start is not None
                provider_call_id = event.start.provider_call_id
                stream_sid = event.start.stream_sid
                session = call_service.create_incoming(
                    provider_call_id,
                    event.start.caller_number,
                )
                if session.state is CallState.INCOMING:
                    session = call_service.transition(session.call_id, CallState.RINGING)

                if event.start.sample_rate is None:
                    raise ValueError("AgentStream start is missing sample rate")
                if event.start.encoding not in {None, "base64"}:
                    raise ValueError(
                        f"unsupported AgentStream encoding: {event.start.encoding}"
                    )
                source_format = AudioFormat(
                    AudioEncoding.PCM16_LE,
                    event.start.sample_rate,
                    channels=1,
                    sample_width_bytes=2,
                )
                inbound_normalizer = AudioNormalizer(source_format)

                # Live transcription is optional in development/test mode. If
                # enabled, the stream must be 8 kHz PCM16 so it can be explicitly
                # converted to G.711 μ-law for OpenAI's telephony input format.
                if settings.openai_api_key:
                    if event.start.sample_rate != 8000:
                        raise ValueError(
                            "OpenAI telephony transcription requires 8000 Hz input"
                        )
                    realtime_transport = await OpenAIRealtimeTranscriptionTransport.connect(
                        settings.openai_api_key
                    )
                    assert stream_sid is not None
                    realtime_session = RealtimeAISession(stream_sid)
                    routing_service = IntentRoutingService()
                    coordinator = IntentCallCoordinator(
                        provider_call_id,
                        stream_sid,
                        call_service,
                        routing_service,
                        human_escalation_adapter=ExotelAdapter(),
                        human_destination=settings.human_phone_number,
                    )
                    event_handler = RealtimeIntentEventHandler(
                        realtime_session,
                        coordinator,
                    )
                    realtime_worker = RealtimeCallWorker(
                        realtime_session,
                        event_handler,
                        realtime_transport,
                        audio_encoder=encode_utterance_pcm16le_to_mulaw,
                    )
                    current = call_service.get(provider_call_id)
                    if current is not None and current.state is CallState.RINGING:
                        call_service.transition(provider_call_id, CallState.AI_ANSWERING)
                        call_service.transition(provider_call_id, CallState.AI_CALL)
                    realtime_reader_task = asyncio.create_task(
                        consume_realtime_events(realtime_worker, provider_call_id)
                    )

            elif event.event_type is ExotelStreamEventType.MEDIA:
                assert event.media is not None
                if (
                    event.media.provider_call_id
                    and provider_call_id
                    and event.media.provider_call_id != provider_call_id
                ):
                    raise ValueError("AgentStream media call id mismatch")
                if (
                    event.media.stream_sid
                    and stream_sid
                    and event.media.stream_sid != stream_sid
                ):
                    raise ValueError("AgentStream media stream id mismatch")
                try:
                    frame = decode_base64_audio(
                        stream_sid=event.media.stream_sid or stream_sid,
                        sequence_number=event.media.sequence_number,
                        timestamp=event.media.timestamp,
                        payload=event.media.payload,
                    )
                except AudioFrameError as exc:
                    raise ValueError(str(exc)) from exc

                inbound_frames = inbound_pipeline.ingest(frame)
                if inbound_normalizer is None:
                    raise ValueError("audio format is not initialized")
                normalized_frames = [
                    inbound_normalizer.normalize(item, inbound_normalizer.target_format)
                    for item in inbound_frames
                ]
                for normalized in normalized_frames:
                    reference = aec_reference.find_aligned(
                        stream_sid=normalized.stream_sid,
                        sequence_number=normalized.sequence_number,
                    )
                    aec_frame = (
                        aec.process(near_end=normalized, far_end_reference=reference)
                        if reference is not None
                        else normalized
                    )
                    denoised_frame = noise_suppressor.process(aec_frame)
                    normalized_level_frame = agc.process(denoised_frame)
                    vad_result = vad.process(normalized_level_frame)
                    utterance = utterance_buffer.process(normalized_level_frame, vad_result)
                    if utterance is not None and realtime_worker is not None:
                        await realtime_worker.send_utterance(utterance)

            elif event.event_type is ExotelStreamEventType.DTMF:
                assert event.dtmf is not None
                if (
                    event.dtmf.provider_call_id
                    and provider_call_id
                    and event.dtmf.provider_call_id != provider_call_id
                ):
                    raise ValueError("AgentStream DTMF call id mismatch")

            elif event.event_type is ExotelStreamEventType.STOP:
                assert event.stop is not None
                if (
                    event.stop.provider_call_id
                    and provider_call_id
                    and event.stop.provider_call_id != provider_call_id
                ):
                    raise ValueError("AgentStream stop call id mismatch")
                break

    except WebSocketDisconnect:
        return
    except OpenAIRealtimeTransportError:
        logger.exception("could not initialize OpenAI realtime transcription")
        await websocket.close(code=1011, reason="AI realtime initialization failed")
    except RealtimeCallWorkerError:
        logger.exception("OpenAI realtime call worker failed")
        await websocket.close(code=1011, reason="AI realtime worker failed")
    except (ValueError, UnicodeDecodeError):
        await websocket.close(code=1003, reason="invalid AgentStream event")
    finally:
        if realtime_reader_task is not None:
            realtime_reader_task.cancel()
            with suppress(asyncio.CancelledError):
                await realtime_reader_task
        if realtime_transport is not None:
            await realtime_transport.close()
