# ADR-010: Remove PostgreSQL Integration

Date: 2025-06-01

## Status

Accepted

## Context

AliceMultiverse initially used PostgreSQL as its primary database for:
- Asset metadata storage
- Event persistence
- Search operations
- Project management

However, we've transitioned to:
- **DuckDB** for metadata search and OLAP operations (file-based, no server needed)
- **Redis Streams** for event persistence
- **File-based metadata** with embedding in image files

The PostgreSQL integration adds complexity without providing value since:
1. DuckDB handles search operations better for our OLAP use case
2. Redis Streams provide better event streaming capabilities
3. File-based metadata with embedding is more portable
4. Removing PostgreSQL eliminates server dependency for basic usage

## Decision

Remove all PostgreSQL integration code including:
- SQLAlchemy models and ORM code
- Alembic migrations
- PostgreSQL connection pooling
- Database configuration
- PostgreSQL event storage

Keep only:
- DuckDB for search/analytics
- Redis for events and caching
- File-based metadata storage

## Consequences

### Positive
- **Simpler deployment** - No PostgreSQL server required
- **Reduced dependencies** - Remove SQLAlchemy, Alembic, psycopg2/asyncpg
- **Lower resource usage** - No database server running
- **Easier testing** - No database setup needed
- **Better portability** - Works on any system with just files

### Negative
- **No ACID transactions** - But not needed for our use case
- **No multi-user support** - Acceptable for personal creative tool
- **Migration required** - Users with PostgreSQL data need to migrate (none exist yet)

### Neutral
- Performance remains the same or better with DuckDB for our OLAP workloads
- Event persistence continues with Redis Streams

## Implementation

1. Remove PostgreSQL dependencies from pyproject.toml and requirements.txt
2. Delete alembic/ directory and migrations
3. Remove database/ module PostgreSQL code
4. Update event system to use only Redis
5. Remove PostgreSQL configuration from settings
6. Update documentation to remove PostgreSQL references

## Notes

This aligns with our philosophy of simplicity and file-first architecture. Since we have no users yet, this is the ideal time to make this breaking change.