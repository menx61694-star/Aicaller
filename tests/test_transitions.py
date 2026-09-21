from aicaller.domain.call import CallState
from aicaller.domain.transitions import can_transition


def test_valid_path():
    assert can_transition(CallState.INCOMING, CallState.RINGING)
    assert can_transition(CallState.RINGING, CallState.AI_ANSWERING)
    assert can_transition(CallState.AI_ANSWERING, CallState.AI_CALL)
    assert can_transition(CallState.AI_CALL, CallState.TAKEOVER_REQUESTED)
    assert can_transition(CallState.TAKEOVER_REQUESTED, CallState.HUMAN_CALL)


def test_invalid_backward_transition():
    assert not can_transition(CallState.AI_CALL, CallState.RINGING)
    assert not can_transition(CallState.CALL_ENDED, CallState.AI_CALL)
