from __future__ import annotations

import re
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
    """Deterministic Hindi/English phrase baseline, not a calibrated ML model."""

    _URGENT = (
        "emergency", "urgent", "help me", "accident", "hospital", "danger",
        "आपातकाल", "तुरंत मदद", "बहुत जरूरी", "madad karo", "madad chahiye",
        "bahut zaroori", "accident ho gaya", "hospital le chalo", "jaan ka khatra",
        "emergency hai",
    )
    _IMPORTANT = (
        "doctor", "school", "family", "important", "appointment", "parivaar",
        "zaroori baat", "जरूरी बात", "परिवार", "अपॉइंटमेंट",
    )
    _HUMAN = (
        "human", "real person", "agent", "talk to someone", "representative",
        "insaan se baat", "kisi insaan", "human se baat", "agent se baat",
        "operator se baat", "aadmi se baat", "किसी इंसान से बात", "इंसान से बात",
        "ऑपरेटर से बात",
    )
    _SPAM = (
        "loan offer", "win a prize", "limited offer", "investment scheme", "press one",
        "loan ke liye", "inaam jeeta", "inaam jeetne", "lakhon jeete", "free recharge",
        "इनाम जीता", "मुफ्त रिचार्ज", "you have won a prize",
    )
    _ROUTINE = (
        "calling to confirm", "just checking in", "general inquiry", "general enquiry",
        "routine call", "not urgent", "following up on", "time confirm", "sirf poochna",
        "bas confirm karna", "koi jaldi nahi", "jaldi nahi hai", "समय की पुष्टि",
        "सिर्फ पूछना", "कोई जल्दी नहीं",
    )
    _NEGATION = re.compile(
        r"\b(?:not|no|never|isn't|aren't|don't|doesn't|didn't|without|"
        r"nahi|nahin|nhi|mat|mana)\b|नहीं|मत|ना",
        re.IGNORECASE,
    )

    def __init__(self, thresholds: ClassificationThresholds | None = None) -> None:
        self.thresholds = thresholds or ClassificationThresholds()

    @classmethod
    def _has_phrase(
        cls,
        text: str,
        phrases: tuple[str, ...],
        *,
        negation_sensitive: bool = True,
    ) -> bool:
        normalized = " ".join(text.casefold().split())
        for phrase in phrases:
            start = 0
            while True:
                index = normalized.find(phrase.casefold(), start)
                if index < 0:
                    break
                end = index + len(phrase)
                if not negation_sensitive:
                    return True
                before = normalized[max(0, index - 14) : index]
                after = normalized[end : min(len(normalized), end + 12)]
                # A corrective contrast such as "urgent earlier, but not now"
                # should not be treated as a current urgent signal.
                tail = normalized[end:]
                contrast = re.search(r"\b(?:but|however|lekin|magar)\b", tail)
                corrected = False
                if contrast:
                    correction = tail[contrast.end() : contrast.end() + 36]
                    corrected = bool(cls._NEGATION.search(correction))
                # Keep ordinary negation local to the matched phrase; do not
                # let a negation from a previous sentence cancel a later signal.
                if (
                    not cls._NEGATION.search(before)
                    and not cls._NEGATION.search(after)
                    and not corrected
                ):
                    return True
                start = index + 1
        return False

    @classmethod
    def _score(
        cls,
        text: str,
        phrases: tuple[str, ...],
        score: float,
        *,
        negation_sensitive: bool = True,
    ) -> float:
        return (
            score
            if cls._has_phrase(text, phrases, negation_sensitive=negation_sensitive)
            else 0.0
        )

    def classify(self, text: str) -> CallerClassification:
        if not text or not text.strip():
            raise ClassificationError("transcript must not be empty")
        urgent = self._score(text, self._URGENT, 0.90)
        important = self._score(text, self._IMPORTANT, 0.72)
        human = self._score(text, self._HUMAN, 0.95)
        spam = self._score(text, self._SPAM, 0.92)
        routine = self._score(text, self._ROUTINE, 0.60, negation_sensitive=False)

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
