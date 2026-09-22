from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.utterance import UtteranceBuffer
from aicaller.audio.vad import VADResult

FMT = AudioFormat(AudioEncoding.PCM16_LE, 8000)


def frame(ts: int) -> NormalizedAudioFrame:
    return NormalizedAudioFrame("stream-1", ts, ts, b"ab", FMT)


def test_utterance_collects_frames_until_speech_ends() -> None:
    buffer = UtteranceBuffer()
    assert buffer.process(frame(0), VADResult(False, 0.0)) is None
    assert buffer.process(frame(20), VADResult(True, 0.2, speech_started=True)) is None
    assert buffer.process(frame(40), VADResult(True, 0.2)) is None
    result = buffer.process(frame(60), VADResult(False, 0.0, speech_ended=True))
    assert result is not None
    assert len(result.frames) == 3
    assert result.payload == b"ababab"
    assert result.started_at_ms == 20
    assert result.ended_at_ms == 60
    assert not buffer.active


def test_reset_discards_partial_utterance() -> None:
    buffer = UtteranceBuffer()
    buffer.process(frame(20), VADResult(True, 0.2, speech_started=True))
    buffer.reset()
    assert not buffer.active
    assert buffer.frame_count == 0
