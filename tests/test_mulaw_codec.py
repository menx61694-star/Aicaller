import pytest

from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.mulaw import (
    AudioCodecError,
    decode_mulaw_to_pcm16le,
    encode_pcm16le_to_mulaw,
    encode_utterance_pcm16le_to_mulaw,
)
from aicaller.audio.utterance import AudioUtterance


def pcm16(*samples: int) -> bytes:
    return b"".join(sample.to_bytes(2, "little", signed=True) for sample in samples)


def test_pcm16_to_mulaw_known_g711_vectors() -> None:
    assert encode_pcm16le_to_mulaw(pcm16(0, 32124, -32124)) == bytes((0xFF, 0x80, 0x00))


def test_mulaw_decode_returns_pcm16_samples() -> None:
    decoded = decode_mulaw_to_pcm16le(bytes((0xFF, 0x80, 0x00)))

    assert len(decoded) == 6
    assert int.from_bytes(decoded[0:2], "little", signed=True) == 0
    assert int.from_bytes(decoded[2:4], "little", signed=True) > 30000
    assert int.from_bytes(decoded[4:6], "little", signed=True) < -30000


def test_pcm16_encoder_rejects_incomplete_sample() -> None:
    with pytest.raises(AudioCodecError, match="complete 2-byte"):
        encode_pcm16le_to_mulaw(b"\x01")


def test_utterance_encoder_preserves_stream_timing_and_sequence() -> None:
    source_format = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    frame = NormalizedAudioFrame("stream-1", 3, 40, pcm16(0, 1000, -1000), source_format)
    utterance = AudioUtterance("stream-1", (frame,), 20, 60)

    encoded = encode_utterance_pcm16le_to_mulaw(utterance)

    assert encoded.stream_sid == "stream-1"
    assert encoded.started_at_ms == 20
    assert encoded.ended_at_ms == 60
    assert encoded.frames[0].sequence_number == 3
    assert encoded.frames[0].timestamp_ms == 40
    assert encoded.frames[0].format.encoding == AudioEncoding.MULAW
    assert encoded.frames[0].format.sample_width_bytes == 1
    assert len(encoded.payload) == 3


def test_utterance_encoder_rejects_non_pcm16_or_non_8khz_input() -> None:
    mulaw = AudioFormat(AudioEncoding.MULAW, 8000, sample_width_bytes=1)
    frame = NormalizedAudioFrame("stream-1", 1, 20, b"\xff", mulaw)
    with pytest.raises(AudioCodecError, match="PCM16_LE"):
        encode_utterance_pcm16le_to_mulaw(
            AudioUtterance("stream-1", (frame,), 20, 40)
        )

    pcm16_16khz = AudioFormat(AudioEncoding.PCM16_LE, 16000)
    frame = NormalizedAudioFrame("stream-1", 1, 20, pcm16(1), pcm16_16khz)
    with pytest.raises(AudioCodecError, match="8000 Hz"):
        encode_utterance_pcm16le_to_mulaw(
            AudioUtterance("stream-1", (frame,), 20, 40)
        )
