from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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

    def select_initial_target(self) -> RouteTarget:
        return RouteTarget.HUMAN if self.policy.prefer_human else RouteTarget.AI

    def route(self, call_id: str, target: RouteTarget) -> CallSession:
        if target is RouteTarget.HUMAN:
            return self.start_human_ring(call_id)
        return self.start_ai_answering(call_id)

    def route_initial(self, call_id: str) -> CallSession:
        return self.route(call_id, self.select_initial_target())

    def evaluate_timeout(
        self,
        call_id: str,
        now: datetime | None = None,
    ) -> CallSession | None:
        session = self.call_service.get(call_id)
        if session is None:
            raise KeyError(call_id)
        now = now or datetime.now(UTC)
        if now < session.updated_at:
            raise ValueError("now cannot be earlier than session.updated_at")
        if session.state is CallState.HUMAN_CALL:
            deadline = session.updated_at + timedelta(seconds=self.policy.human_ring_seconds)
            if now >= deadline:
                return self.on_human_ring_timeout(call_id)
        elif session.state is CallState.AI_ANSWERING:
            deadline = session.updated_at + timedelta(seconds=self.policy.ai_answer_timeout_seconds)
            if now >= deadline:
                return self.on_ai_answer_timeout(call_id)
        return None

    def on_human_ring_timeout(self, call_id: str) -> CallSession:
        return self.start_ai_answering(call_id)

    def on_ai_answer_timeout(self, call_id: str) -> CallSession:
        return self.call_service.transition(
            call_id,
            CallState.FAILURE,
            failure_reason="AI_ANSWER_TIMEOUT",
        )
