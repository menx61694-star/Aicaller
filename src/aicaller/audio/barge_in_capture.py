from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.format import NormalizedAudioFrame


class BargeInCaptureError(ValueError):
    pass


@dataclass(frozen=True)
class CapturedCallerSpeech:
    stream_sid: str
    frames: tuple[NormalizedAudioFrame, ...]
    started_at_ms: int
    ended_at_ms: int | None = None

    @property
    def payload(self) -> bytes:
        return b"".join(frame.payload for frame in self.frames)


class BargeInSpeechCapture:
    """Bounded capture of caller audio after a TTS interruption is detected."""

    def __init__(self, max_frames: int = 100) -> None:
        if max_frames < 1:
            raise BargeInCaptureError("max_frames must be positive")
        self.max_frames = max_frames
        self._frames: list[NormalizedAudioFrame] = []
        self._stream_sid: str | None = None
        self._started_at_ms: int | None = None

    def start(self, frame: NormalizedAudioFrame) -> None:
        self.reset()
        self._stream_sid = frame.stream_sid
        self._started_at_ms = frame.timestamp_ms
        self._frames.append(frame)

    def append(self, frame: NormalizedAudioFrame) -> None:
        if self._started_at_ms is None or self._stream_sid is None:
            raise BargeInCaptureError("capture has not started")
        if frame.stream_sid != self._stream_sid:
            raise BargeInCaptureError("stream_sid mismatch")
        if len(self._frames) >= self.max_frames:
            raise BufferError("barge-in capture capacity exceeded")
        self._frames.append(frame)

    def finish(self, frame: NormalizedAudioFrame) -> CapturedCallerSpeech:
        self.append(frame)
        captured = CapturedCallerSpeech(
            stream_sid=self._stream_sid or "",
            frames=tuple(self._frames),
            started_at_ms=self._started_at_ms or 0,
            ended_at_ms=frame.timestamp_ms,
        )
        self.reset()
        return captured

    def reset(self) -> None:
        self._frames = []
        self._stream_sid = None
        self._started_at_ms = None

    @property
    def active(self) -> bool:
        return self._started_at_ms is not None

    @property
    def frame_count(self) -> int:
        return len(self._frames)
