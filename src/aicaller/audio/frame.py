from __future__ import annotations

import base64
from dataclasses import dataclass


class AudioFrameError(ValueError):
    """Raised when an inbound telephony audio frame is invalid."""


@dataclass(frozen=True)
class AudioFrame:
    """Provider-neutral inbound audio frame.

    Payload remains immutable bytes at this boundary. Codec/sample-rate
    normalization belongs to the audio engine, not the telephony adapter.
    """

    stream_sid: str
    sequence_number: int | None
    timestamp_ms: int | None
    payload: bytes


def decode_base64_audio(
    *,
    stream_sid: str | None,
    sequence_number: str | None,
    timestamp: str | None,
    payload: str,
) -> AudioFrame:
    if not stream_sid:
        raise AudioFrameError("missing stream_sid")
    if not payload:
        raise AudioFrameError("missing audio payload")

    try:
        decoded = base64.b64decode(payload.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise AudioFrameError("invalid base64 audio payload") from exc

    if not decoded:
        raise AudioFrameError("empty audio payload")

    try:
        sequence = int(sequence_number) if sequence_number is not None else None
    except ValueError as exc:
        raise AudioFrameError("invalid audio sequence number") from exc

    try:
        timestamp_ms = int(timestamp) if timestamp is not None else None
    except ValueError as exc:
        raise AudioFrameError("invalid audio timestamp") from exc

    if sequence is not None and sequence < 0:
        raise AudioFrameError("audio sequence number cannot be negative")
    if timestamp_ms is not None and timestamp_ms < 0:
        raise AudioFrameError("audio timestamp cannot be negative")

    return AudioFrame(
        stream_sid=stream_sid,
        sequence_number=sequence,
        timestamp_ms=timestamp_ms,
        payload=decoded,
    )
