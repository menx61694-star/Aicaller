from __future__ import annotations

import base64
import json
import secrets
from dataclasses import dataclass

from aicaller.adapters.telephony.base import TelephonyEvent, TelephonyEventType


@dataclass(frozen=True)
class ExotelStreamStart:
    stream_sid: str
    provider_call_id: str
    account_sid: str | None
    caller_number: str | None
    destination_number: str | None
    sample_rate: int | None


class ExotelStreamAdapter:
    """Parser/auth boundary for Exotel AgentStream Voicebot WSS events.

    Exotel documents Basic Authentication for the WSS endpoint and a JSON
    START event containing call SID, from/to and media format metadata.
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

    def parse_start(self, payload: bytes) -> ExotelStreamStart:
        data = json.loads(payload.decode("utf-8"))
        if str(data.get("event", "")).lower() != "start":
            raise ValueError("expected Exotel AgentStream start event")

        start = data.get("start") or {}
        media = start.get("media_format") or {}
        call_id = str(start.get("call_sid") or "")
        stream_sid = str(start.get("stream_sid") or data.get("stream_sid") or "")
        if not call_id:
            raise ValueError("missing Exotel call_sid")
        if not stream_sid:
            raise ValueError("missing Exotel stream_sid")

        sample_rate = media.get("sample_rate")
        return ExotelStreamStart(
            stream_sid=stream_sid,
            provider_call_id=call_id,
            account_sid=str(start["account_sid"]) if start.get("account_sid") else None,
            caller_number=str(start["from"]) if start.get("from") else None,
            destination_number=str(start["to"]) if start.get("to") else None,
            sample_rate=int(sample_rate) if sample_rate is not None else None,
        )

    def to_telephony_event(self, start: ExotelStreamStart) -> TelephonyEvent:
        return TelephonyEvent(
            event_type=TelephonyEventType.INCOMING_CALL,
            provider_call_id=start.provider_call_id,
            caller_number=start.caller_number,
            raw_status="start",
        )
