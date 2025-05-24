# AliceMultiverse Database System

## Overview

The database system implements a content-addressed asset storage model where files are tracked by their content hash rather than file path. This allows assets to be moved freely while maintaining all metadata and relationships.

## Key Concepts

### Content-Addressed Storage
- Assets are identified by SHA-256 hash of their content (excluding metadata)
- File paths are cached but not required - assets can be rediscovered if moved
- Content hash remains stable even if metadata is updated
- Supports WebP and HEIC/HEIF formats with metadata embedding

### Database Schema

**Projects**
- Container for related assets with creative context
- Stores style preferences, settings, and metadata

**Assets**  
- Primary entity tracked by content_hash
- Stores file properties, generation parameters, analysis results
- Links to current file_path (can be null if file moved)

**AssetPaths**
- Historical record of where assets have been found
- Enables asset rediscovery when files are moved

**AssetRelationships**
- Track relationships between assets (variations, derivatives, etc.)
- Supports workflow tracking and asset lineage

**Tags**
- Semantic tagging system for assets
- Supports user, AI, and auto-generated tags

## Setup

### Initialize Database
```bash
# Using Alembic migrations (recommended)
alembic upgrade head

# Or direct initialization
python scripts/init_db.py
```

### Configuration

Environment variables:
- `ALICEMULTIVERSE_DATABASE_URL` - Database connection string (defaults to SQLite)
- `ALICEMULTIVERSE_SQL_ECHO` - Enable SQL query logging

Default SQLite location: `~/.alicemultiverse/alicemultiverse.db`

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## Usage Example

```python
from alicemultiverse.database import get_session
from alicemultiverse.database.repository import AssetRepository
from alicemultiverse.assets.hashing import calculate_content_hash

# Calculate content hash for a file
content_hash = calculate_content_hash(Path("image.png"))

# Store asset in database
with get_session() as session:
    repo = AssetRepository(session)
    asset = repo.create_or_update_asset(
        content_hash=content_hash,
        file_path="image.png",
        media_type="image",
        source_type="fal.ai"
    )
    session.commit()
```

## Migration Path

The system is designed to support future PostgreSQL migration:
1. Update `ALICEMULTIVERSE_DATABASE_URL` environment variable
2. Run migrations on new database
3. Use same repository pattern - no code changes needed

## Integration with Unified Cache

The database integrates seamlessly with the UnifiedCache system:
- Content hashes are shared between cache and database
- Metadata is stored in both systems for redundancy
- Database enables advanced queries across all assets
- Cache provides fast local access for active operations

## Advanced Features

### Asset Discovery
```python
from alicemultiverse.assets.discovery import AssetDiscovery

discovery = AssetDiscovery(session)
# Find all assets in a directory tree
assets = discovery.discover_assets(Path("/path/to/media"))
```

### Relationship Tracking
- Track parent/child relationships (e.g., variations)
- Monitor workflow progression
- Build asset lineage trees

### Semantic Search
- Tag-based queries
- Metadata-based filtering
- AI-generated content detection