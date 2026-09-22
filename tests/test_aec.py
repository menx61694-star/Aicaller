import pytest

from aicaller.audio.aec import AECConfig, AECError, NLMSAcousticEchoCanceller
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame


def frame(payload: bytes, sequence: int = 1) -> NormalizedAudioFrame:
    return NormalizedAudioFrame(
        stream_sid="stream-1",
        sequence_number=sequence,
        timestamp_ms=0,
        payload=payload,
        format=AudioFormat(AudioEncoding.PCM16_LE, 8000),
    )


def pcm16(*samples: int) -> bytes:
    output = bytearray()
    for sample in samples:
        output.extend(int(sample).to_bytes(2, "little", signed=True))
    return bytes(output)


def test_aec_reduces_a_known_echo_signal() -> None:
    aec = NLMSAcousticEchoCanceller(AECConfig(filter_length=8, step_size=0.5))
    reference = [1000, 2000, -1000, 500] * 20
    # The near-end signal is reference delayed by one sample.
    near = [0] + reference[:-1]
    result = aec.process(
        near_end=frame(pcm16(*near)),
        far_end_reference=frame(pcm16(*reference)),
    )
    before = sum(abs(x) for x in near)
    after = sum(abs(int.from_bytes(result.payload[i:i + 2], "little", signed=True))
                for i in range(0, len(result.payload), 2))
    assert after < before


def test_aec_rejects_mismatched_stream() -> None:
    aec = NLMSAcousticEchoCanceller()
    near = frame(pcm16(1, 2))
    other = NormalizedAudioFrame(
        stream_sid="other",
        sequence_number=1,
        timestamp_ms=0,
        payload=pcm16(1, 2),
        format=near.format,
    )
    with pytest.raises(AECError, match="stream"):
        aec.process(near_end=near, far_end_reference=other)


def test_aec_rejects_mismatched_frame_lengths() -> None:
    aec = NLMSAcousticEchoCanceller()
    with pytest.raises(AECError, match="lengths"):
        aec.process(
            near_end=frame(pcm16(1, 2)),
            far_end_reference=frame(pcm16(1)),
        )

def test_aec_rejects_non_pcm16_format() -> None:
    aec = NLMSAcousticEchoCanceller()
    near = NormalizedAudioFrame(
        stream_sid="stream-1",
        sequence_number=1,
        timestamp_ms=0,
        payload=b"\x00\x00",
        format=AudioFormat(AudioEncoding.MULAW, 8000, sample_width_bytes=1),
    )
    with pytest.raises(AECError, match="PCM16_LE"):
        aec.process(near_end=near, far_end_reference=near)

