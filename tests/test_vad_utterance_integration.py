from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.utterance import UtteranceBuffer
from aicaller.audio.vad import EnergyVAD, VADConfig

FMT = AudioFormat(AudioEncoding.PCM16_LE, 8000)


def frame(sequence: int, timestamp: int, sample: int) -> NormalizedAudioFrame:
    return NormalizedAudioFrame(
        "stream-1",
        sequence,
        timestamp,
        int(sample).to_bytes(2, "little", signed=True) * 160,
        FMT,
    )


def test_vad_and_utterance_boundary_forms_one_segment() -> None:
    vad = EnergyVAD(VADConfig(speech_rms_threshold=0.1, min_speech_frames=1, min_silence_frames=2))
    buffer = UtteranceBuffer()

    assert buffer.process(frame(1, 0, 5000), vad.process(frame(1, 0, 5000))) is None
    assert buffer.process(frame(2, 20, 5000), vad.process(frame(2, 20, 5000))) is None
    result = buffer.process(frame(3, 40, 0), vad.process(frame(3, 40, 0)))
    assert result is None
    result = buffer.process(frame(4, 60, 0), vad.process(frame(4, 60, 0)))

    assert result is not None
    assert result.stream_sid == "stream-1"
    assert result.started_at_ms == 0
    assert result.ended_at_ms == 60
    assert len(result.frames) == 4
