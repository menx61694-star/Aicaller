from __future__ import annotations

import base64
import json
import secrets
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aicaller.adapters.telephony.base import TelephonyEvent, TelephonyEventType


class ExotelStreamEventType(StrEnum):
    START = "start"
    MEDIA = "media"
    STOP = "stop"
    DTMF = "dtmf"
    MARK = "mark"


@dataclass(frozen=True)
class ExotelStreamStart:
    stream_sid: str
    provider_call_id: str
    account_sid: str | None
    caller_number: str | None
    destination_number: str | None
    sample_rate: int | None
    encoding: str | None


@dataclass(frozen=True)
class ExotelStreamMedia:
    stream_sid: str | None
    provider_call_id: str | None
    sequence_number: str | None
    chunk: str | None
    timestamp: str | None
    payload: str


@dataclass(frozen=True)
class ExotelStreamStop:
    stream_sid: str | None
    provider_call_id: str | None
    reason: str | None


@dataclass(frozen=True)
class ExotelStreamDtmf:
    stream_sid: str | None
    provider_call_id: str | None
    digit: str


@dataclass(frozen=True)
class ExotelStreamEvent:
    event_type: ExotelStreamEventType
    start: ExotelStreamStart | None = None
    media: ExotelStreamMedia | None = None
    stop: ExotelStreamStop | None = None
    dtmf: ExotelStreamDtmf | None = None


class ExotelStreamAdapter:
    """Parser/auth boundary for Exotel AgentStream Voicebot WSS events.

    This adapter validates the provider envelope and preserves media payloads
    for the realtime audio layer. It deliberately does not decode or process
    audio yet.
    """

    def __init__(self, api_key: str, api_token: str) -> None:
        self.api_key = api_key
        self.api_token = api_token

    def verify_request(self, headers: dict[str, str]) -> bool:
        if not self.api_key or not self.api_token:
            return False
        authorization = headers.get("authorization", "")
        if not authorization.startswith("Basic "):
            return False
        try:
            supplied = base64.b64decode(
                authorization[6:].encode("ascii"),
                validate=True,
            ).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return False
        expected = f"{self.api_key}:{self.api_token}"
        return secrets.compare_digest(supplied, expected)

    @staticmethod
    def _load(payload: bytes) -> dict[str, Any]:
        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid AgentStream JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("AgentStream event must be a JSON object")
        return data

    @staticmethod
    def _event_type(data: dict[str, Any]) -> ExotelStreamEventType:
        try:
            return ExotelStreamEventType(str(data.get("event", "")).lower())
        except ValueError as exc:
            raise ValueError("unsupported AgentStream event") from exc

    def parse_start(self, payload: bytes) -> ExotelStreamStart:
        data = self._load(payload)
        if self._event_type(data) is not ExotelStreamEventType.START:
            raise ValueError("expected Exotel AgentStream start event")

        start = data.get("start") or {}
        if not isinstance(start, dict):
            raise ValueError("invalid AgentStream start object")
        media = start.get("media_format") or {}
        if not isinstance(media, dict):
            raise ValueError("invalid AgentStream media_format object")

        call_id = str(start.get("call_sid") or "")
        stream_sid = str(start.get("stream_sid") or data.get("stream_sid") or "")
        if not call_id:
            raise ValueError("missing Exotel call_sid")
        if not stream_sid:
            raise ValueError("missing Exotel stream_sid")

        sample_rate = media.get("sample_rate")
        encoding = media.get("encoding")
        try:
            parsed_sample_rate = int(sample_rate) if sample_rate is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid Exotel sample_rate") from exc

        return ExotelStreamStart(
            stream_sid=stream_sid,
            provider_call_id=call_id,
            account_sid=str(start["account_sid"]) if start.get("account_sid") else None,
            caller_number=str(start["from"]) if start.get("from") else None,
            destination_number=str(start["to"]) if start.get("to") else None,
            sample_rate=parsed_sample_rate,
            encoding=str(encoding) if encoding is not None else None,
        )

    def parse_media(self, payload: bytes) -> ExotelStreamMedia:
        data = self._load(payload)
        if self._event_type(data) is not ExotelStreamEventType.MEDIA:
            raise ValueError("expected Exotel AgentStream media event")
        media = data.get("media") or {}
        if not isinstance(media, dict):
            raise ValueError("invalid AgentStream media object")
        audio_payload = media.get("payload")
        if not isinstance(audio_payload, str) or not audio_payload:
            raise ValueError("missing AgentStream media payload")
        return ExotelStreamMedia(
            stream_sid=str(data["stream_sid"]) if data.get("stream_sid") else None,
            provider_call_id=str(data["call_sid"]) if data.get("call_sid") else None,
            sequence_number=str(data["sequence_number"]) if data.get("sequence_number") is not None else None,
            chunk=str(media["chunk"]) if media.get("chunk") is not None else None,
            timestamp=str(media["timestamp"]) if media.get("timestamp") is not None else None,
            payload=audio_payload,
        )

    def parse_stop(self, payload: bytes) -> ExotelStreamStop:
        data = self._load(payload)
        if self._event_type(data) is not ExotelStreamEventType.STOP:
            raise ValueError("expected Exotel AgentStream stop event")
        stop = data.get("stop") or {}
        if not isinstance(stop, dict):
            raise ValueError("invalid AgentStream stop object")
        return ExotelStreamStop(
            stream_sid=str(data["stream_sid"]) if data.get("stream_sid") else None,
            provider_call_id=str(data["call_sid"]) if data.get("call_sid") else None,
            reason=str(stop["reason"]) if stop.get("reason") else None,
        )

    def parse_dtmf(self, payload: bytes) -> ExotelStreamDtmf:
        data = self._load(payload)
        if self._event_type(data) is not ExotelStreamEventType.DTMF:
            raise ValueError("expected Exotel AgentStream dtmf event")
        dtmf = data.get("dtmf") or {}
        if not isinstance(dtmf, dict):
            raise ValueError("invalid AgentStream dtmf object")
        digit = str(dtmf.get("digit") or "")
        if not digit:
            raise ValueError("missing AgentStream dtmf digit")
        return ExotelStreamDtmf(
            stream_sid=str(data["stream_sid"]) if data.get("stream_sid") else None,
            provider_call_id=str(data["call_sid"]) if data.get("call_sid") else None,
            digit=digit,
        )

    def parse_event(self, payload: bytes) -> ExotelStreamEvent:
        data = self._load(payload)
        event_type = self._event_type(data)
        if event_type is ExotelStreamEventType.START:
            return ExotelStreamEvent(event_type=event_type, start=self.parse_start(payload))
        if event_type is ExotelStreamEventType.MEDIA:
            return ExotelStreamEvent(event_type=event_type, media=self.parse_media(payload))
        if event_type is ExotelStreamEventType.STOP:
            return ExotelStreamEvent(event_type=event_type, stop=self.parse_stop(payload))
        if event_type is ExotelStreamEventType.DTMF:
            return ExotelStreamEvent(event_type=event_type, dtmf=self.parse_dtmf(payload))
        raise ValueError("unsupported AgentStream event for realtime pipeline")

    def to_telephony_event(self, start: ExotelStreamStart) -> TelephonyEvent:
        return TelephonyEvent(
            event_type=TelephonyEventType.INCOMING_CALL,
            provider_call_id=start.provider_call_id,
            caller_number=start.caller_number,
            raw_status="start",
        )
