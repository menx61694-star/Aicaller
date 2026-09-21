from fastapi import APIRouter, HTTPException, Request

from aicaller.adapters.telephony.exotel import ExotelAdapter
from aicaller.domain.call import CallState
from aicaller.services.call_service import CallService

router = APIRouter(tags=["telephony"])
adapter = ExotelAdapter()
call_service = CallService()


@router.post("/webhooks/telephony")
async def telephony_webhook(request: Request) -> dict[str, str]:
    payload = await request.body()
    headers = {key.lower(): value for key, value in request.headers.items()}

    if not adapter.verify_request(payload, headers):
        raise HTTPException(status_code=401, detail="invalid telephony signature")

    event = adapter.parse_event(payload, headers)
    if not event.provider_call_id:
        raise HTTPException(status_code=400, detail="missing provider call id")

    if event.event_type is event.event_type.INCOMING_CALL:
        session = call_service.create_incoming(event.provider_call_id, event.caller_number)
        call_service.transition(session.call_id, CallState.RINGING)
    elif event.event_type is event.event_type.HANGUP:
        session = call_service.get(event.provider_call_id)
        if session and session.state not in {CallState.CALL_ENDED, CallState.POST_PROCESSING}:
            call_service.transition(session.call_id, CallState.CALL_ENDED)

    return {"status": "accepted"}
