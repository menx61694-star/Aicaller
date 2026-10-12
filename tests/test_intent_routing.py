import pytest

from aicaller.ai.classification import CallerClassification
from aicaller.ai.intent import CallIntent
from aicaller.ai.intent_routing import (
    IntentRouter,
    IntentRoutingConfig,
    IntentRoutingError,
    RoutingReason,
)
from aicaller.ai.policy import PolicyAction


def classification(
    intent: CallIntent = CallIntent.UNKNOWN,
    *,
    confidence: float = 0.0,
    spam: float = 0.0,
    urgency: float = 0.0,
    human: float = 0.0,
) -> CallerClassification:
    return CallerClassification(
        intent=intent,
        confidence=confidence,
        spam_score=spam,
        urgency_score=urgency,
        human_request_score=human,
        reason="test",
    )


def test_urgent_escalation_has_precedence_over_spam() -> None:
    decision = IntentRouter().route(
        classification(CallIntent.URGENT, confidence=0.9, spam=0.99, urgency=0.9)
    )
    assert decision.action is PolicyAction.REQUEST_HUMAN
    assert decision.reason is RoutingReason.URGENT_ESCALATION


def test_human_request_has_precedence_over_spam() -> None:
    decision = IntentRouter().route(
        classification(CallIntent.HUMAN_REQUEST, confidence=0.95, spam=0.99, human=0.95)
    )
    assert decision.action is PolicyAction.REQUEST_HUMAN
    assert decision.reason is RoutingReason.HUMAN_REQUEST


def test_configured_urgency_threshold_is_not_bypassed_by_intent_label() -> None:
    router = IntentRouter(IntentRoutingConfig(urgent_escalation_threshold=0.98))
    decision = router.route(
        classification(CallIntent.URGENT, confidence=0.9, urgency=0.9)
    )

    assert decision.action is PolicyAction.CONTINUE_AI
    assert decision.reason is RoutingReason.UNKNOWN_REVIEW
    assert decision.requires_confirmation


def test_configured_human_threshold_is_not_bypassed_by_intent_label() -> None:
    router = IntentRouter(IntentRoutingConfig(human_request_threshold=0.99))
    decision = router.route(
        classification(CallIntent.HUMAN_REQUEST, confidence=0.95, human=0.95)
    )

    assert decision.action is PolicyAction.CONTINUE_AI
    assert decision.requires_confirmation


def test_spam_block_is_opt_in_and_requires_confirmation_by_default() -> None:
    result = classification(CallIntent.SPAM, confidence=0.92, spam=0.99)
    default = IntentRouter().route(result)
    assert default.action is PolicyAction.CONTINUE_AI
    assert default.requires_confirmation

    blocking = IntentRouter(IntentRoutingConfig(block_spam_automatically=True)).route(result)
    assert blocking.action is PolicyAction.BLOCK
    assert not blocking.requires_confirmation


def test_important_call_escalates_only_above_configured_threshold() -> None:
    router = IntentRouter(IntentRoutingConfig(important_escalation_threshold=0.8))
    below = router.route(classification(CallIntent.IMPORTANT, confidence=0.7))
    above = router.route(classification(CallIntent.IMPORTANT, confidence=0.85))
    assert below.action is PolicyAction.CONTINUE_AI
    assert above.action is PolicyAction.REQUEST_HUMAN


def test_unknown_intent_is_not_automatically_blocked() -> None:
    decision = IntentRouter().route(classification())
    assert decision.action is PolicyAction.CONTINUE_AI
    assert decision.requires_confirmation


def test_router_rejects_invalid_thresholds_and_scores() -> None:
    with pytest.raises(IntentRoutingError, match="thresholds"):
        IntentRoutingConfig(spam_block_threshold=1.1)
    with pytest.raises(IntentRoutingError, match="scores"):
        IntentRouter().route(classification(spam=1.2))
