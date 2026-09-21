from __future__ import annotations

from dataclasses import dataclass

from aicaller.audio.frame import AudioFrame


@dataclass(frozen=True)
class PacketLossPolicy:
    """Bounded gap handling policy.

    A gap is skipped only after enough newer frames are buffered. This keeps
    normal jitter from being mistaken for packet loss while preventing an
    indefinitely blocked audio stream.
    """

    max_gap_frames: int = 3

    def __post_init__(self) -> None:
        if self.max_gap_frames < 1:
            raise ValueError("max_gap_frames must be positive")


class PacketLossHandler:
    def __init__(self, policy: PacketLossPolicy | None = None) -> None:
        self.policy = policy or PacketLossPolicy()

    def should_skip_gap(
        self,
        *,
        next_sequence: int | None,
        buffered_sequences: list[int],
    ) -> bool:
        if next_sequence is None or not buffered_sequences:
            return False
        # Require the configured number of newer frames before declaring
        # the gap lost. One newer frame can still be ordinary jitter.
        newer_frames = sum(sequence > next_sequence for sequence in buffered_sequences)
        return newer_frames >= self.policy.max_gap_frames

    def skip_gap(self, next_sequence: int | None) -> int | None:
        if next_sequence is None:
            return None
        return next_sequence + 1


def silence_frame(
    *,
    stream_sid: str,
    sequence_number: int,
    timestamp_ms: int | None,
    byte_length: int,
) -> AudioFrame:
    """Create an explicit silence frame for a lost packet.

    The caller supplies the expected codec-frame byte length. This function
    does not assume a codec or sample format.
    """
    if byte_length <= 0:
        raise ValueError("byte_length must be positive")
    return AudioFrame(
        stream_sid=stream_sid,
        sequence_number=sequence_number,
        timestamp_ms=timestamp_ms,
        payload=b"\x00" * byte_length,
    )
