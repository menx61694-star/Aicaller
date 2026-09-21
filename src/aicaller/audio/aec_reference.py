from __future__ import annotations

from collections import deque

from aicaller.audio.format import AudioFormat, NormalizedAudioFrame
from aicaller.audio.output import AudioOutputFrame


class AECReferenceError(ValueError):
    pass


class AECReferenceBuffer:
    """Connection-local far-end reference history for acoustic echo cancellation.

    The buffer deliberately stores provider-neutral outbound PCM frames. AEC
    alignment/delay estimation is a separate concern and must not be guessed.
    """

    def __init__(self, max_frames: int = 200) -> None:
        if max_frames < 1:
            raise AECReferenceError("max_frames must be positive")
        self.max_frames = max_frames
        self._frames: deque[NormalizedAudioFrame] = deque()

    def add(self, frame: AudioOutputFrame, audio_format: AudioFormat) -> None:
        normalized = NormalizedAudioFrame(
            stream_sid=frame.stream_sid,
            sequence_number=frame.sequence_number,
            timestamp_ms=frame.timestamp_ms,
            payload=frame.payload,
            format=audio_format,
        )
        if self._frames and normalized.sequence_number is not None:
            self._frames = deque(
                item for item in self._frames
                if item.sequence_number != normalized.sequence_number
            )
        self._frames.append(normalized)
        while len(self._frames) > self.max_frames:
            self._frames.popleft()

    def latest(self, stream_sid: str) -> NormalizedAudioFrame | None:
        for frame in reversed(self._frames):
            if frame.stream_sid == stream_sid:
                return frame
        return None

    def find_aligned(
        self,
        stream_sid: str,
        sequence_number: int | None,
    ) -> NormalizedAudioFrame | None:
        """Return a reference only when the caller explicitly provides alignment."""
        if sequence_number is None:
            return None
        for frame in reversed(self._frames):
            if (
                frame.stream_sid == stream_sid
                and frame.sequence_number == sequence_number
            ):
                return frame
        return None

    def clear(self) -> None:
        self._frames.clear()

    @property
    def pending_count(self) -> int:
        return len(self._frames)
