import pytest

from aicaller.ai.intent import CallIntent, IntentContextStore, IntentError
from aicaller.ai.intent_routing import RoutingReason
from aicaller.ai.intent_routing_service import IntentRoutingService
from aicaller.ai.policy import PolicyAction, PolicyContextStore, PolicyError


def test_service_persists_urgent_classification_and_human_routing() -> None:
    service = IntentRoutingService()

    result = service.evaluate("This is an emergency, please help me", source_sequence=1)

    assert result.classification.intent is CallIntent.URGENT
    assert result.decision.action is PolicyAction.REQUEST_HUMAN
    assert result.decision.reason is RoutingReason.URGENT_ESCALATION
    assert result.intent_context.source_sequence == 1
    assert result.intent_context.intent is CallIntent.URGENT
    assert result.policy_context.source_sequence == 1
    assert result.policy_context.action is PolicyAction.REQUEST_HUMAN


def test_service_keeps_spam_blocking_safe_by_default() -> None:
    result = IntentRoutingService().evaluate(
        "You have a limited offer, press one now", source_sequence=1
    )

    assert result.classification.intent is CallIntent.SPAM
    assert result.decision.action is PolicyAction.CONTINUE_AI
    assert result.decision.requires_confirmation
    assert "confirmation required" in result.policy_context.reason


def test_service_unknown_transcript_continues_without_automatic_block() -> None:
    result = IntentRoutingService().evaluate(
        "Could you tell me what time it is?", source_sequence=1
    )

    assert result.classification.intent is CallIntent.UNKNOWN
    assert result.policy_context.action is PolicyAction.CONTINUE_AI
    assert result.decision.requires_confirmation


def test_stale_sequence_does_not_partially_mutate_either_store() -> None:
    intent_store = IntentContextStore()
    policy_store = PolicyContextStore()
    service = IntentRoutingService(intent_store=intent_store, policy_store=policy_store)
    service.evaluate("routine call", source_sequence=3)
    before_intent = intent_store.get()
    before_policy = policy_store.get()

    with pytest.raises(IntentError, match="must increase"):
        service.evaluate("emergency", source_sequence=3)

    assert intent_store.get() == before_intent
    assert policy_store.get() == before_policy


def test_policy_store_stale_sequence_does_not_mutate_intent_store() -> None:
    intent_store = IntentContextStore()
    policy_store = PolicyContextStore()
    service = IntentRoutingService(intent_store=intent_store, policy_store=policy_store)
    policy_store.update(PolicyAction.CONTINUE_AI, "existing", source_sequence=5)

    with pytest.raises(PolicyError, match="must increase"):
        service.evaluate("emergency", source_sequence=4)

    assert intent_store.get().source_sequence == -1
    assert policy_store.get().source_sequence == 5


def test_service_rejects_negative_sequence_before_classification() -> None:
    service = IntentRoutingService()

    with pytest.raises(ValueError, match="non-negative"):
        service.evaluate("emergency", source_sequence=-1)
