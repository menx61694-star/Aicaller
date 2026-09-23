import base64
import json

from aicaller.ai.openai_realtime import OpenAIRealtimeAdapter
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.utterance import AudioUtterance


def utterance() -> AudioUtterance:
    fmt = AudioFormat(AudioEncoding.PCM16_LE, 8000)
    frame = NormalizedAudioFrame("stream-1", 1, 20, b"\x00\x01", fmt)
    return AudioUtterance("stream-1", (frame,), 20, 40)


def test_append_audio_encodes_utterance() -> None:
    message = json.loads(OpenAIRealtimeAdapter().append_audio(utterance()))
    assert message["type"] == "input_audio_buffer.append"
    assert base64.b64decode(message["audio"]) == b"\x00\x01"


def test_commit_audio() -> None:
    message = json.loads(OpenAIRealtimeAdapter().commit_audio())
    assert message["type"] == "input_audio_buffer.commit"


def test_parse_partial_and_final_events() -> None:
    adapter = OpenAIRealtimeAdapter()
    partial = adapter.parse_transcript_event(
        json.dumps({
            "type": "conversation.item.input_audio_transcription.delta",
            "delta": "hello",
        }),
        stream_sid="stream-1",
        sequence=1,
    )
    final = adapter.parse_transcript_event(
        json.dumps({
            "type": "conversation.item.input_audio_transcription.completed",
            "transcript": "hello world",
            "language": "en",
        }),
        stream_sid="stream-1",
        sequence=2,
    )
    assert partial is not None and not partial.is_final
    assert final is not None and final.is_final
    assert final.language == "en"
