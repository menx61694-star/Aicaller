from __future__ import annotations

import math
from dataclasses import dataclass

from aicaller.audio.format import AudioEncoding, NormalizedAudioFrame


class AGCError(ValueError):
    pass


@dataclass(frozen=True)
class AGCConfig:
    target_rms: float = 0.12
    max_gain: float = 4.0
    min_gain: float = 0.25
    adaptation_rate: float = 0.2

    def __post_init__(self) -> None:
        if not 0.0 < self.target_rms <= 1.0:
            raise AGCError("target_rms must be in (0, 1]")
        if self.min_gain <= 0 or self.max_gain < self.min_gain:
            raise AGCError("invalid gain limits")
        if not 0.0 < self.adaptation_rate <= 1.0:
            raise AGCError("adaptation_rate must be in (0, 1]")


class AutomaticGainController:
    """Bounded frame-level gain normalization for PCM16 mono audio."""

    def __init__(self, config: AGCConfig | None = None) -> None:
        self.config = config or AGCConfig()
        self._gain = 1.0

    @property
    def gain(self) -> float:
        return self._gain

    def process(self, frame: NormalizedAudioFrame) -> NormalizedAudioFrame:
        if frame.format.encoding != AudioEncoding.PCM16_LE:
            raise AGCError("AGC requires PCM16_LE")
        if frame.format.channels != 1 or frame.format.sample_width_bytes != 2:
            raise AGCError("AGC requires mono 16-bit audio")
        if len(frame.payload) % 2:
            raise AGCError("PCM16_LE payload must contain complete samples")
        if not frame.payload:
            return frame

        rms = self._rms(frame.payload)
        if rms > 0:
            desired = self.config.target_rms / rms
            desired = max(self.config.min_gain, min(self.config.max_gain, desired))
            rate = self.config.adaptation_rate
            self._gain = (1.0 - rate) * self._gain + rate * desired

        return NormalizedAudioFrame(
            frame.stream_sid,
            frame.sequence_number,
            frame.timestamp_ms,
            self._apply_gain(frame.payload, self._gain),
            frame.format,
        )

    @staticmethod
    def _rms(payload: bytes) -> float:
        count = len(payload) // 2
        if not count:
            return 0.0
        total = 0.0
        for i in range(0, len(payload), 2):
            value = int.from_bytes(payload[i:i+2], "little", signed=True) / 32768.0
            total += value * value
        return math.sqrt(total / count)

    @staticmethod
    def _apply_gain(payload: bytes, gain: float) -> bytes:
        out = bytearray()
        for i in range(0, len(payload), 2):
            value = int.from_bytes(payload[i:i+2], "little", signed=True)
            value = max(-32768, min(32767, round(value * gain)))
            out.extend(value.to_bytes(2, "little", signed=True))
        return bytes(out)
