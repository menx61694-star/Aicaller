from __future__ import annotations

from dataclasses import dataclass

from aicaller.ai.openai_realtime import OpenAIRealtimeAdapter
from aicaller.ai.transcript import TranscriptState
from aicaller.audio.utterance import AudioUtterance


class AISessionError(RuntimeError):
    pass


@dataclass(frozen=True)
class AITranscriptEvent:
    stream_sid: str
    text: str
    is_final: bool
    sequence: int


class RealtimeAISession:
    """Connection-independent realtime AI session state.

    Transport ownership remains outside this class. This keeps telephony and
    OpenAI WebSocket lifecycles isolated while sharing deterministic state.
    """

    def __init__(
        self,
        stream_sid: str,
        adapter: OpenAIRealtimeAdapter | None = None,
    ) -> None:
        if not stream_sid:
            raise AISessionError("stream_sid is required")
        self.stream_sid = stream_sid
        self.adapter = adapter or OpenAIRealtimeAdapter()
        self.transcript = TranscriptState(stream_sid)
        self._sequence = 0

    def build_audio_messages(self, utterance: AudioUtterance) -> tuple[str, str]:
        if utterance.stream_sid != self.stream_sid:
            raise AISessionError("utterance stream mismatch")
        return (
            self.adapter.append_audio(utterance),
            self.adapter.commit_audio(),
        )

    def consume_event(self, payload: bytes | str) -> AITranscriptEvent | None:
        self._sequence += 1
        update = self.adapter.parse_transcript_event(
            payload,
            stream_sid=self.stream_sid,
            sequence=self._sequence,
        )
        if update is None:
            return None
        self.transcript.apply(update)
        return AITranscriptEvent(
            stream_sid=update.stream_sid,
            text=update.text,
            is_final=update.is_final,
            sequence=update.sequence,
        )
