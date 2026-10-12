from __future__ import annotations

from aicaller.audio.format import (
    AudioEncoding,
    AudioFormat,
)
from aicaller.audio.utterance import AudioUtterance


_MULAW_BIAS = 0x84
_MULAW_CLIP = 32635
_SEGMENT_END = (0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF, 0x1FFF, 0x3FFF, 0x7FFF)


class AudioCodecError(ValueError):
    pass


def encode_pcm16le_to_mulaw(payload: bytes) -> bytes:
    """Encode mono little-endian PCM16 samples into G.711 μ-law bytes."""
    if len(payload) % 2:
        raise AudioCodecError("PCM16 payload must contain complete 2-byte samples")

    encoded = bytearray()
    for offset in range(0, len(payload), 2):
        sample = int.from_bytes(payload[offset : offset + 2], "little", signed=True)
        sign = 0x80 if sample < 0 else 0
        magnitude = -sample if sample < 0 else sample
        magnitude = min(magnitude, _MULAW_CLIP) + _MULAW_BIAS

        exponent = 0
        while exponent < 7 and magnitude > _SEGMENT_END[exponent]:
            exponent += 1
        mantissa = (magnitude >> (exponent + 3)) & 0x0F
        encoded.append((~(sign | (exponent << 4) | mantissa)) & 0xFF)
    return bytes(encoded)


def decode_mulaw_to_pcm16le(payload: bytes) -> bytes:
    """Decode G.711 μ-law bytes into mono little-endian PCM16 samples."""
    decoded = bytearray()
    for value in payload:
        value = (~value) & 0xFF
        sign = value & 0x80
        exponent = (value >> 4) & 0x07
        mantissa = value & 0x0F
        magnitude = ((mantissa << 3) + _MULAW_BIAS) << exponent
        magnitude -= _MULAW_BIAS
        sample = -magnitude if sign else magnitude
        decoded.extend(int(sample).to_bytes(2, "little", signed=True))
    return bytes(decoded)


def encode_utterance_pcm16le_to_mulaw(utterance: AudioUtterance) -> AudioUtterance:
    """Convert each PCM16 utterance frame to the 8 kHz-compatible μ-law codec."""
    if not utterance.frames:
        raise AudioCodecError("utterance must contain at least one frame")

    converted_frames = []
    for frame in utterance.frames:
        if frame.format.encoding != AudioEncoding.PCM16_LE:
            raise AudioCodecError("utterance frames must use PCM16_LE")
        if frame.format.sample_rate_hz != 8000:
            raise AudioCodecError("μ-law telephony conversion requires 8000 Hz input")
        converted_frames.append(
            type(frame)(
                stream_sid=frame.stream_sid,
                sequence_number=frame.sequence_number,
                timestamp_ms=frame.timestamp_ms,
                payload=encode_pcm16le_to_mulaw(frame.payload),
                format=AudioFormat(AudioEncoding.MULAW, 8000, sample_width_bytes=1),
            )
        )
    return AudioUtterance(
        stream_sid=utterance.stream_sid,
        frames=tuple(converted_frames),
        started_at_ms=utterance.started_at_ms,
        ended_at_ms=utterance.ended_at_ms,
    )
