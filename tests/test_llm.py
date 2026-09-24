import pytest

from aicaller.ai.llm import LLMDelta, LLMError, LLMStreamState, UnconfiguredStreamingLLM


@pytest.mark.asyncio
async def test_unconfigured_llm_fails_closed() -> None:
    with pytest.raises(LLMError, match="not configured"):
        await UnconfiguredStreamingLLM().stream((("user", "hello"),))


def test_llm_stream_accumulates_deltas() -> None:
    state = LLMStreamState()
    state.apply(LLMDelta("Hel", sequence=1))
    state.apply(LLMDelta("lo", sequence=2, is_final=True))
    assert state.text == "Hello"
    assert state.finished


def test_llm_stream_rejects_stale_sequence() -> None:
    state = LLMStreamState()
    state.apply(LLMDelta("one", sequence=1))
    with pytest.raises(LLMError, match="must increase"):
        state.apply(LLMDelta("old", sequence=1))


def test_llm_stream_rejects_delta_after_final() -> None:
    state = LLMStreamState()
    state.apply(LLMDelta("done", sequence=1, is_final=True))
    with pytest.raises(LLMError, match="already finished"):
        state.apply(LLMDelta("late", sequence=2))
