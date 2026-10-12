import pytest

from aicaller.ai.intent_routing_service import IntentRoutingService
from aicaller.ai.session import AITranscriptEvent
from aicaller.domain.call import CallState
from aicaller.services.call_repository import InMemoryCallRepository
from aicaller.services.call_service import CallService
from aicaller.services.intent_call_coordinator import (
    IntentCallCoordinator,
    IntentCallCoordinatorError,
)


def create_call(state: CallState = CallState.RINGING) -> tuple[CallService, str]:
    calls = CallService(InMemoryCallRepository())
    call = calls.create_incoming("call-coordinator-1", "+911234567890")
    calls.transition(call.call_id, CallState.RINGING)
    if state in {CallState.AI_ANSWERING, CallState.AI_CALL}:
        calls.transition(call.call_id, CallState.AI_ANSWERING)
    if state is CallState.AI_CALL:
        calls.transition(call.call_id, CallState.AI_CALL)
    return calls, call.call_id


def event(text: str, sequence: int = 1, stream_sid: str = "stream-1") -> AITranscriptEvent:
    return AITranscriptEvent(
        stream_sid=stream_sid,
        text=text,
        is_final=True,
        sequence=sequence,
    )


def coordinator(call_id: str, calls: CallService) -> IntentCallCoordinator:
    return IntentCallCoordinator(call_id, "stream-1", calls, IntentRoutingService())


def test_urgent_final_transcript_requests_takeover_during_ai_call() -> None:
    calls, call_id = create_call(CallState.AI_CALL)

    result = coordinator(call_id, calls).process_final_event(event("This is an emergency"))

    assert result.call_session.state is CallState.TAKEOVER_REQUESTED
    assert result.state_transitioned
    assert "provider bridge action remains external" in result.state_transition_reason


def test_human_request_during_ringing_moves_to_human_ring_state() -> None:
    calls, call_id = create_call()

    result = coordinator(call_id, calls).process_final_event(
        event("Please connect me to a real person")
    )

    assert result.call_session.state is CallState.HUMAN_CALL
    assert result.state_transitioned
    assert "provider ring action remains external" in result.state_transition_reason


def test_unknown_transcript_does_not_change_call_state() -> None:
    calls, call_id = create_call(CallState.AI_CALL)

    result = coordinator(call_id, calls).process_final_event(
        event("Could you tell me the time?")
    )

    assert result.call_session.state is CallState.AI_CALL
    assert not result.state_transitioned
    assert result.evaluation.decision.requires_confirmation


def test_escalation_in_unsupported_state_is_deferred_without_invalid_transition() -> None:
    calls, call_id = create_call(CallState.AI_ANSWERING)

    result = coordinator(call_id, calls).process_final_event(event("Emergency, help me"))

    assert result.call_session.state is CallState.AI_ANSWERING
    assert not result.state_transitioned
    assert "deferred" in result.state_transition_reason


def test_coordinator_rejects_empty_call_id_or_stream_id() -> None:
    calls, call_id = create_call()

    with pytest.raises(IntentCallCoordinatorError, match="call_id is required"):
        IntentCallCoordinator("", "stream-1", calls, IntentRoutingService())
    with pytest.raises(IntentCallCoordinatorError, match="stream_sid is required"):
        IntentCallCoordinator(call_id, "", calls, IntentRoutingService())


def test_coordinator_rejects_transcript_from_different_stream_without_mutation() -> None:
    calls, call_id = create_call(CallState.AI_CALL)
    service = IntentRoutingService()
    coordinator_instance = IntentCallCoordinator(call_id, "stream-1", calls, service)

    with pytest.raises(IntentCallCoordinatorError, match="does not match"):
        coordinator_instance.process_final_event(
            event("Emergency", stream_sid="another-stream")
        )

    assert calls.get(call_id).state is CallState.AI_CALL
    assert service.intent_store.get().source_sequence == -1
    assert service.policy_store.get().source_sequence == -1


def test_coordinator_rejects_unknown_call() -> None:
    calls = CallService(InMemoryCallRepository())
    coordinator_instance = coordinator("missing", calls)

    with pytest.raises(KeyError, match="missing"):
        coordinator_instance.process_final_event(event("Emergency"))
