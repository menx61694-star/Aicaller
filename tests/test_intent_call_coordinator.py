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


def event(text: str, sequence: int = 1) -> AITranscriptEvent:
    return AITranscriptEvent(
        stream_sid="stream-1",
        text=text,
        is_final=True,
        sequence=sequence,
    )


def test_urgent_final_transcript_requests_takeover_during_ai_call() -> None:
    calls, call_id = create_call(CallState.AI_CALL)
    coordinator = IntentCallCoordinator(call_id, calls, IntentRoutingService())

    result = coordinator.process_final_event(event("This is an emergency"))

    assert result.call_session.state is CallState.TAKEOVER_REQUESTED
    assert result.state_transitioned
    assert "provider bridge action remains external" in result.state_transition_reason


def test_human_request_during_ringing_moves_to_human_ring_state() -> None:
    calls, call_id = create_call()
    coordinator = IntentCallCoordinator(call_id, calls, IntentRoutingService())

    result = coordinator.process_final_event(event("Please connect me to a real person"))

    assert result.call_session.state is CallState.HUMAN_CALL
    assert result.state_transitioned
    assert "provider ring action remains external" in result.state_transition_reason


def test_unknown_transcript_does_not_change_call_state() -> None:
    calls, call_id = create_call(CallState.AI_CALL)
    coordinator = IntentCallCoordinator(call_id, calls, IntentRoutingService())

    result = coordinator.process_final_event(event("Could you tell me the time?"))

    assert result.call_session.state is CallState.AI_CALL
    assert not result.state_transitioned
    assert result.evaluation.decision.requires_confirmation


def test_escalation_in_unsupported_state_is_deferred_without_invalid_transition() -> None:
    calls, call_id = create_call(CallState.AI_ANSWERING)
    coordinator = IntentCallCoordinator(call_id, calls, IntentRoutingService())

    result = coordinator.process_final_event(event("Emergency, help me"))

    assert result.call_session.state is CallState.AI_ANSWERING
    assert not result.state_transitioned
    assert "deferred" in result.state_transition_reason


def test_coordinator_rejects_empty_call_id() -> None:
    calls, _ = create_call()

    with pytest.raises(IntentCallCoordinatorError, match="call_id is required"):
        IntentCallCoordinator("", calls, IntentRoutingService())


def test_coordinator_rejects_unknown_call() -> None:
    calls = CallService(InMemoryCallRepository())
    coordinator = IntentCallCoordinator("missing", calls, IntentRoutingService())

    with pytest.raises(KeyError, match="missing"):
        coordinator.process_final_event(event("Emergency"))
