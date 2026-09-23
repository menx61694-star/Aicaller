from __future__ import annotations

import base64
import json
from dataclasses import dataclass

from aicaller.ai.transcript import TranscriptUpdate
from aicaller.audio.utterance import AudioUtterance


class RealtimeProtocolError(ValueError):
    """Raised when a realtime server event is malformed."""


@dataclass(frozen=True)
class RealtimeConfig:
    model: str = "gpt-realtime-2.1"


class OpenAIRealtimeAdapter:
    """Provider boundary for OpenAI realtime transcription events.

    Network/session ownership stays outside this adapter. This class only
    converts normalized utterances and provider events into deterministic
    protocol messages/domain updates.
    """

    def __init__(self, config: RealtimeConfig | None = None) -> None:
        self.config = config or RealtimeConfig()

    def append_audio(self, utterance: AudioUtterance) -> str:
        return json.dumps(
            {
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(utterance.payload).decode("ascii"),
            },
            separators=(",", ":"),
        )

    def commit_audio(self) -> str:
        return json.dumps(
            {"type": "input_audio_buffer.commit"},
            separators=(",", ":"),
        )

    def parse_transcript_event(
        self,
        payload: bytes | str,
        *,
        stream_sid: str,
        sequence: int,
    ) -> TranscriptUpdate | None:
        try:
            data = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            raise RealtimeProtocolError("invalid realtime JSON") from exc

        event_type = data.get("type")
        if event_type not in {
            "conversation.item.input_audio_transcription.delta",
            "conversation.item.input_audio_transcription.completed",
        }:
            return None

        text = data.get("delta") if event_type.endswith(".delta") else data.get("transcript")
        if not isinstance(text, str) or not text.strip():
            return None

        language = data.get("language")
        if language is not None and not isinstance(language, str):
            raise RealtimeProtocolError("realtime language must be a string")

        return TranscriptUpdate(
            stream_sid=stream_sid,
            text=text,
            is_final=event_type.endswith(".completed"),
            sequence=sequence,
            language=language,
        )
