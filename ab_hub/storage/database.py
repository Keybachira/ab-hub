"""Database engine and session management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ab_hub.core.config import Settings, get_settings
from ab_hub.core.logger import get_logger
from ab_hub.storage.models import Base

logger = get_logger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine
    if _engine is None:
        settings = settings or get_settings()
        settings.ensure_data_dir()
        url = f"sqlite:///{settings.db_path}"
        _engine = create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

        # Enable foreign keys for SQLite
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine(settings)
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionLocal


def init_db(settings: Settings | None = None) -> None:
    """Create all tables."""
    engine = get_engine(settings)
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized at %s", (settings or get_settings()).db_path)


@contextmanager
def get_session(settings: Settings | None = None) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    factory = get_session_factory(settings)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
