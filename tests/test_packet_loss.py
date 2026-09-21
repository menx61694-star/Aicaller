from aicaller.audio.frame import AudioFrame
from aicaller.audio.packet_loss import (
    PacketLossHandler,
    PacketLossPolicy,
    silence_frame,
)


def frame(sequence: int) -> AudioFrame:
    return AudioFrame("stream-1", sequence, sequence, b"x")


def test_packet_loss_policy_waits_before_skipping() -> None:
    handler = PacketLossHandler(PacketLossPolicy(max_gap_frames=3))

    assert not handler.should_skip_gap(
        next_sequence=2,
        buffered_sequences=[3, 4],
    )
    assert handler.should_skip_gap(
        next_sequence=2,
        buffered_sequences=[3, 4, 5],
    )


def test_packet_loss_skip_advances_only_one_missing_sequence() -> None:
    handler = PacketLossHandler()

    assert handler.skip_gap(7) == 8
    assert handler.skip_gap(None) is None


def test_silence_frame_is_explicit_and_codec_agnostic() -> None:
    item = silence_frame(
        stream_sid="stream-1",
        sequence_number=4,
        timestamp_ms=80,
        byte_length=4,
    )

    assert item == AudioFrame("stream-1", 4, 80, b"\x00\x00\x00\x00")
