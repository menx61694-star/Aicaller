import pytest

from aicaller.ai.policy import PolicyAction, PolicyContextStore, PolicyError


def test_policy_defaults_to_continue_ai() -> None:
    context = PolicyContextStore().get()
    assert context.action is PolicyAction.CONTINUE_AI
    assert context.reason == "default"


def test_policy_updates_decision() -> None:
    store = PolicyContextStore()
    store.update(
        PolicyAction.REQUEST_HUMAN,
        "caller explicitly requested a person",
        source_sequence=1,
    )
    context = store.get()
    assert context.action is PolicyAction.REQUEST_HUMAN
    assert context.source_sequence == 1


def test_policy_rejects_empty_reason() -> None:
    store = PolicyContextStore()
    with pytest.raises(PolicyError, match="must not be empty"):
        store.update(PolicyAction.BLOCK, " ", source_sequence=1)


def test_policy_rejects_stale_sequence() -> None:
    store = PolicyContextStore()
    store.update(PolicyAction.CONTINUE_AI, "continue", source_sequence=2)
    with pytest.raises(PolicyError, match="must increase"):
        store.update(PolicyAction.END_CALL, "end", source_sequence=2)
