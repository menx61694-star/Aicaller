import pytest

from aicaller.ai.stt import STTError, TranscriptEventAdapter, UnconfiguredSTT
from aicaller.ai.transcript import TranscriptUpdate
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.utterance import AudioUtterance


def utterance() -> AudioUtterance:
    fmt = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    frame = NormalizedAudioFrame("stream-1", 1, 20, b"\x00\x01", fmt)
    return AudioUtterance("stream-1", (frame,), 20, 40)


@pytest.mark.asyncio
async def test_unconfigured_stt_fails_closed() -> None:
    with pytest.raises(STTError, match="not configured"):
        await UnconfiguredSTT().transcribe(utterance())


def test_streaming_stt_event_adapter_accepts_partial_and_final() -> None:
    adapter = TranscriptEventAdapter("stream-1")
    partial = adapter.consume(
        TranscriptUpdate("stream-1", "hello", False, 1)
    )
    final = adapter.consume(
        TranscriptUpdate("stream-1", "hello world", True, 2)
    )

    assert partial.text == "hello"
    assert not partial.is_final
    assert final.text == "hello world"
    assert final.is_final


def test_streaming_stt_event_adapter_rejects_stale_sequence() -> None:
    adapter = TranscriptEventAdapter("stream-1")
    adapter.consume(TranscriptUpdate("stream-1", "hello", False, 2))

    with pytest.raises(STTError, match="sequence must increase"):
        adapter.consume(TranscriptUpdate("stream-1", "stale", True, 2))


def test_streaming_stt_event_adapter_rejects_stream_mismatch() -> None:
    adapter = TranscriptEventAdapter("stream-1")

    with pytest.raises(STTError, match="stream mismatch"):
        adapter.consume(TranscriptUpdate("stream-2", "hello", False, 1))
