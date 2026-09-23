import pytest

from aicaller.audio.agc import AGCConfig, AGCError, AutomaticGainController
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame

FMT = AudioFormat(AudioEncoding.PCM16_LE, 8000)


def frame(sample: int) -> NormalizedAudioFrame:
    return NormalizedAudioFrame("stream-1", 1, 20, int(sample).to_bytes(2, "little", signed=True) * 160, FMT)


def rms(payload: bytes) -> float:
    values = [int.from_bytes(payload[i:i+2], "little", signed=True) for i in range(0, len(payload), 2)]
    return (sum(v*v for v in values) / len(values)) ** 0.5 / 32768.0


def test_agc_boosts_quiet_audio_within_bounds() -> None:
    agc = AutomaticGainController(AGCConfig(target_rms=0.2, max_gain=4.0))
    result = agc.process(frame(1000))
    assert rms(result.payload) > rms(frame(1000).payload)
    assert agc.gain <= 4.0


def test_agc_preserves_metadata() -> None:
    agc = AutomaticGainController()
    source = frame(5000)
    result = agc.process(source)
    assert result.stream_sid == source.stream_sid
    assert result.sequence_number == source.sequence_number
    assert result.timestamp_ms == source.timestamp_ms
    assert result.format == source.format


def test_agc_rejects_non_pcm16() -> None:
    agc = AutomaticGainController()
    fmt = AudioFormat(AudioEncoding.MULAW, 8000, sample_width_bytes=1)
    with pytest.raises(AGCError):
        agc.process(NormalizedAudioFrame("stream-1", 1, 20, b"\x00", fmt))

def test_agc_never_exceeds_configured_max_gain() -> None:
    agc = AutomaticGainController(
        AGCConfig(target_rms=0.5, min_gain=0.25, max_gain=2.0, adaptation_rate=1.0)
    )
    result = agc.process(frame(100))
    assert agc.gain == 2.0
    assert rms(result.payload) <= rms(frame(100).payload) * 2.01


def test_agc_limits_attenuation_to_min_gain() -> None:
    agc = AutomaticGainController(
        AGCConfig(target_rms=0.01, min_gain=0.5, max_gain=2.0, adaptation_rate=1.0)
    )
    agc.process(frame(32000))
    assert agc.gain == 0.5


def test_agc_rejects_malformed_pcm16() -> None:
    agc = AutomaticGainController()
    with pytest.raises(AGCError, match="complete samples"):
        agc.process(NormalizedAudioFrame("stream-1", 1, 20, b"\\x00", FMT))
\n