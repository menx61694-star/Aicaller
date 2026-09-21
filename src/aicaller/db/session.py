from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from aicaller.config import settings


def build_engine(database_url: str | None = None):
    url = database_url or settings.database_url
    if not url:
        raise ValueError("DATABASE_URL is required for PostgreSQL persistence")
    return create_engine(url, pool_pre_ping=True)


def build_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(
        bind=build_engine(database_url),
        class_=Session,
        expire_on_commit=False,
    )
