from aicaller.audio.aec_reference import AECReferenceBuffer
from aicaller.audio.format import AudioEncoding, AudioFormat
from aicaller.audio.output import AudioOutputFrame


def test_reference_buffer_keeps_latest_frame() -> None:
    fmt = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    buffer = AECReferenceBuffer(max_frames=2)
    buffer.add(AudioOutputFrame("stream-1", 1, b"a", 0), fmt)
    buffer.add(AudioOutputFrame("stream-1", 2, b"b", 20), fmt)
    assert buffer.latest("stream-1").sequence_number == 2


def test_reference_buffer_is_bounded() -> None:
    fmt = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    buffer = AECReferenceBuffer(max_frames=2)
    for sequence in range(3):
        buffer.add(AudioOutputFrame("stream-1", sequence, b"x", sequence), fmt)
    assert buffer.pending_count == 2


def test_reference_buffer_clear() -> None:
    fmt = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    buffer = AECReferenceBuffer()
    buffer.add(AudioOutputFrame("stream-1", 1, b"x"), fmt)
    buffer.clear()
    assert buffer.pending_count == 0
