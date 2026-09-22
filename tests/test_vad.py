import pytest

from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.vad import EnergyVAD, VADConfig, VADError

FMT = AudioFormat(AudioEncoding.PCM16_LE, 8000)


def frame(sample: int) -> NormalizedAudioFrame:
    value = int(sample).to_bytes(2, "little", signed=True)
    return NormalizedAudioFrame("stream-1", 1, 20, value * 160, FMT)


def test_vad_requires_consecutive_speech_frames() -> None:
    vad = EnergyVAD(VADConfig(speech_rms_threshold=0.1, min_speech_frames=2))
    assert not vad.process(frame(0)).speech_started
    assert not vad.process(frame(5000)).speech_started
    result = vad.process(frame(5000))
    assert result.speech_started
    assert result.is_speech


def test_vad_requires_consecutive_silence_frames_to_end() -> None:
    vad = EnergyVAD(
        VADConfig(
            speech_rms_threshold=0.1,
            min_speech_frames=1,
            min_silence_frames=2,
        )
    )
    assert vad.process(frame(5000)).speech_started
    assert not vad.process(frame(0)).speech_ended
    result = vad.process(frame(0))
    assert result.speech_ended
    assert not result.is_speech


def test_vad_rejects_odd_pcm_payload() -> None:
    vad = EnergyVAD()
    bad = NormalizedAudioFrame("stream-1", 1, 20, b"\x00", FMT)
    with pytest.raises(VADError):
        vad.process(bad)
