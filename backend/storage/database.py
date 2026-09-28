"""
backend/storage/database.py
Owner: Arzaan
Purpose: SQLAlchemy engine, session factory, declarative Base, and init_db().
         All other storage modules import Base and get_db() from here.

Rules (guide_arzaan.md §6 step 4):
  - check_same_thread=False required for SQLite + FastAPI async background tasks.
  - Use get_db() as FastAPI dependency injection — never create sessions manually.
  - init_db() called once from main.py startup_event.
"""

from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from typing import Generator

from backend.core.config import config
from backend.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

DATABASE_URL: str = config.database.url

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + threading
    echo=config.app.debug,                       # SQL echo only in debug mode
)

# Enable WAL mode for better concurrent read performance with SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):  # noqa: ANN001
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# Declarative Base — imported by models.py
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy session.
    Usage in route handlers:
        def my_route(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Create all tables defined in ORM models.
    Called once from backend/main.py startup_event.
    Safe to call multiple times — CREATE TABLE IF NOT EXISTS semantics.
    """
    # Import models here to ensure they are registered with Base before create_all
    import backend.storage.models  # noqa: F401  — registers ORM models

    Base.metadata.create_all(bind=engine)

    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]

    logger.info("Database initialised | url=%s | tables=%s", DATABASE_URL, tables)
