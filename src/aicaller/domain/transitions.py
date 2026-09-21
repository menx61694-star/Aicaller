from aicaller.domain.call import CallState

VALID_TRANSITIONS = {
    CallState.INCOMING: {CallState.RINGING, CallState.FAILURE},
    CallState.RINGING: {CallState.AI_ANSWERING, CallState.HUMAN_CALL, CallState.FAILURE},
    CallState.AI_ANSWERING: {CallState.AI_CALL, CallState.FAILURE},
    CallState.AI_CALL: {CallState.TAKEOVER_REQUESTED, CallState.CALL_ENDED, CallState.FAILURE},
    CallState.TAKEOVER_REQUESTED: {CallState.HUMAN_CALL, CallState.AI_CALL, CallState.FAILURE},
    CallState.HUMAN_CALL: {CallState.CALL_ENDED, CallState.FAILURE},
    CallState.FAILURE: {CallState.CALL_ENDED},
    CallState.CALL_ENDED: {CallState.POST_PROCESSING},
    CallState.POST_PROCESSING: set(),
}


def can_transition(current: CallState, target: CallState) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())
