from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from aicaller.audio.frame import AudioFrame


@dataclass(frozen=True)
class JitterBufferConfig:
    max_frames: int = 50


class JitterBuffer:
    """Bounded sequence-aware buffer.

    Frames are released only when the next expected sequence is available.
    A missing packet is never fabricated here; packet-loss policy decides
    whether and when to skip a gap.
    """

    def __init__(self, config: JitterBufferConfig | None = None) -> None:
        self.config = config or JitterBufferConfig()
        if self.config.max_frames < 1:
            raise ValueError("max_frames must be positive")
        self._frames: dict[int, AudioFrame] = {}
        self._unsequenced: deque[AudioFrame] = deque()
        self._next_sequence: int | None = None

    def push(self, frame: AudioFrame) -> str:
        if frame.sequence_number is None:
            if len(self._unsequenced) >= self.config.max_frames:
                self._unsequenced.popleft()
            self._unsequenced.append(frame)
            return "unsequenced"

        sequence = frame.sequence_number
        if sequence in self._frames or (
            self._next_sequence is not None and sequence < self._next_sequence
        ):
            return "duplicate"

        if len(self._frames) >= self.config.max_frames:
            raise BufferError("jitter buffer capacity exceeded")

        self._frames[sequence] = frame
        if self._next_sequence is None:
            self._next_sequence = sequence
        return "buffered"

    def pop_ready(self) -> list[AudioFrame]:
        ready: list[AudioFrame] = []
        if self._next_sequence is None:
            return ready

        while self._next_sequence in self._frames:
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
            raise ValueError("cannot move jitter cursor backwards")
        self._next_sequence = sequence

    def pending_sequences(self) -> list[int]:
        return sorted(self._frames)

    def pop_unsequenced(self) -> AudioFrame | None:
        if not self._unsequenced:
            return None
        return self._unsequenced.popleft()

    @property
    def pending_count(self) -> int:
        return len(self._frames) + len(self._unsequenced)

    @property
    def next_sequence(self) -> int | None:
        return self._next_sequence
