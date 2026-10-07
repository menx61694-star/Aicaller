from aicaller.ai.barge_in_context import BargeInContextStore
from aicaller.audio.format import AudioFormat, NormalizedAudioFrame
from aicaller.audio.utterance import AudioUtterance


def utterance() -> AudioUtterance:
    frame = NormalizedAudioFrame(
        stream_sid="stream-1",
        sequence_number=7,
        timestamp_ms=700,
        payload=b"\x01\x00",
        audio_format=AudioFormat.PCM16_LE,
    )
    return AudioUtterance("stream-1", (frame,), 700, 700)


def test_context_store_preserves_interrupted_utterance() -> None:
    store = BargeInContextStore()

    context = store.capture(
        utterance(),
        interrupted_tts_generation=3,
        sequence=9,
    )

    assert store.peek() == context
    assert context.utterance.payload == b"\x01\x00"
    assert context.interrupted_tts_generation == 3


def test_context_store_consume_is_single_use() -> None:
    store = BargeInContextStore()
    store.capture(utterance(), interrupted_tts_generation=1, sequence=2)

    first = store.consume()

    assert first is not None
    assert store.consume() is None


def test_context_store_capture_replaces_stale_interruption_context() -> None:
    store = BargeInContextStore()
    store.capture(utterance(), interrupted_tts_generation=1, sequence=2)

    replacement = store.capture(
        utterance(),
        interrupted_tts_generation=2,
        sequence=3,
    )

    assert store.peek() == replacement
    assert replacement.interrupted_tts_generation == 2
