import json


class ExotelHumanRingNotConfigured(RuntimeError):
    """Raised until the account-specific Exotel bridge/transfer is configured."""

from aicaller.adapters.telephony.base import TelephonyEvent, TelephonyEventType


class ExotelAdapter:
    """Provider boundary; authentication remains fail-closed until configured."""

    def verify_request(self, payload: bytes, headers: dict[str, str]) -> bool:
        return False

    def start_human_ring(self, provider_call_id: str, destination: str) -> None:
        raise ExotelHumanRingNotConfigured(
            "Exotel human-ring bridge requires account-specific flow configuration"
        )

    def stop_human_ring(self, provider_call_id: str) -> None:
        raise ExotelHumanRingNotConfigured(
            "Exotel human-ring bridge requires account-specific flow configuration"
        )

    def parse_event(self, payload: bytes, headers: dict[str, str]) -> TelephonyEvent:
        data = json.loads(payload.decode("utf-8"))
        name = str(data.get("event_type", data.get("event", "INCOMING_CALL"))).upper()
        call_id = str(data.get("call_id") or data.get("CallSid") or "")
        caller = data.get("caller_number") or data.get("From") or data.get("from")
        return TelephonyEvent(
            event_type=TelephonyEventType(name),
            provider_call_id=call_id,
            caller_number=str(caller) if caller else None,
            raw_status=str(data.get("status")) if data.get("status") is not None else None,
        )
