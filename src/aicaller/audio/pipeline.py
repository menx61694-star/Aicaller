from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.frame import AudioFrame
from aicaller.audio.jitter_buffer import JitterBuffer, JitterBufferConfig
from aicaller.audio.packet_loss import (
    PacketLossHandler,
    PacketLossPolicy,
    silence_frame,
)


@dataclass(frozen=True)
class AudioPipelineConfig:
    jitter_max_frames: int = 50
    max_gap_frames: int = 3
    silence_frame_bytes: int = 160

    def __post_init__(self) -> None:
        if self.silence_frame_bytes <= 0:
            raise ValueError("silence_frame_bytes must be positive")


class InboundAudioPipeline:
    """Deterministic inbound media path before codec/VAD/AI processing.

    Flow: frame -> jitter buffer -> bounded gap decision -> ordered output.
    The pipeline never silently drops a frame because of jitter.
    """

    def __init__(self, config: AudioPipelineConfig | None = None) -> None:
        self.config = config or AudioPipelineConfig()
        self.jitter = JitterBuffer(
            JitterBufferConfig(max_frames=self.config.jitter_max_frames)
        )
        self.packet_loss = PacketLossHandler(
            PacketLossPolicy(max_gap_frames=self.config.max_gap_frames)
        )

    def ingest(self, frame: AudioFrame) -> list[AudioFrame]:
        self.jitter.push(frame)
        ready = self.jitter.pop_ready()
        if ready:
            return ready

        next_sequence = self.jitter.next_sequence
        if next_sequence is None:
            return []

        pending_sequences = self._pending_sequences()
        if not self.packet_loss.should_skip_gap(
            next_sequence=next_sequence,
            buffered_sequences=pending_sequences,
        ):
            return []

        missing = next_sequence
        advanced = self.packet_loss.skip_gap(next_sequence)
        if advanced is None:
            return []

        # The jitter buffer owns the sequence cursor. Advancing it is done
        # through a single explicit method so gap recovery remains observable.
        self.jitter.skip_to(advanced)
        return [
            silence_frame(
                stream_sid=frame.stream_sid,
                sequence_number=missing,
                timestamp_ms=frame.timestamp_ms,
                byte_length=self.config.silence_frame_bytes,
            )
        ]

    def _pending_sequences(self) -> list[int]:
        return self.jitter.pending_sequences()

    def flush(self) -> list[AudioFrame]:
        return self.jitter.pop_ready()
