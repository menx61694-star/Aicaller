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


class FakeHumanEscalationAdapter:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.actions: list[tuple[str, str, str]] = []

    def start_human_ring(self, provider_call_id: str, destination: str) -> None:
        if self.fail:
            raise RuntimeError("provider rejected ring")
        self.actions.append(("ring", provider_call_id, destination))

    def request_human_takeover(self, provider_call_id: str, destination: str) -> None:
        if self.fail:
            raise RuntimeError("provider rejected takeover")
        self.actions.append(("takeover", provider_call_id, destination))


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


def coordinator(
    call_id: str,
    calls: CallService,
    adapter: FakeHumanEscalationAdapter | None = None,
) -> IntentCallCoordinator:
    return IntentCallCoordinator(
        call_id,
        "stream-1",
        calls,
        IntentRoutingService(),
        human_escalation_adapter=adapter or FakeHumanEscalationAdapter(),
        human_destination="+911234567890",
    )


def test_urgent_final_transcript_requests_takeover_after_provider_accepts() -> None:
    calls, call_id = create_call(CallState.AI_CALL)
    adapter = FakeHumanEscalationAdapter()

    result = coordinator(call_id, calls, adapter).process_final_event(
        event("This is an emergency")
    )

    assert result.call_session.state is CallState.TAKEOVER_REQUESTED
    assert result.state_transitioned
    assert adapter.actions == [("takeover", call_id, "+911234567890")]
    assert result.state_transition_reason == "provider accepted human-takeover action"


def test_human_request_during_ringing_moves_state_after_provider_accepts() -> None:
    calls, call_id = create_call()
    adapter = FakeHumanEscalationAdapter()

    result = coordinator(call_id, calls, adapter).process_final_event(
        event("Please connect me to a real person")
    )

    assert result.call_session.state is CallState.HUMAN_CALL
    assert result.state_transitioned
    assert adapter.actions == [("ring", call_id, "+911234567890")]
    assert result.state_transition_reason == "provider accepted human-ring action"


def test_escalation_without_provider_configuration_does_not_fake_state_change() -> None:
    calls, call_id = create_call(CallState.AI_CALL)
    coordinator_instance = IntentCallCoordinator(
        call_id,
        "stream-1",
        calls,
        IntentRoutingService(),
    )

    result = coordinator_instance.process_final_event(event("This is an emergency"))

    assert result.call_session.state is CallState.AI_CALL
    assert not result.state_transitioned
    assert "not configured" in result.state_transition_reason


def test_provider_failure_does_not_change_call_state() -> None:
    calls, call_id = create_call(CallState.AI_CALL)
    adapter = FakeHumanEscalationAdapter(fail=True)

    result = coordinator(call_id, calls, adapter).process_final_event(
        event("This is an emergency")
    )

    assert result.call_session.state is CallState.AI_CALL
    assert not result.state_transitioned
    assert "RuntimeError" in result.state_transition_reason


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



def test_unexpected_provider_exception_fails_closed_without_state_change() -> None:
    calls, call_id = create_call(CallState.AI_CALL)

    class UnexpectedFailureAdapter:
        def start_human_ring(self, provider_call_id: str, destination: str) -> None:
            raise ValueError("provider payload rejected")

        def request_human_takeover(self, provider_call_id: str, destination: str) -> None:
            raise ValueError("provider payload rejected")

    result = coordinator(
        call_id,
        calls,
        UnexpectedFailureAdapter(),
    ).process_final_event(event("This is an emergency"))

    assert result.call_session.state is CallState.AI_CALL
    assert not result.state_transitioned
    assert "ValueError" in result.state_transition_reason
