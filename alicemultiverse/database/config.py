"""Database configuration and session management."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Database URL with fallback to SQLite
DATABASE_URL = os.environ.get(
    "ALICEMULTIVERSE_DATABASE_URL", f"sqlite:///{Path.home()}/.alicemultiverse/alicemultiverse.db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=bool(os.environ.get("ALICEMULTIVERSE_SQL_ECHO", False)),
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_engine():
    """Get the database engine."""
    return engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Initialize the database by creating all tables."""
    from .models import Base

    # Create directory for SQLite if needed
    if DATABASE_URL.startswith("sqlite"):
        db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
