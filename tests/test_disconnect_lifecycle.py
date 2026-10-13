import pytest

from aicaller.domain.call import CallState
from aicaller.domain.transitions import can_transition
from aicaller.services.call_repository import InMemoryCallRepository
from aicaller.services.call_service import CallService


@pytest.mark.parametrize(
    "state",
    [
        CallState.INCOMING,
        CallState.RINGING,
        CallState.AI_ANSWERING,
        CallState.AI_CALL,
        CallState.TAKEOVER_REQUESTED,
        CallState.HUMAN_CALL,
        CallState.FAILURE,
    ],
)
def test_active_or_failed_call_can_end_after_provider_disconnect(state: CallState) -> None:
    assert can_transition(state, CallState.CALL_ENDED)


@pytest.mark.parametrize(
    "state",
    [
        CallState.INCOMING,
        CallState.RINGING,
        CallState.AI_ANSWERING,
    ],
)
def test_early_disconnect_transitions_to_call_ended(state: CallState) -> None:
    calls = CallService(InMemoryCallRepository())
    call = calls.create_incoming(f"disconnect-{state.value}", "+911")
    if state is not CallState.INCOMING:
        calls.transition(call.call_id, CallState.RINGING)
    if state is CallState.AI_ANSWERING:
        calls.transition(call.call_id, CallState.AI_ANSWERING)

    ended = calls.transition(call.call_id, CallState.CALL_ENDED)

    assert ended.state is CallState.CALL_ENDED
