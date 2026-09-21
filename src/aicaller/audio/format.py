from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.frame import AudioFrame


class AudioFormatError(ValueError):
    """Raised when an audio format cannot be normalized safely."""


class AudioEncoding:
    PCM16_LE = "pcm16le"
    MULAW = "mulaw"


@dataclass(frozen=True)
class AudioFormat:
    encoding: str
    sample_rate_hz: int
    channels: int = 1
    sample_width_bytes: int = 2

    def __post_init__(self) -> None:
        if self.encoding not in {AudioEncoding.PCM16_LE, AudioEncoding.MULAW}:
            raise AudioFormatError(f"unsupported audio encoding: {self.encoding}")
        if self.sample_rate_hz <= 0:
            raise AudioFormatError("sample_rate_hz must be positive")
        if self.channels != 1:
            raise AudioFormatError("only mono audio is supported at this boundary")
        if self.encoding == AudioEncoding.PCM16_LE and self.sample_width_bytes != 2:
            raise AudioFormatError("PCM16_LE requires 2-byte samples")
        if self.encoding == AudioEncoding.MULAW and self.sample_width_bytes != 1:
            raise AudioFormatError("MULAW requires 1-byte samples")


@dataclass(frozen=True)
class NormalizedAudioFrame:
    """Internal audio representation consumed by VAD/AI stages."""

    stream_sid: str
    sequence_number: int | None
    timestamp_ms: int | None
    payload: bytes
    format: AudioFormat


class AudioNormalizer:
    """Normalize supported telephony frames without hiding codec assumptions.

    Resampling/transcoding is intentionally not performed here yet. The
    selected provider media format must be explicitly known before conversion.
    """

    def __init__(self, target_format: AudioFormat) -> None:
        self.target_format = target_format

    def normalize(
        self,
        frame: AudioFrame,
        source_format: AudioFormat,
    ) -> NormalizedAudioFrame:
        if source_format != self.target_format:
            raise AudioFormatError(
                "source and target formats differ; explicit transcoding is "
                "required before normalization"
            )
        return NormalizedAudioFrame(
            stream_sid=frame.stream_sid,
            sequence_number=frame.sequence_number,
            timestamp_ms=frame.timestamp_ms,
            payload=frame.payload,
            format=self.target_format,
        )
