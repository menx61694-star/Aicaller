import pytest

from aicaller.domain.call import CallState
from aicaller.services.call_repository import InMemoryCallRepository
from aicaller.services.call_routing import CallRoutingService, RouteTarget, RoutingPolicy
from aicaller.services.call_service import CallService


def service() -> CallRoutingService:
    calls = CallService(InMemoryCallRepository())
    return CallRoutingService(calls, RoutingPolicy(human_ring_seconds=5, ai_answer_timeout_seconds=3))


def test_human_route_and_ai_timeout() -> None:
    routing = service()
    call = routing.call_service.create_incoming("call-1", "+911")
    routing.call_service.transition(call.call_id, CallState.RINGING)

    human = routing.route(call.call_id, RouteTarget.HUMAN)
    assert human.state is CallState.HUMAN_CALL

    ended = routing.call_service.transition(call.call_id, CallState.CALL_ENDED)
    assert ended.state is CallState.CALL_ENDED


def test_human_ring_timeout_starts_ai() -> None:
    routing = service()
    call = routing.call_service.create_incoming("call-2", "+912")
    routing.call_service.transition(call.call_id, CallState.RINGING)

    result = routing.on_human_ring_timeout(call.call_id)
    assert result.state is CallState.AI_ANSWERING


def test_ai_timeout_fails_call() -> None:
    routing = service()
    call = routing.call_service.create_incoming("call-3", "+913")
    routing.call_service.transition(call.call_id, CallState.RINGING)
    routing.start_ai_answering(call.call_id)

    result = routing.on_ai_answer_timeout(call.call_id)
    assert result.state is CallState.FAILURE
    assert result.failure_reason == "AI_ANSWER_TIMEOUT"


def test_invalid_policy_rejected() -> None:
    with pytest.raises(ValueError):
        RoutingPolicy(ai_answer_timeout_seconds=0)
