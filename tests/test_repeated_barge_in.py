import pytest

from aicaller.ai.repeated_barge_in import (
    RepeatedBargeInController,
    RepeatedBargeInError,
)


def test_repeated_barge_in_advances_generation() -> None:
    controller = RepeatedBargeInController(max_interruptions=3)

    first = controller.begin(sequence=10)
    second = controller.begin(sequence=20)

    assert first.generation == 1
    assert second.generation == 2
    assert controller.count == 2


def test_repeated_barge_in_is_bounded() -> None:
    controller = RepeatedBargeInController(max_interruptions=2)
    controller.begin(sequence=1)
    controller.begin(sequence=2)

    with pytest.raises(RepeatedBargeInError, match="maximum interruptions"):
        controller.begin(sequence=3)


def test_reset_starts_a_new_generation() -> None:
    controller = RepeatedBargeInController()
    controller.begin(sequence=1)
    controller.reset()

    assert controller.count == 0
    assert controller.generation == 2
