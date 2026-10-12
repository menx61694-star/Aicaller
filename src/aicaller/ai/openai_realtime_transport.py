from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from typing import Any
from urllib.parse import quote

from websockets.asyncio.client import connect


class OpenAIRealtimeTransportError(RuntimeError):
    pass


class OpenAIRealtimeTranscriptionTransport:
    """Authenticated OpenAI Realtime WebSocket configured for live transcription.

    Uses the current transcription-session schema and G.711 μ-law at 8 kHz,
    avoiding an implicit or lossy sample-rate conversion for telephony audio.
    """

    def __init__(self, socket: Any) -> None:
        self._socket = socket

    @classmethod
    async def connect(
        cls,
        api_key: str,
        *,
        realtime_model: str = "gpt-realtime-2.1",
        transcription_model: str = "gpt-live-transcribe",
        languages: Sequence[str] = ("en", "hi"),
        timeout_seconds: float = 10.0,
    ) -> OpenAIRealtimeTranscriptionTransport:
        if not api_key.strip():
            raise OpenAIRealtimeTransportError("OpenAI API key is required")
        if not realtime_model.strip() or not transcription_model.strip():
            raise OpenAIRealtimeTransportError("model names must not be empty")
        if timeout_seconds <= 0:
            raise OpenAIRealtimeTransportError("timeout must be positive")
        if not languages or any(not language.strip() for language in languages):
            raise OpenAIRealtimeTransportError("at least one language code is required")

        uri = (
            "wss://api.openai.com/v1/realtime?model="
            f"{quote(realtime_model, safe='')}"
        )
        try:
            socket = await connect(
                uri,
                additional_headers={"Authorization": f"Bearer {api_key}"},
                open_timeout=timeout_seconds,
                max_size=2**20,
            )
        except Exception as exc:
            raise OpenAIRealtimeTransportError("failed to connect to OpenAI Realtime") from exc

        transport = cls(socket)
        try:
            async with asyncio.timeout(timeout_seconds):
                await transport._wait_for_event("session.created")
                await transport.send(
                    json.dumps(
                        {
                            "type": "session.update",
                            "session": {
                                "type": "transcription",
                                "audio": {
                                    "input": {
                                        "format": {"type": "audio/pcmu"},
                                        "transcription": {
                                            "model": transcription_model,
                                            "languages": list(languages),
                                        },
                                        "turn_detection": None,
                                    }
                                },
                            },
                        },
                        separators=(",", ":"),
                    )
                )
                await transport._wait_for_event("session.updated")
        except Exception as exc:
            await transport.close()
            if isinstance(exc, OpenAIRealtimeTransportError):
                raise
            raise OpenAIRealtimeTransportError(
                "OpenAI Realtime transcription session initialization failed"
            ) from exc
        return transport

    async def _wait_for_event(self, expected_type: str) -> dict[str, Any]:
        while True:
            raw = await self.receive()
            try:
                event = json.loads(raw)
            except (TypeError, json.JSONDecodeError) as exc:
                raise OpenAIRealtimeTransportError("OpenAI sent invalid JSON") from exc
            if not isinstance(event, dict):
                raise OpenAIRealtimeTransportError("OpenAI event must be a JSON object")
            if event.get("type") == "error":
                error = event.get("error")
                message = error.get("message") if isinstance(error, dict) else None
                raise OpenAIRealtimeTransportError(
                    f"OpenAI Realtime error: {message or 'unspecified error'}"
                )
            if event.get("type") == expected_type:
                return event

    async def send(self, payload: str) -> None:
        await self._socket.send(payload)

    async def receive(self) -> str | bytes:
        return await self._socket.recv()

    async def close(self) -> None:
        await self._socket.close()
