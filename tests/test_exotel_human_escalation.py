import pytest

from aicaller.adapters.telephony.exotel import (
    ExotelAdapter,
    ExotelHumanRingNotConfigured,
)


def test_exotel_human_ring_fails_closed_without_account_flow_configuration() -> None:
    with pytest.raises(ExotelHumanRingNotConfigured, match="account-specific"):
        ExotelAdapter().start_human_ring("provider-call-1", "+911234567890")


def test_exotel_takeover_fails_closed_without_account_bridge_configuration() -> None:
    with pytest.raises(ExotelHumanRingNotConfigured, match="bridge configuration"):
        ExotelAdapter().request_human_takeover("provider-call-1", "+911234567890")
