import pytest

from aicaller.audio.tts_cancel import (
    TTSCancellationController,
    TTSCancellationError,
)


def test_tts_cancellation_is_idempotent() -> None:
    controller = TTSCancellationController()
    first = controller.cancel(reason="caller interrupted", sequence=3)
    second = controller.cancel(reason="different reason", sequence=4)
    assert first == second
    assert controller.cancelled


def test_tts_cancellation_rejects_empty_reason() -> None:
    with pytest.raises(TTSCancellationError, match="must not be empty"):
        TTSCancellationController().cancel(reason=" ", sequence=1)


def test_tts_cancellation_reset() -> None:
    controller = TTSCancellationController()
    controller.cancel(reason="barge-in", sequence=1)
    controller.reset()
    assert not controller.cancelled
    assert controller.signal is None
