import pytest

from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.noise_suppression import (
    AdaptiveNoiseSuppressor,
    NoiseSuppressionConfig,
    NoiseSuppressionError,
)



FMT = AudioFormat(AudioEncoding.PCM16_LE, 8000)


def frame(sample: int) -> NormalizedAudioFrame:
    return NormalizedAudioFrame("stream-1", 1, 20, int(sample).to_bytes(2, "little", signed=True) * 160, FMT)


def rms(payload: bytes) -> float:
    values = [
        int.from_bytes(payload[i:i + 2], "little", signed=True)
        for i in range(0, len(payload), 2)
    ]
    return (sum(v * v for v in values) / len(values)) ** 0.5


def test_noise_suppressor_reduces_stationary_noise() -> None:
    suppressor = AdaptiveNoiseSuppressor(
        NoiseSuppressionConfig(initial_noise_rms=0.05, minimum_gain=0.1)
    )
    result = suppressor.process(frame(1200))
    assert rms(result.payload) < rms(frame(1200).payload)


def test_noise_suppressor_preserves_frame_metadata() -> None:
    suppressor = AdaptiveNoiseSuppressor()
    source = frame(4000)
    result = suppressor.process(source)
    assert result.stream_sid == source.stream_sid
    assert result.sequence_number == source.sequence_number
    assert result.timestamp_ms == source.timestamp_ms
    assert result.format == source.format


def test_noise_suppressor_rejects_unsupported_format() -> None:
    suppressor = AdaptiveNoiseSuppressor()
    bad_format = AudioFormat(AudioEncoding.MULAW, 8000, sample_width_bytes=1)
    bad = NormalizedAudioFrame("stream-1", 1, 20, b"\x00", bad_format)
    with pytest.raises(NoiseSuppressionError):
        suppressor.process(bad)
