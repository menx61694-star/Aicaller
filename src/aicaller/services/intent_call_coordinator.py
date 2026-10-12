from __future__ import annotations

from dataclasses import dataclass

from aicaller.ai.intent_routing_service import (
    IntentRoutingEvaluation,
    IntentRoutingService,
)
from aicaller.ai.policy import PolicyAction
from aicaller.ai.session import AITranscriptEvent
from aicaller.domain.call import CallSession, CallState
from aicaller.services.call_service import CallService


class IntentCallCoordinatorError(ValueError):
    pass


@dataclass(frozen=True)
class CoordinatedIntentResult:
    evaluation: IntentRoutingEvaluation
    call_session: CallSession
    state_transitioned: bool
    state_transition_reason: str


class IntentCallCoordinator:
    """Apply intent escalation only to the call's explicitly bound AI stream.

    Scope one coordinator and routing context to one call and one stream.
    Provider-specific ring/bridge operations remain the responsibility of the
    telephony adapter.
    """

    def __init__(
        self,
        call_id: str,
        stream_sid: str,
        call_service: CallService,
        intent_routing: IntentRoutingService,
    ) -> None:
        if not call_id:
            raise IntentCallCoordinatorError("call_id is required")
        if not stream_sid:
            raise IntentCallCoordinatorError("stream_sid is required")
        self.call_id = call_id
        self.stream_sid = stream_sid
        self.call_service = call_service
        self.intent_routing = intent_routing

    def process_final_event(self, event: AITranscriptEvent) -> CoordinatedIntentResult:
        if event.stream_sid != self.stream_sid:
            raise IntentCallCoordinatorError("transcript stream does not match call stream")

        current = self.call_service.get(self.call_id)
        if current is None:
            raise KeyError(self.call_id)

        evaluation = self.intent_routing.evaluate_final_event(event)
        if evaluation.decision.action is not PolicyAction.REQUEST_HUMAN:
            return CoordinatedIntentResult(
                evaluation,
                current,
                False,
                "no human escalation requested",
            )

        if current.state is CallState.RINGING:
            updated = self.call_service.transition(self.call_id, CallState.HUMAN_CALL)
            return CoordinatedIntentResult(
                evaluation,
                updated,
                updated.state is not current.state,
                "human ring state requested; provider ring action remains external",
            )
        if current.state is CallState.AI_CALL:
            updated = self.call_service.transition(
                self.call_id,
                CallState.TAKEOVER_REQUESTED,
            )
            return CoordinatedIntentResult(
                evaluation,
                updated,
                updated.state is not current.state,
                "takeover requested; provider bridge action remains external",
            )
        if current.state in {CallState.TAKEOVER_REQUESTED, CallState.HUMAN_CALL}:
            return CoordinatedIntentResult(
                evaluation,
                current,
                False,
                "human escalation already active or pending",
            )

        return CoordinatedIntentResult(
            evaluation,
            current,
            False,
            f"human escalation deferred in state {current.state}",
        )
