import pytest

from aicaller.ai.intent import CallIntent, IntentContextStore, IntentError


def test_intent_context_starts_unknown() -> None:
    context = IntentContextStore().get()
    assert context.intent is CallIntent.UNKNOWN
    assert context.confidence == 0.0


def test_intent_context_updates_monotonically() -> None:
    store = IntentContextStore()
    store.update(
        CallIntent.URGENT,
        0.92,
        source_sequence=1,
        reason="caller requested immediate help",
    )
    context = store.get()
    assert context.intent is CallIntent.URGENT
    assert context.confidence == 0.92
    assert context.reason == "caller requested immediate help"


def test_intent_context_rejects_invalid_confidence() -> None:
    store = IntentContextStore()
    with pytest.raises(IntentError, match="between 0 and 1"):
        store.update(CallIntent.ROUTINE, 1.1, source_sequence=1)


def test_intent_context_rejects_stale_sequence() -> None:
    store = IntentContextStore()
    store.update(CallIntent.ROUTINE, 0.5, source_sequence=2)
    with pytest.raises(IntentError, match="must increase"):
        store.update(CallIntent.IMPORTANT, 0.7, source_sequence=2)
