import pytest

from aicaller.ai.barge_in import BargeInConfig, BargeInDetector, BargeInError


def test_barge_in_requires_consecutive_speech_frames() -> None:
    detector = BargeInDetector(BargeInConfig(speech_frames_required=2))
    assert not detector.observe(is_speech=True, confidence=0.9)
    assert detector.observe(is_speech=True, confidence=0.9)


def test_barge_in_resets_on_non_speech_before_threshold() -> None:
    detector = BargeInDetector(BargeInConfig(speech_frames_required=2))
    detector.observe(is_speech=True, confidence=0.9)
    assert not detector.observe(is_speech=False, confidence=0.0)
    assert not detector.triggered


def test_barge_in_rejects_invalid_confidence() -> None:
    detector = BargeInDetector()
    with pytest.raises(BargeInError, match="between 0 and 1"):
        detector.observe(is_speech=True, confidence=1.1)


def test_barge_in_reset_clears_trigger() -> None:
    detector = BargeInDetector(BargeInConfig(speech_frames_required=1))
    assert detector.observe(is_speech=True, confidence=0.8)
    detector.reset()
    assert not detector.triggered
