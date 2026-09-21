from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from aicaller.db.base import Base


class CallSessionModel(Base):
    __tablename__ = "call_sessions"

    call_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    caller_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    provider_call_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    last_provider_event: Mapped[str | None] = mapped_column(String(128), nullable=True)
