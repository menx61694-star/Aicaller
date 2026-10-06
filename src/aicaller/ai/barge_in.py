from __future__ import annotations

from dataclasses import dataclass


class BargeInError(ValueError):
    pass


@dataclass(frozen=True)
class BargeInConfig:
    speech_frames_required: int = 2
    min_speech_confidence: float = 0.5

    def __post_init__(self) -> None:
        if self.speech_frames_required < 1:
            raise BargeInError("speech_frames_required must be positive")
        if not 0.0 <= self.min_speech_confidence <= 1.0:
            raise BargeInError("min_speech_confidence must be between 0 and 1")


class BargeInDetector:
    """Deterministic hysteresis gate for caller speech detected during TTS."""

    def __init__(self, config: BargeInConfig | None = None) -> None:
        self.config = config or BargeInConfig()
        self._speech_frames = 0
        self._triggered = False

    def observe(self, *, is_speech: bool, confidence: float) -> bool:
        if not 0.0 <= confidence <= 1.0:
            raise BargeInError("confidence must be between 0 and 1")

        if is_speech and confidence >= self.config.min_speech_confidence:
            self._speech_frames += 1
            if self._speech_frames >= self.config.speech_frames_required:
                self._triggered = True
        else:
            self._speech_frames = 0

        return self._triggered

    @property
    def triggered(self) -> bool:
        return self._triggered

    def reset(self) -> None:
        self._speech_frames = 0
        self._triggered = False
