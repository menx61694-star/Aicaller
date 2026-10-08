from aicaller.ai.barge_in import BargeInDetector
from aicaller.ai.repeated_barge_in import RepeatedBargeInController
from aicaller.audio.barge_in_latency import BargeInLatencyRecorder
from aicaller.audio.output import AudioOutputFrame, OutboundAudioPipeline
from aicaller.audio.tts_cancel import TTSCancellationController


def test_phase4_barge_in_chain_cancels_flushes_and_measures() -> None:
    detector = BargeInDetector()
    assert not detector.observe(is_speech=True, confidence=0.9)
    assert detector.observe(is_speech=True, confidence=0.9)

    interruption = RepeatedBargeInController().begin(sequence=12)

    cancellation = TTSCancellationController().cancel(
        reason="caller_speech",
        sequence=interruption.sequence,
    )

    output = OutboundAudioPipeline()
    output.enqueue(AudioOutputFrame("s1", 10, b"tts"))
    flushed = output.flush()

    latency = BargeInLatencyRecorder().record(
        detected_at_ms=1000,
        cancellation_at_ms=1050,
        flush_at_ms=1100,
    )

    assert cancellation.reason == "caller_speech"
    assert [frame.payload for frame in flushed] == [b"tts"]
    assert latency.detection_to_flush_ms == 100
