import pytest

from aicaller.ai.repeated_interruption import (
    RepeatedInterruptionConfig,
    RepeatedInterruptionError,
    RepeatedInterruptionGuard,
)


def test_guard_accepts_interruptions_until_limit_then_rejects_more() -> None:
    guard = RepeatedInterruptionGuard(RepeatedInterruptionConfig(2))

    first = guard.observe(generation=4, sequence=10)
    second = guard.observe(generation=4, sequence=11)
    third = guard.observe(generation=4, sequence=12)

    assert first.accepted and not first.limit_reached
    assert second.accepted and second.limit_reached
    assert not third.accepted and third.limit_reached
    assert guard.interruption_count == 2


def test_duplicate_event_is_idempotent() -> None:
    guard = RepeatedInterruptionGuard()
    first = guard.observe(generation=1, sequence=8)
    duplicate = guard.observe(generation=1, sequence=8)
    assert duplicate == first
    assert guard.interruption_count == 1


def test_guard_requires_reset_for_new_generation() -> None:
    guard = RepeatedInterruptionGuard()
    guard.observe(generation=1, sequence=1)
    with pytest.raises(RepeatedInterruptionError, match="reset is required"):
        guard.observe(generation=2, sequence=2)

    guard.reset(generation=2)
    decision = guard.observe(generation=2, sequence=0)
    assert decision.accepted
    assert decision.count == 1


def test_guard_rejects_backwards_sequence_and_invalid_reset() -> None:
    guard = RepeatedInterruptionGuard()
    guard.observe(generation=1, sequence=5)
    with pytest.raises(RepeatedInterruptionError, match="backwards"):
        guard.observe(generation=1, sequence=4)
    with pytest.raises(RepeatedInterruptionError, match="must increase"):
        guard.reset(generation=1)


def test_guard_validates_configuration() -> None:
    with pytest.raises(RepeatedInterruptionError, match="must be positive"):
        RepeatedInterruptionConfig(0)
