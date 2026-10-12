from __future__ import annotations

from dataclasses import dataclass

from aicaller.ai.classification import CallerClassification, CallerClassifier
from aicaller.ai.intent import IntentContext, IntentContextStore, IntentError
from aicaller.ai.intent_routing import (
    IntentRouter,
    IntentRoutingDecision,
    IntentRoutingError,
)
from aicaller.ai.policy import PolicyContext, PolicyContextStore, PolicyError


class IntentRoutingServiceError(ValueError):
    pass


@dataclass(frozen=True)
class IntentRoutingEvaluation:
    classification: CallerClassification
    decision: IntentRoutingDecision
    intent_context: IntentContext
    policy_context: PolicyContext


class IntentRoutingService:
    """Evaluate transcript intent and persist matching intent/policy contexts.

    Both stores are preflighted before either is changed, preventing stale
    transcript events from partially updating the two contexts.
    """

    def __init__(
        self,
        classifier: CallerClassifier | None = None,
        router: IntentRouter | None = None,
        intent_store: IntentContextStore | None = None,
        policy_store: PolicyContextStore | None = None,
    ) -> None:
        self.classifier = classifier or CallerClassifier()
        self.router = router or IntentRouter()
        self.intent_store = intent_store or IntentContextStore()
        self.policy_store = policy_store or PolicyContextStore()

    def evaluate(self, transcript: str, *, source_sequence: int) -> IntentRoutingEvaluation:
        if source_sequence < 0:
            raise IntentRoutingServiceError("source sequence must be non-negative")

        # Compute first; failures here must not mutate either context store.
        classification = self.classifier.classify(transcript)
        decision = self.router.route(classification)

        current_intent = self.intent_store.get()
        current_policy = self.policy_store.get()
        if source_sequence <= current_intent.source_sequence:
            raise IntentError("intent sequence must increase")
        if source_sequence <= current_policy.source_sequence:
            raise PolicyError("policy sequence must increase")

        reason = f"{decision.reason.value}: {classification.reason}"
        if decision.requires_confirmation:
            reason = f"{reason}; confirmation required"

        # All input and sequence validation is complete before the first write.
        self.intent_store.update(
            classification.intent,
            classification.confidence,
            source_sequence=source_sequence,
            reason=classification.reason,
        )
        self.policy_store.update(
            decision.action,
            reason,
            source_sequence=source_sequence,
        )
        return IntentRoutingEvaluation(
            classification=classification,
            decision=decision,
            intent_context=self.intent_store.get(),
            policy_context=self.policy_store.get(),
        )
