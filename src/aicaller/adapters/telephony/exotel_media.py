from __future__ import annotations

import base64
import json
from dataclasses import dataclass

from aicaller.audio.output import AudioOutputFrame


class ExotelMediaError(ValueError):
    """Raised when an outbound Exotel media message is invalid."""


@dataclass(frozen=True)
class ExotelMediaConfig:
    """Constraints for bidirectional AgentStream outbound media."""

    min_chunk_bytes: int = 320
    max_chunk_bytes: int = 100_000
    required_chunk_multiple: int = 320

    def __post_init__(self) -> None:
        if self.min_chunk_bytes <= 0:
            raise ValueError("min_chunk_bytes must be positive")
        if self.max_chunk_bytes < self.min_chunk_bytes:
            raise ValueError("max_chunk_bytes must be >= min_chunk_bytes")
        if self.required_chunk_multiple <= 0:
            raise ValueError("required_chunk_multiple must be positive")


class ExotelMediaAdapter:
    """Encode provider-neutral PCM output into AgentStream media JSON.

    Exotel's bidirectional AgentStream expects base64 audio in media events.
    Chunk-size validation is performed here, at the provider boundary, rather
    than inside the provider-neutral audio pipeline.
    """

    def __init__(self, config: ExotelMediaConfig | None = None) -> None:
        self.config = config or ExotelMediaConfig()

    def encode_media(
        self,
        frame: AudioOutputFrame,
        *,
        sequence_number: int,
        timestamp_ms: int | None = None,
    ) -> str:
        self._validate_payload(frame.payload)
        if sequence_number < 0:
            raise ExotelMediaError("sequence_number cannot be negative")
        timestamp = (
            frame.timestamp_ms if timestamp_ms is None else timestamp_ms
        )
        if timestamp is not None and timestamp < 0:
            raise ExotelMediaError("timestamp_ms cannot be negative")

        message = {
            "event": "media",
            "sequence_number": sequence_number,
            "stream_sid": frame.stream_sid,
            "media": {
                "chunk": frame.sequence_number,
                "timestamp": str(timestamp) if timestamp is not None else "0",
                "payload": base64.b64encode(frame.payload).decode("ascii"),
            },
        }
        return json.dumps(message, separators=(",", ":"))

    def encode_mark(self, stream_sid: str, *, sequence_number: int, name: str) -> str:
        if not stream_sid:
            raise ExotelMediaError("stream_sid is required")
        if sequence_number < 0:
            raise ExotelMediaError("sequence_number cannot be negative")
        if not name:
            raise ExotelMediaError("mark name is required")
        return json.dumps(
            {
                "event": "mark",
                "sequence_number": sequence_number,
                "stream_sid": stream_sid,
                "mark": {"name": name},
            },
            separators=(",", ":"),
        )

    @staticmethod
    def encode_clear(stream_sid: str) -> str:
        if not stream_sid:
            raise ExotelMediaError("stream_sid is required")
        return json.dumps(
            {"event": "clear", "stream_sid": stream_sid},
            separators=(",", ":"),
        )

    def _validate_payload(self, payload: bytes) -> None:
        size = len(payload)
        if size < self.config.min_chunk_bytes:
            raise ExotelMediaError(
                f"audio chunk is below minimum size: {size} bytes"
            )
        if size > self.config.max_chunk_bytes:
            raise ExotelMediaError(
                f"audio chunk exceeds maximum size: {size} bytes"
            )
        if size % self.config.required_chunk_multiple != 0:
            raise ExotelMediaError(
                "audio chunk size must be a multiple of "
                f"{self.config.required_chunk_multiple} bytes"
            )
