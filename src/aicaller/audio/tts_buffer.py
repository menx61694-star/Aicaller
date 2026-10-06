from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.output import AudioOutputFrame, OutboundAudioPipeline


class TTSBufferError(RuntimeError):
    """Raised when an invalid TTS buffer operation is requested."""


@dataclass(frozen=True)
class TTSFlushResult:
    generation: int
    discarded_frames: int


class TTSOutputBuffer:
    """Provider-neutral TTS output buffer with explicit flush generations."""

    def __init__(self, pipeline: OutboundAudioPipeline | None = None) -> None:
        self.pipeline = pipeline or OutboundAudioPipeline()
        self._generation = 0

    @property
    def generation(self) -> int:
        return self._generation

    def enqueue(self, frame: AudioOutputFrame, generation: int | None = None) -> str:
        active_generation = self._generation if generation is None else generation
        if active_generation != self._generation:
            return "stale_generation"
        return self.pipeline.enqueue(frame)

    def flush(self) -> TTSFlushResult:
        discarded = self.pipeline.clear()
        self._generation += 1
        return TTSFlushResult(
            generation=self._generation,
            discarded_frames=len(discarded),
        )
