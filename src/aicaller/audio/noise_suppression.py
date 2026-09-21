from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.format import AudioEncoding, NormalizedAudioFrame


class NoiseSuppressionError(ValueError):
    pass


@dataclass(frozen=True)
class NoiseSuppressionConfig:
    initial_noise_rms: float = 0.005
    adaptation_rate: float = 0.05
    suppression_ratio: float = 0.35
    minimum_gain: float = 0.15

    def __post_init__(self) -> None:
        if not 0.0 < self.initial_noise_rms <= 1.0:
            raise NoiseSuppressionError("initial_noise_rms must be in (0, 1]")
        if not 0.0 < self.adaptation_rate <= 1.0:
            raise NoiseSuppressionError("adaptation_rate must be in (0, 1]")
        if not 0.0 < self.suppression_ratio <= 1.0:
            raise NoiseSuppressionError("suppression_ratio must be in (0, 1]")
        if not 0.0 <= self.minimum_gain <= 1.0:
            raise NoiseSuppressionError("minimum_gain must be between 0 and 1")


class AdaptiveNoiseSuppressor:
    """Deterministic stationary-noise suppressor for mono PCM16 audio.

    This is a conservative baseline: it estimates a slowly changing noise
    floor from low-energy frames and applies a soft frame-level gain. It is
    intentionally not presented as a production denoiser; a calibrated DSP
    or provider noise-suppression engine can replace this boundary later.
    """

    def __init__(self, config: NoiseSuppressionConfig | None = None) -> None:
        self.config = config or NoiseSuppressionConfig()
        self._noise_rms = self.config.initial_noise_rms

    @property
    def noise_rms(self) -> float:
        return self._noise_rms

    def process(self, frame: NormalizedAudioFrame) -> NormalizedAudioFrame:
        if frame.format.encoding != AudioEncoding.PCM16_LE:
            raise NoiseSuppressionError("noise suppression requires PCM16_LE")
        if frame.format.channels != 1 or frame.format.sample_width_bytes != 2:
            raise NoiseSuppressionError("noise suppression requires mono 16-bit audio")
        if len(frame.payload) % 2:
            raise NoiseSuppressionError("PCM16_LE payload must contain complete samples")
        if not frame.payload:
            return frame

        rms = self._rms(frame.payload)
        # Only low-energy frames update the floor; this avoids learning speech
        # as stationary noise.
        if rms <= self._noise_rms * 2.0:
            rate = self.config.adaptation_rate
            self._noise_rms = (1.0 - rate) * self._noise_rms + rate * rms

        threshold = max(self._noise_rms * 1.5, 1e-6)
        if rms <= threshold:
            gain = self.config.minimum_gain
        else:
            excess = min(1.0, (rms - threshold) / max(threshold, 1e-6))
            gain = max(
                self.config.minimum_gain,
                1.0 - self.config.suppression_ratio * (1.0 - min(1.0, excess)),
            )

        payload = self._apply_gain(frame.payload, gain)
        return NormalizedAudioFrame(
            stream_sid=frame.stream_sid,
            sequence_number=frame.sequence_number,
            timestamp_ms=frame.timestamp_ms,
            payload=payload,
            format=frame.format,
        )

    @staticmethod
    def _rms(payload: bytes) -> float:
        total = 0.0
        count = len(payload) // 2
        for offset in range(0, len(payload), 2):
            sample = int.from_bytes(payload[offset:offset + 2], "little", signed=True) / 32768.0
            total += sample * sample
        return (total / count) ** 0.5 if count else 0.0

    @staticmethod
    def _apply_gain(payload: bytes, gain: float) -> bytes:
        output = bytearray()
        for offset in range(0, len(payload), 2):
            sample = int.from_bytes(payload[offset:offset + 2], "little", signed=True)
            value = max(-32768, min(32767, int(round(sample * gain))))
            output.extend(value.to_bytes(2, "little", signed=True))
        return bytes(output)
