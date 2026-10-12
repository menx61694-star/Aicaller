import json

import pytest

from aicaller.ai.intent_routing_service import IntentRoutingService
from aicaller.ai.session import RealtimeAISession
from aicaller.domain.call import CallState
from aicaller.services.call_repository import InMemoryCallRepository
from aicaller.services.call_service import CallService
from aicaller.services.intent_call_coordinator import IntentCallCoordinator
from aicaller.services.realtime_intent_event_handler import (
    RealtimeIntentEventHandler,
    RealtimeIntentEventHandlerError,
)


def make_handler(state: CallState = CallState.AI_CALL):
    calls = CallService(InMemoryCallRepository())
    call = calls.create_incoming("call-realtime-intent", "+911234567890")
    calls.transition(call.call_id, CallState.RINGING)
    if state in {CallState.AI_ANSWERING, CallState.AI_CALL}:
        calls.transition(call.call_id, CallState.AI_ANSWERING)
    if state is CallState.AI_CALL:
        calls.transition(call.call_id, CallState.AI_CALL)
    routing = IntentRoutingService()
    session = RealtimeAISession("stream-rt-1")
    coordinator = IntentCallCoordinator(
        call.call_id,
        "stream-rt-1",
        calls,
        routing,
    )
    return RealtimeIntentEventHandler(session, coordinator), calls, call.call_id, routing


def test_final_realtime_urgent_transcript_requests_takeover() -> None:
    handler, calls, call_id, routing = make_handler()
    payload = json.dumps(
        {
            "type": "conversation.item.input_audio_transcription.completed",
            "transcript": "This is an emergency, help me",
            "language": "en",
        }
    )

    result = handler.handle(payload)

    assert result is not None
    assert result.call_session.state is CallState.TAKEOVER_REQUESTED
    assert result.evaluation.intent_context.source_sequence == 1
    assert routing.policy_store.get().action.value == "request_human"
    assert calls.get(call_id).state is CallState.TAKEOVER_REQUESTED


def test_partial_transcript_updates_session_but_never_routes_call() -> None:
    handler, calls, call_id, routing = make_handler()
    payload = json.dumps(
        {
            "type": "conversation.item.input_audio_transcription.delta",
            "delta": "This is an emergency",
        }
    )

    result = handler.handle(payload)

    assert result is None
    assert calls.get(call_id).state is CallState.AI_CALL
    assert routing.intent_store.get().source_sequence == -1
    assert routing.policy_store.get().source_sequence == -1


def test_non_transcript_realtime_events_are_ignored() -> None:
    handler, calls, call_id, routing = make_handler()

    result = handler.handle(json.dumps({"type": "response.created"}))

    assert result is None
    assert calls.get(call_id).state is CallState.AI_CALL
    assert routing.intent_store.get().source_sequence == -1


def test_handler_rejects_mismatched_session_and_call_stream() -> None:
    calls = CallService(InMemoryCallRepository())
    call = calls.create_incoming("call-stream-mismatch", "+911")
    coordinator = IntentCallCoordinator(
        call.call_id,
        "expected-stream",
        calls,
        IntentRoutingService(),
    )

    with pytest.raises(RealtimeIntentEventHandlerError, match="stream ids do not match"):
        RealtimeIntentEventHandler(RealtimeAISession("other-stream"), coordinator)


def test_handler_rejects_malformed_realtime_event() -> None:
    handler, _, _, _ = make_handler()

    with pytest.raises(RealtimeIntentEventHandlerError, match="invalid realtime JSON"):
        handler.handle("{not-json")
