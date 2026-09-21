from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.format import NormalizedAudioFrame
from aicaller.audio.vad import VADResult


class UtteranceError(ValueError):
    pass


@dataclass(frozen=True)
class AudioUtterance:
    stream_sid: str
    frames: tuple[NormalizedAudioFrame, ...]
    started_at_ms: int | None
    ended_at_ms: int | None

    @property
    def payload(self) -> bytes:
        return b"".join(frame.payload for frame in self.frames)


class UtteranceBuffer:
    """Collects one caller speech segment from normalized audio frames."""

    def __init__(self) -> None:
        self._frames: list[NormalizedAudioFrame] = []
        self._active = False
        self._started_at_ms: int | None = None

    def process(self, frame: NormalizedAudioFrame, vad: VADResult) -> AudioUtterance | None:
        if vad.speech_started:
            self._frames = []
            self._active = True
            self._started_at_ms = frame.timestamp_ms

        if self._active:
            self._frames.append(frame)

        if vad.speech_ended and self._active:
            utterance = AudioUtterance(
                stream_sid=frame.stream_sid,
                frames=tuple(self._frames),
                started_at_ms=self._started_at_ms,
                ended_at_ms=frame.timestamp_ms,
            )
            self._frames = []
            self._active = False
            self._started_at_ms = None
            return utterance

        return None

    def reset(self) -> None:
        self._frames = []
        self._active = False
        self._started_at_ms = None

    @property
    def active(self) -> bool:
        return self._active

    @property
    def frame_count(self) -> int:
        return len(self._frames)
