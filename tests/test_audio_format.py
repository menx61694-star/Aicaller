import pytest

from aicaller.audio.format import (
    AudioEncoding,
    AudioFormat,
    AudioFormatError,
    AudioNormalizer,
)
from aicaller.audio.frame import AudioFrame


def frame() -> AudioFrame:
    return AudioFrame("stream-1", 1, 20, b"\x00\x01" * 80)


def test_normalizer_preserves_matching_pcm16_format() -> None:
    fmt = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    result = AudioNormalizer(fmt).normalize(frame(), fmt)
    assert result.payload == frame().payload
    assert result.format == fmt


def test_normalizer_rejects_unknown_encoding() -> None:
    with pytest.raises(AudioFormatError):
        AudioFormat("unknown", 8000)


def test_normalizer_rejects_format_mismatch_instead_of_guessing() -> None:
    source = AudioFormat(AudioEncoding.MULAW, 8000, sample_width_bytes=1)
    target = AudioFormat(AudioEncoding.PCM16_LE, 16000)
    with pytest.raises(AudioFormatError):
        AudioNormalizer(target).normalize(frame(), source)
