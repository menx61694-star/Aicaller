from __future__ import annotations

from dataclasses import dataclass

from aicaller.adapters.telephony.base import HumanEscalationAdapter
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
    """Apply escalation only after the provider accepts its action.

    Scope one coordinator and routing context to one call and one stream.
    The domain state is never advanced to a human state if the provider
    adapter/destination is missing or the provider action raises an error.
    """

    def __init__(
        self,
        call_id: str,
        stream_sid: str,
        call_service: CallService,
        intent_routing: IntentRoutingService,
        human_escalation_adapter: HumanEscalationAdapter | None = None,
        human_destination: str | None = None,
    ) -> None:
        if not call_id:
            raise IntentCallCoordinatorError("call_id is required")
        if not stream_sid:
            raise IntentCallCoordinatorError("stream_sid is required")
        self.call_id = call_id
        self.stream_sid = stream_sid
        self.call_service = call_service
        self.intent_routing = intent_routing
        self.human_escalation_adapter = human_escalation_adapter
        self.human_destination = human_destination.strip() if human_destination else None

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
            if not self.human_destination or self.human_escalation_adapter is None:
                return CoordinatedIntentResult(
                    evaluation,
                    current,
                    False,
                    "human ring blocked: provider adapter or destination not configured",
                )
            try:
                provider_call_id = current.provider_call_id or current.call_id
                self.human_escalation_adapter.start_human_ring(
                    provider_call_id,
                    self.human_destination,
                )
            except (RuntimeError, OSError, ValueError, TypeError) as exc:
                return CoordinatedIntentResult(
                    evaluation,
                    current,
                    False,
                    f"human ring provider action failed: {type(exc).__name__}",
                )
            updated = self.call_service.transition(self.call_id, CallState.HUMAN_CALL)
            return CoordinatedIntentResult(
                evaluation,
                updated,
                updated.state is not current.state,
                "provider accepted human-ring action",
            )

        if current.state is CallState.AI_CALL:
            if not self.human_destination or self.human_escalation_adapter is None:
                return CoordinatedIntentResult(
                    evaluation,
                    current,
                    False,
                    "human takeover blocked: provider adapter or destination not configured",
                )
            try:
                provider_call_id = current.provider_call_id or current.call_id
                self.human_escalation_adapter.request_human_takeover(
                    provider_call_id,
                    self.human_destination,
                )
            except (RuntimeError, OSError, ValueError, TypeError) as exc:
                return CoordinatedIntentResult(
                    evaluation,
                    current,
                    False,
                    f"human takeover provider action failed: {type(exc).__name__}",
                )
            updated = self.call_service.transition(
                self.call_id,
                CallState.TAKEOVER_REQUESTED,
            )
            return CoordinatedIntentResult(
                evaluation,
                updated,
                updated.state is not current.state,
                "provider accepted human-takeover action",
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
