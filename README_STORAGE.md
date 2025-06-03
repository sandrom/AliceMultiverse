# AliceMultiverse Storage System

## Overview

AliceMultiverse uses a file-first approach where all data lives alongside your media files. The system implements content-addressed storage using SHA-256 hashes, allowing files to be moved freely while maintaining metadata. Search is powered by DuckDB, an embedded database that requires no server.

## Architecture

### File-Based Metadata Storage

All metadata is stored in `.metadata/` directories within your media folders:

```
inbox/
├── .metadata/
│   ├── ab/                    # First 2 chars of hash
│   │   └── abcdef...123.json  # Full metadata
│   └── cd/
│       └── cdef...456.json
├── image1.png
└── image2.jpg
```

**Metadata Format (v4.0)**:
```json
{
  "version": "4.0",
  "content_hash": "abcdef...",
  "file_name": "image1.png",
  "file_size": 1234567,
  "analysis": {
    "media_type": "image",
    "understanding": {
      "tags": {
        "style": ["cyberpunk", "neon"],
        "mood": ["energetic", "futuristic"],
        "subject": ["portrait", "woman"]
      },
      "description": "...",
      "cost": 0.0025
    }
  }
}
```

### Embedded Metadata

Metadata is also embedded directly in files for portability:
- **JPEG/PNG**: EXIF and XMP tags
- **WebP**: XMP metadata
- **HEIC/HEIF**: EXIF metadata
- **MP4**: Metadata atoms

### DuckDB Search Index

Search functionality uses DuckDB (`data/search.duckdb`):

```sql
-- Main assets table
CREATE TABLE assets (
    content_hash VARCHAR PRIMARY KEY,
    file_path VARCHAR,
    media_type VARCHAR,
    tags VARCHAR[],
    prompt TEXT,
    ...
);

-- Perceptual hashes for similarity
CREATE TABLE perceptual_hashes (
    content_hash VARCHAR PRIMARY KEY,
    phash VARCHAR,  -- DCT-based hash
    dhash VARCHAR,  -- Difference hash
    ahash VARCHAR   -- Average hash
);
```

## Key Features

### Content Addressing
- Files identified by SHA-256 hash of content
- Metadata stored by hash, not path
- Files can be moved/renamed without losing data
- Deduplication happens automatically

### Project Management
Projects are self-contained directories:
```
my-project/
├── project.yaml          # Project metadata
├── .alice/               # Alice-specific data
│   ├── selections.json   # What you selected and why
│   └── sessions/         # Conversation history
├── created/              # New generations
├── selected/             # Curated from library
└── exports/              # Final deliverables
```

### Event System (Optional)
- File-based by default: `~/.alice/events/`
- Redis Streams when scaling to microservices
- Set `USE_REDIS_EVENTS=true` to enable Redis

## Usage

### Rebuild Search Index
```bash
# Scan configured paths and rebuild index
alice index rebuild

# Update with new files only
alice index update

# Verify index integrity
alice index verify
```

### Direct Search (via Python)
```python
from alicemultiverse.storage.duckdb_search import DuckDBSearch

# Initialize search
search = DuckDBSearch("data/search.duckdb")

# Search by tags
results, total = search.search({
    "tags": ["cyberpunk", "portrait"],
    "media_type": "image"
})

# Find similar images
similar = search.find_similar(
    content_hash="abc123...",
    threshold=10  # Hamming distance
)
```

### Search via AI Assistant
```
You: Find all my cyberpunk portraits
Claude: [Uses search_images tool to query DuckDB]
```

## Configuration

In `settings.yaml`:
```yaml
storage:
  search_db: data/search.duckdb
  project_paths:
    - ~/Projects/AI
  asset_paths:
    - ~/Pictures/AI-Generated
    - ~/Downloads/AI-Images
```

## Backup Strategy

Since everything is file-based:

1. **Media + Metadata**: Back up your media directories (includes `.metadata/`)
2. **Search Index**: Can be rebuilt anytime from files
3. **Projects**: Self-contained directories, easy to archive

```bash
# Backup example
rsync -av --include="*/" --include="*.png" --include="*.jpg" \
          --include=".metadata/**" ~/Pictures/AI/ /backup/
```

## Migration from Database

If migrating from a database-backed system:

1. Export metadata to `.metadata/` folders
2. Ensure tags are embedded in files
3. Rebuild search index
4. Remove database dependencies

## Advantages

1. **No Database Server**: DuckDB is embedded, no setup needed
2. **Portable**: Metadata travels with files
3. **Simple Backups**: Just copy directories
4. **Offline Capable**: Everything works locally
5. **Fast Search**: DuckDB optimized for analytics

## Troubleshooting

### Search Not Finding Files
```bash
# Rebuild index
alice index rebuild --verify

# Check for .metadata folders
find ~/Pictures -name ".metadata" -type d
```

### Metadata Not Loading
```bash
# Verify cache version
cat inbox/.metadata/*/ab*.json | jq .version

# Should show "4.0" for current format
```

### Performance Tips
- Keep images organized in year/month folders
- Run `alice index update` after large imports
- Use `--dry-run` to preview operations

## File-First Philosophy

AliceMultiverse treats files as the source of truth:
- Databases are just indexes/caches
- Metadata lives with files
- No vendor lock-in
- Your data remains yours

This approach ensures your creative assets remain accessible regardless of what happens to AliceMultiverse or any external services.