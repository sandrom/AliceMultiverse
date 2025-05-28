# AliceMultiverse Database System

## Overview

AliceMultiverse uses PostgreSQL exclusively for all database operations. The system implements a content-addressed asset storage model where files are tracked by their content hash rather than file path. This allows assets to be moved freely while maintaining all metadata and relationships.

## PostgreSQL Setup

### Local Development

Use docker-compose to run PostgreSQL locally:

```bash
# Start PostgreSQL and other services
docker-compose up -d postgres

# Database will be available at:
# postgresql://alice:alice@localhost:5432/alicemultiverse
```

### Kubernetes Production

In Kubernetes, PostgreSQL is managed by CloudNativePG operator:

```bash
# Database connection is provided via environment variable:
# DATABASE_URL=postgresql://alice:password@postgres-rw:5432/alicemultiverse
```

## Key Concepts

### Content-Addressed Storage
- Assets are identified by SHA-256 hash of their content (excluding metadata)
- File paths are cached but not required - assets can be rediscovered if moved
- Content hash remains stable even if metadata is updated
- Supports WebP and HEIC/HEIF formats with metadata embedding

### Database Schema

**Projects**
- Container for related assets with creative context
- Budget tracking with automatic enforcement
- Stores style preferences, settings, and metadata

**Assets**  
- Primary entity tracked by content_hash
- Stores file properties, generation parameters, analysis results
- Links to current file_path (can be null if file moved)

**Generations**
- Tracks AI generation requests and costs
- Links to projects for budget management
- Records provider, model, prompt, and results

**AssetPaths**
- Historical record of where assets have been found
- Enables asset rediscovery when files are moved

**AssetRelationships**
- Track relationships between assets (variations, derivatives, etc.)
- Supports workflow tracking and asset lineage

**Tags**
- Semantic tagging system with key:value pairs
- Example: {"style": ["cyberpunk"], "mood": ["dark"]}
- Supports user, AI, and auto-generated tags

## Database Migrations

All schema changes are managed through Alembic:

```bash
# Run all migrations
alembic upgrade head

# Create a new migration
alembic revision -m "Description of changes"

# Check current version
alembic current

# View migration history
alembic history
```

## Environment Variables

```bash
# Required - PostgreSQL connection string
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Optional - Enable SQL logging
ALICEMULTIVERSE_SQL_ECHO=true
```

## Connection Pool Settings

The database connection is configured with:
- `pool_size=10`: Number of persistent connections
- `max_overflow=20`: Additional connections when needed
- `pool_pre_ping=True`: Verify connections before use
- `pool_recycle=3600`: Recycle connections after 1 hour

## Python Usage

```python
from alicemultiverse.database.config import get_session, init_db
from alicemultiverse.database.repository import AssetRepository

# Initialize database connection
db_session = init_db()

# Use repository pattern
repo = AssetRepository(db_session)
assets = repo.search(tags={"style": ["cyberpunk"]})
```

## Troubleshooting

### Connection Issues

```bash
# Test PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1"

# Check if migrations are up to date
alembic current
```

### Performance

- Create indexes for frequently queried columns
- Use EXPLAIN ANALYZE for slow queries
- Monitor connection pool usage
- Consider partitioning for large tables

## Best Practices

1. **Always use migrations** - Never modify schema directly
2. **Use transactions** - Wrap related operations in transactions
3. **Handle connections properly** - Always close sessions
4. **Index foreign keys** - PostgreSQL doesn't do this automatically
5. **Use JSONB for flexible data** - Better than JSON for querying

## Backup and Recovery

For production deployments:

```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

In Kubernetes, use CloudNativePG's built-in backup features.