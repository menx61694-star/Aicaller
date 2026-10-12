from __future__ import annotations

from dataclasses import dataclass

from aicaller.ai.intent import CallIntent


class ClassificationError(ValueError):
    pass


@dataclass(frozen=True)
class ClassificationThresholds:
    urgent: float = 0.75
    spam: float = 0.80
    important: float = 0.65
    human_request: float = 0.70

    def __post_init__(self) -> None:
        if any(
            not 0.0 <= value <= 1.0
            for value in (self.urgent, self.spam, self.important, self.human_request)
        ):
            raise ClassificationError("thresholds must be between 0 and 1")


@dataclass(frozen=True)
class CallerClassification:
    intent: CallIntent
    confidence: float
    spam_score: float
    urgency_score: float
    human_request_score: float
    reason: str


class CallerClassifier:
    """Small deterministic baseline; replaceable by a calibrated model adapter.

    Scores are rule-derived indicators, not verified probabilities. Unknown
    phrases remain UNKNOWN rather than being force-classified.
    """

    _URGENT = ("emergency", "urgent", "help me", "accident", "hospital", "danger")
    _IMPORTANT = ("doctor", "school", "family", "important", "appointment")
    _HUMAN = ("human", "real person", "agent", "talk to someone", "representative")
    _SPAM = ("loan offer", "win a prize", "limited offer", "investment scheme", "press one")
    _ROUTINE = (
        "calling to confirm",
        "just checking in",
        "general inquiry",
        "general enquiry",
        "routine call",
        "not urgent",
        "following up on",
    )

    def __init__(self, thresholds: ClassificationThresholds | None = None) -> None:
        self.thresholds = thresholds or ClassificationThresholds()

    @staticmethod
    def _score(text: str, phrases: tuple[str, ...], score: float) -> float:
        normalized = " ".join(text.casefold().split())
        return score if any(phrase in normalized for phrase in phrases) else 0.0

    def classify(self, text: str) -> CallerClassification:
        if not text or not text.strip():
            raise ClassificationError("transcript must not be empty")
        urgent = self._score(text, self._URGENT, 0.90)
        important = self._score(text, self._IMPORTANT, 0.72)
        human = self._score(text, self._HUMAN, 0.95)
        spam = self._score(text, self._SPAM, 0.92)
        routine = self._score(text, self._ROUTINE, 0.60)

        if urgent >= self.thresholds.urgent:
            intent, confidence, reason = CallIntent.URGENT, urgent, "urgent phrase matched"
        elif human >= self.thresholds.human_request:
            intent, confidence, reason = (
                CallIntent.HUMAN_REQUEST,
                human,
                "human request phrase matched",
            )
        elif spam >= self.thresholds.spam:
            intent, confidence, reason = CallIntent.SPAM, spam, "spam phrase matched"
        elif important >= self.thresholds.important:
            intent, confidence, reason = (
                CallIntent.IMPORTANT,
                important,
                "important phrase matched",
            )
        elif routine > 0.0:
            intent, confidence, reason = CallIntent.ROUTINE, routine, "routine phrase matched"
        else:
            intent, confidence, reason = CallIntent.UNKNOWN, 0.0, "no configured phrase matched"

        return CallerClassification(
            intent=intent,
            confidence=confidence,
            spam_score=spam,
            urgency_score=urgent,
            human_request_score=human,
            reason=reason,
        )
