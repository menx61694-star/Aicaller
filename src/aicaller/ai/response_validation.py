from __future__ import annotations

from dataclasses import dataclass


class ResponseValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedResponse:
    text: str
    language: str | None = None


class ResponseValidator:
    """Deterministic safety/shape gate before model output reaches TTS."""

    def __init__(self, max_chars: int = 2000) -> None:
        if max_chars < 1:
            raise ResponseValidationError("max_chars must be positive")
        self.max_chars = max_chars

    def validate(
        self,
        text: str,
        *,
        language: str | None = None,
    ) -> ValidatedResponse:
        normalized = " ".join(text.split())
        if not normalized:
            raise ResponseValidationError("response text must not be empty")
        if len(normalized) > self.max_chars:
            raise ResponseValidationError("response exceeds maximum length")
        if any(ord(char) < 32 and char not in "\t\n\r" for char in normalized):
            raise ResponseValidationError("response contains control characters")
        if language is not None and not language.strip():
            raise ResponseValidationError("language must not be empty")
        return ValidatedResponse(text=normalized, language=language)
