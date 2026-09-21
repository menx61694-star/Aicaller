from __future__ import annotations

from collections import deque
from dataclasses import dataclass


class AudioOutputError(ValueError):
    """Raised when an outbound audio frame is invalid."""


@dataclass(frozen=True)
class AudioOutputFrame:
    """Provider-neutral outbound audio frame.

    Payload is already encoded for the selected media format. Provider adapters
    are responsible for converting this frame to their wire representation.
    """

    stream_sid: str
    sequence_number: int
    payload: bytes
    timestamp_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.stream_sid:
            raise AudioOutputError("stream_sid is required")
        if self.sequence_number < 0:
            raise AudioOutputError("sequence_number cannot be negative")
        if not self.payload:
            raise AudioOutputError("payload cannot be empty")
        if self.timestamp_ms is not None and self.timestamp_ms < 0:
            raise AudioOutputError("timestamp_ms cannot be negative")


@dataclass(frozen=True)
class AudioOutputConfig:
    max_frames: int = 50

    def __post_init__(self) -> None:
        if self.max_frames < 1:
            raise ValueError("max_frames must be positive")


class OutboundAudioPipeline:
    """Bounded, sequence-aware outbound audio queue.

    The pipeline owns ordering and backpressure at the provider-neutral
    boundary. It does not choose a codec or send network frames.
    """

    def __init__(self, config: AudioOutputConfig | None = None) -> None:
        self.config = config or AudioOutputConfig()
        self._frames: dict[int, AudioOutputFrame] = {}
        self._unsequenced: deque[AudioOutputFrame] = deque()
        self._next_sequence: int | None = None

    def enqueue(self, frame: AudioOutputFrame) -> str:
        if frame.sequence_number in self._frames or (
            self._next_sequence is not None
            and frame.sequence_number < self._next_sequence
        ):
            return "duplicate"

        if len(self._frames) >= self.config.max_frames:
            raise BufferError("output buffer capacity exceeded")

        self._frames[frame.sequence_number] = frame
        if self._next_sequence is None:
            self._next_sequence = frame.sequence_number
        return "queued"

    def pop_ready(self, limit: int | None = None) -> list[AudioOutputFrame]:
        if limit is not None and limit < 1:
            raise ValueError("limit must be positive")

        ready: list[AudioOutputFrame] = []
        if self._next_sequence is None:
            return ready

        while self._next_sequence in self._frames:
            if limit is not None and len(ready) >= limit:
                break
            ready.append(self._frames.pop(self._next_sequence))
            self._next_sequence += 1
        return ready

    def skip_to(self, sequence: int) -> None:
        if sequence < 0:
            raise ValueError("sequence cannot be negative")
        if self._next_sequence is None:
            self._next_sequence = sequence
            return
        if sequence < self._next_sequence:
            raise ValueError("cannot move output cursor backwards")
        self._next_sequence = sequence

    def clear(self) -> list[AudioOutputFrame]:
        frames = [self._frames[key] for key in sorted(self._frames)]
        self._frames.clear()
        self._unsequenced.clear()
        self._next_sequence = None
        return frames

    @property
    def pending_count(self) -> int:
        return len(self._frames) + len(self._unsequenced)

    @property
    def next_sequence(self) -> int | None:
        return self._next_sequence
