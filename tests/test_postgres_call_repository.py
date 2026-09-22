from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicaller.db.base import Base
from aicaller.domain.call import CallSession, CallState
from aicaller.services.postgres_call_repository import PostgresCallRepository


def test_repository_round_trip_with_relational_database() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    repository = PostgresCallRepository(factory)

    now = datetime.now(UTC)
    session = CallSession(
        call_id="call-123",
        caller_number="+919999999999",
        state=CallState.RINGING,
        created_at=now,
        updated_at=now,
        provider_call_id="provider-123",
        last_provider_event="ringing",
    )

    repository.save(session)
    loaded = repository.get("call-123")

    assert loaded == session
    assert repository.get("missing") is None
