from dataclasses import dataclass
from enum import StrEnum

from aicaller.domain.call import CallSession, CallState
from aicaller.services.call_service import CallService


class RouteTarget(StrEnum):
    HUMAN = "HUMAN"
    AI = "AI"


@dataclass(frozen=True)
class RoutingPolicy:
    human_ring_seconds: float = 7.0
    ai_answer_timeout_seconds: float = 3.0
    prefer_human: bool = True

    def __post_init__(self) -> None:
        if self.human_ring_seconds < 0:
            raise ValueError("human_ring_seconds must be non-negative")
        if self.ai_answer_timeout_seconds <= 0:
            raise ValueError("ai_answer_timeout_seconds must be positive")


class CallRoutingService:
    """Deterministic routing decisions and timeout transitions."""

    def __init__(
        self,
        call_service: CallService,
        policy: RoutingPolicy | None = None,
    ) -> None:
        self.call_service = call_service
        self.policy = policy or RoutingPolicy()

    def start_human_ring(self, call_id: str) -> CallSession:
        return self.call_service.transition(call_id, CallState.HUMAN_CALL)

    def start_ai_answering(self, call_id: str) -> CallSession:
        return self.call_service.transition(call_id, CallState.AI_ANSWERING)

    def route(self, call_id: str, target: RouteTarget) -> CallSession:
        if target is RouteTarget.HUMAN:
            return self.start_human_ring(call_id)
        return self.start_ai_answering(call_id)

    def on_human_ring_timeout(self, call_id: str) -> CallSession:
        return self.start_ai_answering(call_id)

    def on_ai_answer_timeout(self, call_id: str) -> CallSession:
        return self.call_service.transition(
            call_id,
            CallState.FAILURE,
            failure_reason="AI_ANSWER_TIMEOUT",
        )
