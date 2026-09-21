from aicaller.audio.frame import AudioFrame
from aicaller.audio.pipeline import AudioPipelineConfig, InboundAudioPipeline


def frame(sequence: int, payload: bytes = b"x") -> AudioFrame:
    return AudioFrame("stream-1", sequence, sequence, payload)


def test_pipeline_releases_ordered_frames_after_jitter() -> None:
    pipeline = InboundAudioPipeline()

    assert pipeline.ingest(frame(1)) == [frame(1)]
    assert pipeline.ingest(frame(3)) == []
    assert pipeline.ingest(frame(2)) == [frame(2), frame(3)]


def test_pipeline_emits_explicit_silence_after_bounded_gap() -> None:
    pipeline = InboundAudioPipeline(
        AudioPipelineConfig(max_gap_frames=2, silence_frame_bytes=4)
    )

    assert pipeline.ingest(frame(1)) == [frame(1)]
    assert pipeline.ingest(frame(4)) == []

    lost = pipeline.ingest(frame(5))
    assert len(lost) == 1
    assert lost[0].sequence_number == 2
    assert lost[0].payload == b"\x00\x00\x00\x00"

    recovered = pipeline.ingest(frame(3))
    assert [item.sequence_number for item in recovered] == [3, 4, 5]
    assert pipeline.jitter.next_sequence == 6


def test_pipeline_does_not_mutate_input_frame() -> None:
    pipeline = InboundAudioPipeline()
    item = frame(1, b"abc")

    output = pipeline.ingest(item)

    assert output[0] == item
