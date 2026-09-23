from __future__ import annotations

from dataclasses import dataclass


class ConversationError(ValueError):
    pass


@dataclass(frozen=True)
class ConversationTurn:
    role: str
    text: str
    sequence: int
    language: str | None = None


@dataclass(frozen=True)
class ConversationContext:
    turns: tuple[ConversationTurn, ...]
    current_transcript: str
    last_user_language: str | None


class ConversationManager:
    """Deterministic bounded conversation state for an active call."""

    def __init__(self, max_turns: int = 20) -> None:
        if max_turns < 1:
            raise ConversationError("max_turns must be positive")
        self.max_turns = max_turns
        self._turns: list[ConversationTurn] = []
        self._current_transcript = ""
        self._last_user_language: str | None = None
        self._sequence = -1

    def apply_user_transcript(
        self,
        text: str,
        *,
        sequence: int,
        is_final: bool,
        language: str | None = None,
    ) -> None:
        if sequence <= self._sequence:
            raise ConversationError("transcript sequence must increase")
        if not text.strip():
            raise ConversationError("transcript text must not be empty")
        self._sequence = sequence
        self._current_transcript = text
        if language is not None:
            self._last_user_language = language
        if is_final:
            self._turns.append(
                ConversationTurn(
                    role="user",
                    text=text,
                    sequence=sequence,
                    language=language,
                )
            )
            self._turns = self._turns[-self.max_turns :]
            self._current_transcript = ""

    def add_assistant_turn(
        self,
        text: str,
        *,
        sequence: int,
        language: str | None = None,
    ) -> None:
        if sequence <= self._sequence:
            raise ConversationError("turn sequence must increase")
        if not text.strip():
            raise ConversationError("assistant text must not be empty")
        self._sequence = sequence
        self._turns.append(
            ConversationTurn(
                role="assistant",
                text=text,
                sequence=sequence,
                language=language,
            )
        )
        self._turns = self._turns[-self.max_turns :]

    def context(self) -> ConversationContext:
        return ConversationContext(
            turns=tuple(self._turns),
            current_transcript=self._current_transcript,
            last_user_language=self._last_user_language,
        )
