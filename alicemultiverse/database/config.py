"""Database configuration and session management for PostgreSQL."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from alicemultiverse.core.monitoring import DatabasePoolMonitor, setup_pool_monitoring

# PostgreSQL connection - required in production
# In Kubernetes, this comes from ConfigMap/Secret
# For local development, use docker-compose PostgreSQL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    os.environ.get(
        "ALICEMULTIVERSE_DATABASE_URL",
        "postgresql://alice:alice@localhost:5432/alicemultiverse"
    )
)

if not DATABASE_URL.startswith("postgresql"):
    raise ValueError(
        "PostgreSQL is required. Set DATABASE_URL environment variable. "
        "Example: postgresql://user:password@host:5432/dbname"
    )

# Create engine with PostgreSQL-optimized settings
engine = create_engine(
    DATABASE_URL,
    echo=bool(os.environ.get("ALICEMULTIVERSE_SQL_ECHO", False)),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup pool monitoring (optional - can be disabled in production if needed)
_pool_monitor: Optional[DatabasePoolMonitor] = None
if os.environ.get("ENABLE_DB_MONITORING", "true").lower() == "true":
    _pool_monitor = setup_pool_monitoring(
        engine, 
        log_interval=int(os.environ.get("DB_MONITOR_INTERVAL", "60"))
    )


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


def init_db() -> Session:
    """Initialize database connection and return a session.
    
    Note: Table creation is handled by Alembic migrations.
    This function now just verifies connectivity and returns a session.
    """
    # Test connection
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    
    return SessionLocal()


def get_database_url() -> str:
    """Get the current database URL (with password masked)."""
    if "@" in DATABASE_URL:
        # Mask password in connection string
        parts = DATABASE_URL.split("@")
        creds = parts[0].split("://")[1]
        if ":" in creds:
            user = creds.split(":")[0]
            return f"postgresql://{user}:****@{parts[1]}"
    return DATABASE_URL


def get_pool_monitor() -> Optional[DatabasePoolMonitor]:
    """Get the database pool monitor if enabled."""
    return _pool_monitor


def get_pool_stats() -> dict:
    """Get current pool statistics."""
    if _pool_monitor:
        return _pool_monitor.get_stats()
    return {"error": "Pool monitoring not enabled"}