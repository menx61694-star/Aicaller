from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from aicaller.adapters.telephony.exotel_media import ExotelMediaAdapter
from aicaller.adapters.telephony.exotel_stream import (
    ExotelStreamAdapter,
    ExotelStreamEventType,
)
from aicaller.audio.output import AudioOutputFrame, OutboundAudioPipeline
from aicaller.config import settings
from aicaller.domain.call import CallState
from aicaller.services.call_service import CallService

router = APIRouter(tags=["telephony"])
adapter = ExotelStreamAdapter(settings.exotel_api_key, settings.exotel_api_token)
call_service = CallService()


async def flush_outbound_audio(
    websocket: WebSocket,
    pipeline: OutboundAudioPipeline,
    media_adapter: ExotelMediaAdapter,
) -> int:
    """Send all currently contiguous outbound frames to AgentStream.

    The caller owns the pipeline. This helper only drains frames that are
    already queued; it never creates synthetic audio or changes call state.
    """
    sent = 0
    for frame in pipeline.pop_ready():
        message = media_adapter.encode_media(
            frame,
            sequence_number=frame.sequence_number,
            timestamp_ms=frame.timestamp_ms,
        )
        await websocket.send_text(message)
        sent += 1
    return sent


@router.websocket("/ws/exotel/agentstream")
async def exotel_agentstream(websocket: WebSocket) -> None:
    headers = {key.lower(): value for key, value in websocket.headers.items()}
    if not adapter.verify_request(headers):
        await websocket.close(code=1008, reason="invalid telephony authentication")
        return

    await websocket.accept()
    provider_call_id: str | None = None
    stream_sid: str | None = None

    # Connection-local output state prevents audio from one call leaking into
    # another call. No output is generated until a later AI/TTS layer enqueues it.
    outbound_pipeline = OutboundAudioPipeline()
    media_adapter = ExotelMediaAdapter()
    inbound_pipeline = InboundAudioPipeline()

    try:
        while True:
            # Drain only audio explicitly produced by a future realtime layer.
            await flush_outbound_audio(
                websocket,
                outbound_pipeline,
                media_adapter,
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
                    call_service.transition(session.call_id, CallState.RINGING)

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

                # Ordering and bounded packet-loss handling now happen in the
                # provider-neutral audio engine. Codec normalization, VAD and
                # AI consumption remain later stages.
                inbound_frames = inbound_pipeline.ingest(frame)
                _ = inbound_frames

            elif event.event_type is ExotelStreamEventType.DTMF:
                assert event.dtmf is not None
                if (
                    event.dtmf.provider_call_id
                    and provider_call_id
                    and event.dtmf.provider_call_id != provider_call_id
                ):
                    raise ValueError("AgentStream DTMF call id mismatch")
                # DTMF remains at the transport boundary for the future IVR layer.

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
    except (ValueError, UnicodeDecodeError):
        await websocket.close(code=1003, reason="invalid AgentStream event")
