from __future__ import annotations

from dataclasses import dataclass
import math

from aicaller.audio.format import AudioEncoding, NormalizedAudioFrame


class VADError(ValueError):
    """Raised when VAD receives an unsupported audio frame."""


@dataclass(frozen=True)
class VADConfig:
    speech_rms_threshold: float = 0.02
    min_speech_frames: int = 2
    min_silence_frames: int = 3

    def __post_init__(self) -> None:
        if not 0.0 <= self.speech_rms_threshold <= 1.0:
            raise ValueError("speech_rms_threshold must be between 0 and 1")
        if self.min_speech_frames < 1:
            raise ValueError("min_speech_frames must be positive")
        if self.min_silence_frames < 1:
            raise ValueError("min_silence_frames must be positive")


@dataclass(frozen=True)
class VADResult:
    is_speech: bool
    rms: float
    speech_started: bool = False
    speech_ended: bool = False


class EnergyVAD:
    """Deterministic PCM16 mono energy VAD.

    This is a conservative baseline, not a production noise classifier.
    Noise suppression and a provider/runtime-calibrated VAD can replace it
    without changing the normalized audio boundary.
    """

    def __init__(self, config: VADConfig | None = None) -> None:
        self.config = config or VADConfig()
        self._speech_frames = 0
        self._silence_frames = 0
        self._active = False

    def process(self, frame: NormalizedAudioFrame) -> VADResult:
        if frame.format.encoding != AudioEncoding.PCM16_LE:
            raise VADError("EnergyVAD currently requires PCM16_LE")
        if frame.format.channels != 1 or frame.format.sample_width_bytes != 2:
            raise VADError("EnergyVAD currently requires mono 16-bit audio")
        if len(frame.payload) % 2:
            raise VADError("PCM16_LE payload must contain complete samples")

        rms = self._rms_pcm16(frame.payload)
        candidate = rms >= self.config.speech_rms_threshold

        if candidate:
            self._speech_frames += 1
            self._silence_frames = 0
        else:
            self._silence_frames += 1
            self._speech_frames = 0

        started = False
        ended = False

        if not self._active and self._speech_frames >= self.config.min_speech_frames:
            self._active = True
            started = True
        elif self._active and self._silence_frames >= self.config.min_silence_frames:
            self._active = False
            ended = True

        return VADResult(
            is_speech=self._active,
            rms=rms,
            speech_started=started,
            speech_ended=ended,
        )

    @staticmethod
    def _rms_pcm16(payload: bytes) -> float:
        sample_count = len(payload) // 2
        if sample_count == 0:
            return 0.0
        total = 0.0
        for offset in range(0, len(payload), 2):
            sample = int.from_bytes(
                payload[offset:offset + 2],
                byteorder="little",
                signed=True,
            )
            normalized = sample / 32768.0
            total += normalized * normalized
        return math.sqrt(total / sample_count)
