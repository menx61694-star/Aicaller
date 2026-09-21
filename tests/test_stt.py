import pytest

from aicaller.ai.stt import STTError, UnconfiguredSTT
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
