import pytest

from aicaller.ai.transcript import TranscriptError, TranscriptState, TranscriptUpdate


def test_partial_then_final_transcript() -> None:
    state = TranscriptState("stream-1")
    state.apply(TranscriptUpdate("stream-1", "hello wor", False, 1))
    assert state.current_text == "hello wor"
    state.apply(TranscriptUpdate("stream-1", "hello world", True, 2))
    assert state.partial == ""
    assert state.final_text == "hello world"


def test_multiple_final_segments_are_preserved() -> None:
    state = TranscriptState("stream-1")
    state.apply(TranscriptUpdate("stream-1", "hello", True, 1))
    state.apply(TranscriptUpdate("stream-1", "how are you", True, 2))
    assert state.final_text == "hello how are you"


def test_sequence_must_increase() -> None:
    state = TranscriptState("stream-1")
    state.apply(TranscriptUpdate("stream-1", "hello", False, 1))
    with pytest.raises(TranscriptError):
        state.apply(TranscriptUpdate("stream-1", "hello again", True, 1))
