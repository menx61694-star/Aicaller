from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

from aicaller.adapters.telephony.exotel_stream import (
    ExotelStreamAdapter,
    ExotelStreamEventType,
)
from aicaller.config import settings
from aicaller.domain.call import CallState
from aicaller.services.call_service import CallService

router = APIRouter(tags=["telephony"])
adapter = ExotelStreamAdapter(settings.exotel_api_key, settings.exotel_api_token)
call_service = CallService()


@router.post("/webhooks/telephony")
async def telephony_webhook(request: Request) -> dict[str, str]:
    from aicaller.adapters.telephony.exotel import ExotelAdapter

    http_adapter = ExotelAdapter()
    payload = await request.body()
    headers = {key.lower(): value for key, value in request.headers.items()}

    if not http_adapter.verify_request(payload, headers):
        raise HTTPException(status_code=401, detail="invalid telephony signature")

    event = http_adapter.parse_event(payload, headers)
    if not event.provider_call_id:
        raise HTTPException(status_code=400, detail="missing provider call id")

    if event.event_type is event.event_type.INCOMING_CALL:
        session = call_service.create_incoming(event.provider_call_id, event.caller_number)
        call_service.transition(session.call_id, CallState.RINGING)
    elif event.event_type is event.event_type.HANGUP:
        session = call_service.get(event.provider_call_id)
        if session and session.state not in {CallState.CALL_ENDED, CallState.POST_PROCESSING}:
            if session.state in {
                CallState.AI_CALL,
                CallState.HUMAN_CALL,
                CallState.FAILURE,
            }:
                call_service.transition(session.call_id, CallState.CALL_ENDED)

    return {"status": "accepted"}


@router.websocket("/ws/exotel/agentstream")
async def exotel_agentstream(websocket: WebSocket) -> None:
    headers = {key.lower(): value for key, value in websocket.headers.items()}
    if not adapter.verify_request(headers):
        await websocket.close(code=1008, reason="invalid telephony authentication")
        return

    await websocket.accept()
    provider_call_id: str | None = None
    stream_sid: str | None = None

    try:
        while True:
            payload = await websocket.receive_bytes()
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
                # Audio payload is intentionally preserved but not decoded here.
                # Phase 2 audio processing consumes this boundary.

            elif event.event_type is ExotelStreamEventType.DTMF:
                assert event.dtmf is not None
                if (
                    event.dtmf.provider_call_id
                    and provider_call_id
                    and event.dtmf.provider_call_id != provider_call_id
                ):
                    raise ValueError("AgentStream DTMF call id mismatch")
                # DTMF is retained at the adapter boundary for the future IVR layer.

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
    finally:
        # Stream termination is intentionally not treated as a call hangup.
        # The authoritative call lifecycle remains driven by telephony events.
        pass
