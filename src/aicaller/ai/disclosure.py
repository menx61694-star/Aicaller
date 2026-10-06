from __future__ import annotations

from dataclasses import dataclass


class DisclosureError(ValueError):
    pass


@dataclass(frozen=True)
class AIDisclosure:
    text: str
    language: str


class AIDisclosurePolicy:
    """Provides a deterministic disclosure statement for AI-assisted calls."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        statements: dict[str, str] | None = None,
    ) -> None:
        self.enabled = enabled
        self._statements = {
            "en": "You are speaking with an AI assistant.",
            "hi": "Aap ek AI assistant se baat kar rahe hain.",
        }
        if statements:
            self._statements.update(statements)

    def disclosure(self, language: str = "en") -> AIDisclosure | None:
        if not self.enabled:
            return None
        normalized = language.strip().lower()
        if not normalized:
            raise DisclosureError("language must not be empty")
        text = self._statements.get(normalized)
        if text is None:
            text = self._statements["en"]
            normalized = "en"
        return AIDisclosure(text=text, language=normalized)
