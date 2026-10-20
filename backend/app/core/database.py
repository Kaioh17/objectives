from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# The app uses DATABASE_URL (Neon's pooled string). Alembic uses DATABASE_URL_UNPOOLED.
# Engine choice needs no code change.
url = settings.database_url

if url.startswith("sqlite"):
    # SQLite needs this flag because FastAPI runs sync deps in a threadpool
    connect_args: dict = {"check_same_thread": False}
else:
    # PgBouncer in transaction mode must not see server-side prepared statements
    connect_args = {"prepare_threshold": None}

# Neon suspends idle computes, so recycle connections and ping before reuse
engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    """SQLite ignores foreign keys unless asked, so ON DELETE CASCADE would silently not run."""

    @event.listens_for(engine, "connect")
    def _pragma(dbapi_connection, _record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")


if url.startswith("sqlite"):
    enable_sqlite_foreign_keys(engine)


def get_db() -> Iterator[Session]:
    """Request-scoped session dependency."""
    with SessionLocal() as db:
        yield db


DBDep = Annotated[Session, Depends(get_db)]
