import pytest

from aicaller.ai.classification import (
    CallerClassifier,
    ClassificationError,
    ClassificationThresholds,
)
from aicaller.ai.intent import CallIntent


def test_classifier_marks_urgent_and_reports_score() -> None:
    result = CallerClassifier().classify("Please help me, this is an emergency")
    assert result.intent is CallIntent.URGENT
    assert result.urgency_score == 0.90
    assert result.confidence == result.urgency_score


def test_classifier_scores_spam_without_hiding_human_request_precedence() -> None:
    result = CallerClassifier().classify("I am a real person calling about a loan offer")
    assert result.intent is CallIntent.HUMAN_REQUEST
    assert result.human_request_score == 0.95
    assert result.spam_score == 0.92


def test_classifier_uses_configurable_thresholds() -> None:
    classifier = CallerClassifier(ClassificationThresholds(urgent=0.95))
    result = classifier.classify("urgent help me")
    assert result.intent is CallIntent.UNKNOWN
    assert result.urgency_score == 0.90


def test_classifier_recognizes_routine_phrases_below_urgent_priorities() -> None:
    result = CallerClassifier().classify("I am calling to confirm the time")

    assert result.intent is CallIntent.ROUTINE
    assert result.confidence == 0.60
    assert result.reason == "routine phrase matched"


def test_urgent_phrase_wins_when_transcript_has_routine_phrase_too() -> None:
    result = CallerClassifier().classify(
        "I am calling to confirm, but this is an emergency"
    )

    assert result.intent is CallIntent.URGENT


def test_classifier_leaves_unmatched_text_unknown() -> None:
    result = CallerClassifier().classify("Hello, I wanted to ask about tomorrow")
    assert result.intent is CallIntent.UNKNOWN
    assert result.confidence == 0.0


def test_classifier_rejects_empty_text_and_invalid_thresholds() -> None:
    with pytest.raises(ClassificationError, match="must not be empty"):
        CallerClassifier().classify("  ")
    with pytest.raises(ClassificationError, match="between 0 and 1"):
        ClassificationThresholds(spam=1.1)
