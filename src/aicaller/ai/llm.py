from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMDelta:
    text: str
    sequence: int
    is_final: bool = False


class StreamingLLM(Protocol):
    async def stream(
        self,
        messages: tuple[tuple[str, str], ...],
    ) -> "AsyncIterator[LLMDelta]": ...


class UnconfiguredStreamingLLM:
    """Fail-closed provider boundary until a live LLM transport is configured."""

    async def stream(
        self,
        messages: tuple[tuple[str, str], ...],
    ) -> AsyncIterator[LLMDelta]:
        raise LLMError("streaming LLM provider is not configured")


class LLMStreamState:
    """Deterministic validation/state for streamed model output."""

    def __init__(self) -> None:
        self._sequence = -1
        self._parts: list[str] = []
        self._finished = False

    def apply(self, delta: LLMDelta) -> None:
        if self._finished:
            raise LLMError("LLM stream is already finished")
        if delta.sequence <= self._sequence:
            raise LLMError("LLM sequence must increase")
        if not delta.text:
            raise LLMError("LLM delta must not be empty")
        self._sequence = delta.sequence
        self._parts.append(delta.text)
        if delta.is_final:
            self._finished = True

    @property
    def text(self) -> str:
        return "".join(self._parts)

    @property
    def finished(self) -> bool:
        return self._finished
