from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aicaller.ai.classification import CallerClassification
from aicaller.ai.intent import CallIntent
from aicaller.ai.policy import PolicyAction


class IntentRoutingError(ValueError):
    pass


class RoutingReason(StrEnum):
    URGENT_ESCALATION = "urgent_escalation"
    HUMAN_REQUEST = "human_request"
    SPAM_BLOCK = "spam_block"
    IMPORTANT_ESCALATION = "important_escalation"
    ROUTINE_CONTINUE = "routine_continue"
    UNKNOWN_REVIEW = "unknown_review"


@dataclass(frozen=True)
class IntentRoutingConfig:
    urgent_escalation_threshold: float = 0.75
    human_request_threshold: float = 0.70
    spam_block_threshold: float = 0.95
    important_escalation_threshold: float = 0.80
    block_spam_automatically: bool = False

    def __post_init__(self) -> None:
        values = (
            self.urgent_escalation_threshold,
            self.human_request_threshold,
            self.spam_block_threshold,
            self.important_escalation_threshold,
        )
        if any(not 0.0 <= value <= 1.0 for value in values):
            raise IntentRoutingError("routing thresholds must be between 0 and 1")


@dataclass(frozen=True)
class IntentRoutingDecision:
    action: PolicyAction
    reason: RoutingReason
    source_intent: CallIntent
    confidence: float
    requires_confirmation: bool


class IntentRouter:
    """Applies explicit, configurable precedence to deterministic classifier output.

    Urgency and explicit human requests outrank spam indicators so a mixed
    transcript is not silently blocked. Automatic spam blocking is opt-in.
    """

    def __init__(self, config: IntentRoutingConfig | None = None) -> None:
        self.config = config or IntentRoutingConfig()

    def route(self, result: CallerClassification) -> IntentRoutingDecision:
        if not 0.0 <= result.confidence <= 1.0:
            raise IntentRoutingError("confidence must be between 0 and 1")
        for score in (result.spam_score, result.urgency_score, result.human_request_score):
            if not 0.0 <= score <= 1.0:
                raise IntentRoutingError("classification scores must be between 0 and 1")

        if (
            result.urgency_score >= self.config.urgent_escalation_threshold
            or result.intent is CallIntent.URGENT
        ):
            return IntentRoutingDecision(
                PolicyAction.REQUEST_HUMAN,
                RoutingReason.URGENT_ESCALATION,
                result.intent,
                max(result.confidence, result.urgency_score),
                requires_confirmation=False,
            )
        if (
            result.human_request_score >= self.config.human_request_threshold
            or result.intent is CallIntent.HUMAN_REQUEST
        ):
            return IntentRoutingDecision(
                PolicyAction.REQUEST_HUMAN,
                RoutingReason.HUMAN_REQUEST,
                result.intent,
                max(result.confidence, result.human_request_score),
                requires_confirmation=False,
            )
        if result.spam_score >= self.config.spam_block_threshold:
            action = (
                PolicyAction.BLOCK
                if self.config.block_spam_automatically
                else PolicyAction.CONTINUE_AI
            )
            return IntentRoutingDecision(
                action,
                RoutingReason.SPAM_BLOCK,
                result.intent,
                result.spam_score,
                requires_confirmation=not self.config.block_spam_automatically,
            )
        if (
            result.intent is CallIntent.IMPORTANT
            and result.confidence >= self.config.important_escalation_threshold
        ):
            return IntentRoutingDecision(
                PolicyAction.REQUEST_HUMAN,
                RoutingReason.IMPORTANT_ESCALATION,
                result.intent,
                result.confidence,
                requires_confirmation=False,
            )
        if result.intent in {CallIntent.ROUTINE, CallIntent.UNKNOWN, CallIntent.SPAM}:
            return IntentRoutingDecision(
                PolicyAction.CONTINUE_AI,
                RoutingReason.ROUTINE_CONTINUE if result.intent is CallIntent.ROUTINE else RoutingReason.UNKNOWN_REVIEW,
                result.intent,
                result.confidence,
                requires_confirmation=result.intent in {CallIntent.UNKNOWN, CallIntent.SPAM},
            )
        return IntentRoutingDecision(
            PolicyAction.CONTINUE_AI,
            RoutingReason.UNKNOWN_REVIEW,
            result.intent,
            result.confidence,
            requires_confirmation=True,
        )
