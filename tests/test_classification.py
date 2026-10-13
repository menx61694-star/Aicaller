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


def test_classifier_recognizes_hindi_urgent_phrase() -> None:
    result = CallerClassifier().classify("Mujhe turant madad chahiye")

    assert result.intent is CallIntent.URGENT
    assert result.urgency_score == 0.90


def test_classifier_recognizes_devanagari_urgent_phrase() -> None:
    result = CallerClassifier().classify("यह आपातकाल है, तुरंत मदद चाहिए")

    assert result.intent is CallIntent.URGENT


def test_classifier_recognizes_hindi_human_request_and_spam() -> None:
    human = CallerClassifier().classify("Mujhe kisi insaan se baat karni hai")
    spam = CallerClassifier().classify("Aapne inaam jeeta hai, free recharge lein")

    assert human.intent is CallIntent.HUMAN_REQUEST
    assert spam.intent is CallIntent.SPAM


@pytest.mark.parametrize(
    "transcript",
    [
        "This is not an emergency",
        "Emergency nahi hai",
        "Koi emergency nahi hai",
        "Not urgent, just calling to confirm",
    ],
)
def test_negated_urgency_does_not_trigger_urgent_classification(transcript: str) -> None:
    result = CallerClassifier().classify(transcript)

    assert result.urgency_score == 0.0
    assert result.intent is not CallIntent.URGENT


def test_negation_in_previous_sentence_does_not_cancel_later_emergency() -> None:
    result = CallerClassifier().classify(
        "I am not sure what happened. This is an emergency."
    )

    assert result.intent is CallIntent.URGENT


def test_routine_negation_phrase_is_still_classified_as_routine() -> None:
    result = CallerClassifier().classify("Koi jaldi nahi, bas confirm karna tha")

    assert result.intent is CallIntent.ROUTINE


def test_classifier_leaves_unmatched_text_unknown() -> None:
    result = CallerClassifier().classify("Hello, I wanted to ask about tomorrow")
    assert result.intent is CallIntent.UNKNOWN
    assert result.confidence == 0.0


def test_classifier_rejects_empty_text_and_invalid_thresholds() -> None:
    with pytest.raises(ClassificationError, match="must not be empty"):
        CallerClassifier().classify("  ")
    with pytest.raises(ClassificationError, match="between 0 and 1"):
        ClassificationThresholds(spam=1.1)


@pytest.mark.parametrize(
    "transcript",
    [
        "Madad karo, accident ho gaya",
        "Mere paas jaan ka khatra hai",
        "Hospital le chalo, bahut zaroori hai",
        "मुझे तुरंत मदद चाहिए",
        "यह आपातकाल है",
    ],
)
def test_classifier_recognizes_additional_urgent_phrase_variants(transcript: str) -> None:
    result = CallerClassifier().classify(transcript)

    assert result.intent is CallIntent.URGENT
    assert result.urgency_score >= CallerClassifier().thresholds.urgent


@pytest.mark.parametrize(
    "transcript",
    [
        "Please connect me to a representative",
        "I need to talk to someone",
        "Operator se baat karwa do",
        "मुझे किसी इंसान से बात करनी है",
        "ऑपरेटर से बात कराइए",
    ],
)
def test_classifier_recognizes_human_request_variants(transcript: str) -> None:
    result = CallerClassifier().classify(transcript)

    assert result.intent is CallIntent.HUMAN_REQUEST
    assert result.human_request_score >= CallerClassifier().thresholds.human_request


@pytest.mark.parametrize(
    "transcript",
    [
        "You have won a prize",
        "Limited offer, press one",
        "Aapne lakhon jeete",
        "इनाम जीता है",
        "मुफ्त रिचार्ज पाएं",
    ],
)
def test_classifier_recognizes_additional_spam_phrase_variants(transcript: str) -> None:
    result = CallerClassifier().classify(transcript)

    assert result.spam_score >= CallerClassifier().thresholds.spam
    assert result.intent is CallIntent.SPAM


@pytest.mark.parametrize(
    "transcript",
    [
        "No emergency here, I am calling to confirm tomorrow's time",
        "Pehle laga urgent hai, lekin ab koi jaldi nahi",
        "यह आपातकाल नहीं है, बस समय की पुष्टि करनी है",
    ],
)
def test_nonurgent_context_does_not_override_explicit_routine_context(
    transcript: str,
) -> None:
    result = CallerClassifier().classify(transcript)

    assert result.urgency_score == 0.0
    assert result.intent is CallIntent.ROUTINE
