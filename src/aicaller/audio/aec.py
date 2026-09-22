from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame


class AECError(ValueError):
    pass


@dataclass(frozen=True)
class AECConfig:
    filter_length: int = 128
    step_size: float = 0.05
    regularization: float = 1e-6

    def __post_init__(self) -> None:
        if self.filter_length <= 0:
            raise AECError("filter_length must be positive")
        if not 0 < self.step_size <= 1:
            raise AECError("step_size must be in (0, 1]")
        if self.regularization <= 0:
            raise AECError("regularization must be positive")


class NLMSAcousticEchoCanceller:
    """Deterministic mono PCM16 adaptive echo canceller.

    The reference signal is the audio sent toward the caller. The input frame
    is the microphone/telephony return path. No codec conversion or resampling
    is performed here; callers must provide the same PCM16 format on both
    paths.
    """

    def __init__(self, config: AECConfig | None = None) -> None:
        self.config = config or AECConfig()
        self._weights = [0.0] * self.config.filter_length
        self._reference: list[float] = [0.0] * self.config.filter_length

    @staticmethod
    def _decode_pcm16(payload: bytes) -> list[float]:
        if len(payload) % 2:
            raise AECError("PCM16 payload must contain complete samples")
        return [
            int.from_bytes(payload[i:i + 2], "little", signed=True) / 32768.0
            for i in range(0, len(payload), 2)
        ]

    @staticmethod
    def _encode_pcm16(samples: list[float]) -> bytes:
        output = bytearray()
        for sample in samples:
            clipped = max(-1.0, min(0.999969482421875, sample))
            value = round(clipped * 32768.0)
            output.extend(value.to_bytes(2, "little", signed=True))
        return bytes(output)

    def process(
        self,
        *,
        near_end: NormalizedAudioFrame,
        far_end_reference: NormalizedAudioFrame,
    ) -> NormalizedAudioFrame:
        if near_end.stream_sid != far_end_reference.stream_sid:
            raise AECError("near-end and reference stream IDs must match")
        if near_end.format != far_end_reference.format:
            raise AECError("near-end and reference formats must match")
        fmt: AudioFormat = near_end.format
        if fmt.encoding != AudioEncoding.PCM16_LE or fmt.channels != 1:
            raise AECError("AEC currently requires mono PCM16_LE")
        near = self._decode_pcm16(near_end.payload)
        far = self._decode_pcm16(far_end_reference.payload)
        if len(near) != len(far):
            raise AECError("near-end and reference frame lengths must match")

        out: list[float] = []
        for sample, reference in zip(near, far):
            self._reference.pop(0)
            self._reference.append(reference)
            prediction = sum(w * x for w, x in zip(self._weights, reversed(self._reference)))
            error = sample - prediction
            power = sum(x * x for x in self._reference) + self.config.regularization
            gain = self.config.step_size * error / power
            for index, x in enumerate(reversed(self._reference)):
                self._weights[index] += gain * x
            out.append(error)

        return NormalizedAudioFrame(
            stream_sid=near_end.stream_sid,
            sequence_number=near_end.sequence_number,
            timestamp_ms=near_end.timestamp_ms,
            payload=self._encode_pcm16(out),
            format=near_end.format,
        )
