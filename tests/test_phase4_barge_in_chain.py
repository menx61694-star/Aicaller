from aicaller.ai.barge_in import BargeInDetector
from aicaller.ai.barge_in_context import BargeInContextStore
from aicaller.ai.repeated_barge_in import RepeatedBargeInController
from aicaller.audio.barge_in_capture import BargeInSpeechCapture
from aicaller.audio.barge_in_latency import BargeInLatencyRecorder
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.output import AudioOutputFrame, OutboundAudioPipeline
from aicaller.audio.tts_cancel import TTSCancellationController


def caller_frame(sequence: int, timestamp_ms: int) -> NormalizedAudioFrame:
    return NormalizedAudioFrame(
        stream_sid="s1",
        sequence_number=sequence,
        timestamp_ms=timestamp_ms,
        payload=b"\x01\x00",
        format=AudioFormat(AudioEncoding.PCM16_LE, 8000),
    )


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

    capture = BargeInSpeechCapture()
    capture.start(caller_frame(1, 1200))
    captured = capture.finish(caller_frame(2, 1220))
    context_store = BargeInContextStore()
    context = context_store.capture(
        captured,
        interrupted_tts_generation=interruption.generation,
        sequence=interruption.sequence,
    )

    latency = BargeInLatencyRecorder().record(
        detected_at_ms=1000,
        cancellation_at_ms=1050,
        flush_at_ms=1100,
    )

    assert cancellation.reason == "caller_speech"
    assert [frame.payload for frame in flushed] == [b"tts"]
    assert context_store.consume() == context
    assert context.utterance.payload == b"\x01\x00" * 2
    assert latency.detection_to_flush_ms == 100
