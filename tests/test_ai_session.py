import json

from aicaller.ai.session import RealtimeAISession
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.utterance import AudioUtterance


def utterance() -> AudioUtterance:
    fmt = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    frame = NormalizedAudioFrame("stream-1", 1, 20, b"\x00\x01", fmt)
    return AudioUtterance("stream-1", (frame,), 20, 40)


def test_session_builds_audio_messages() -> None:
    session = RealtimeAISession("stream-1")
    append, commit = session.build_audio_messages(utterance())
    assert json.loads(append)["type"] == "input_audio_buffer.append"
    assert json.loads(commit)["type"] == "input_audio_buffer.commit"


def test_session_updates_transcript_state() -> None:
    session = RealtimeAISession("stream-1")
    result = session.consume_event(json.dumps({
        "type": "conversation.item.input_audio_transcription.completed",
        "transcript": "hello",
        "language": "hi",
    }))
    assert result is not None
    assert result.is_final
    assert result.language == "hi"
    assert session.transcript.final_text == "hello"
