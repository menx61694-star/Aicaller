import pytest

from aicaller.ai.tts import TTSChunk, TTSError, TTSStreamState, UnconfiguredStreamingTTS


@pytest.mark.asyncio
async def test_unconfigured_tts_fails_closed() -> None:
    with pytest.raises(TTSError, match="not configured"):
        await UnconfiguredStreamingTTS().synthesize("hello", language="en")


def test_tts_stream_accumulates_chunks() -> None:
    state = TTSStreamState()
    state.apply(TTSChunk(b"abc", sequence=1))
    state.apply(TTSChunk(b"def", sequence=2, is_final=True))
    assert state.audio == b"abcdef"
    assert state.finished


def test_tts_stream_rejects_stale_sequence() -> None:
    state = TTSStreamState()
    state.apply(TTSChunk(b"abc", sequence=1))
    with pytest.raises(TTSError, match="must increase"):
        state.apply(TTSChunk(b"old", sequence=1))


def test_tts_stream_rejects_empty_chunk() -> None:
    state = TTSStreamState()
    with pytest.raises(TTSError, match="must not be empty"):
        state.apply(TTSChunk(b"", sequence=1))


def test_tts_stream_rejects_chunk_after_final() -> None:
    state = TTSStreamState()
    state.apply(TTSChunk(b"done", sequence=1, is_final=True))
    with pytest.raises(TTSError, match="already finished"):
        state.apply(TTSChunk(b"late", sequence=2))
