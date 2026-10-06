from __future__ import annotations

from dataclasses import dataclass

from aicaller.ai.conversation import ConversationManager
from aicaller.ai.disclosure import AIDisclosurePolicy
from aicaller.ai.intent import IntentContextStore
from aicaller.ai.llm import LLMDelta, LLMStreamState
from aicaller.ai.policy import PolicyContextStore
from aicaller.ai.response_validation import ResponseValidator, ValidatedResponse


class ResponsePipelineError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResponseContext:
    conversation: ConversationManager
    intent: IntentContextStore
    policy: PolicyContextStore
    disclosure: AIDisclosurePolicy
    validator: ResponseValidator


class AIResponsePipeline:
    """Deterministic orchestration boundary from model deltas to validated text."""

    def __init__(self, max_response_chars: int = 2000) -> None:
        self.context = ResponseContext(
            conversation=ConversationManager(),
            intent=IntentContextStore(),
            policy=PolicyContextStore(),
            disclosure=AIDisclosurePolicy(),
            validator=ResponseValidator(max_chars=max_response_chars),
        )

    def validate_stream(
        self,
        deltas: tuple[LLMDelta, ...],
        *,
        language: str | None = None,
    ) -> ValidatedResponse:
        state = LLMStreamState()
        for delta in deltas:
            state.apply(delta)
        if not state.finished:
            raise ResponsePipelineError("LLM stream did not finish")
        return self.context.validator.validate(state.text, language=language)
