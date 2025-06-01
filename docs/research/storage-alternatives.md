# Storage Alternatives Research for AliceMultiverse

## Current State
- PostgreSQL used as primary database
- Metadata embedded in image files (EXIF/XMP)
- Cache stored in `.metadata` folders
- Database acts as a "search cache" - all data can be reconstructed from files

## Requirements
1. **Multi-location support**: Multiple drives, cloud storage (S3/GCS), network drives
2. **Content-addressed storage**: Find files by hash regardless of location
3. **Fast semantic search**: Search by tags, descriptions, generated prompts
4. **Scalability**: Handle millions of assets across distributed storage
5. **Resilience**: Rebuild from file metadata if needed
6. **Cloud-native**: Support object storage metadata (with 8KB limit on GCS)

## Storage Architecture Options

### 1. Hybrid Approach (Recommended)
**Components:**
- **Primary Storage**: Files with embedded metadata (source of truth)
- **Search Layer**: Lightweight, fast search index
- **Location Registry**: Track where files are stored
- **Cache Layer**: Fast access to frequently used data

**Advantages:**
- Files remain self-contained and portable
- Can rebuild entire system from files
- Flexible storage locations
- Fast search without full file scans

### 2. Search Layer Alternatives

#### Option A: Elasticsearch/OpenSearch
**Pros:**
- Excellent full-text search
- Native support for semantic/vector search
- Horizontal scaling
- Rich query DSL
- Aggregations for faceted search

**Cons:**
- Operational complexity
- Resource intensive
- Overkill for metadata-only search

#### Option B: Meilisearch
**Pros:**
- Fast, typo-tolerant search
- Easy to deploy and operate
- Low resource usage
- Good for faceted search
- Built-in UI for testing

**Cons:**
- Less mature than Elasticsearch
- Limited vector search capabilities
- Smaller ecosystem

#### Option C: SQLite with FTS5 (Full-Text Search)
**Pros:**
- Zero operational overhead
- Embedded database
- Full-text search built-in
- Can distribute database files
- Perfect for edge deployments

**Cons:**
- Single-writer limitation
- No built-in replication
- Limited to single machine

#### Option D: DuckDB
**Pros:**
- Columnar storage (fast analytics)
- Embedded like SQLite
- Better for analytical queries
- Parquet file support
- Can query S3 directly

**Cons:**
- Newer, less battle-tested
- Limited full-text search
- Not optimized for OLTP

#### Option E: Qdrant/Weaviate (Vector Databases)
**Pros:**
- Semantic search using embeddings
- Find similar images by content
- AI-native search capabilities
- Hybrid search (vector + metadata)

**Cons:**
- Requires embedding generation
- More complex to set up
- Additional AI costs

### 3. Recommended Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Storage Locations                     │
├─────────────┬────────────┬─────────────┬───────────────┤
│ Local Drive │   S3/GCS   │Network Drive│ External HDD  │
└──────┬──────┴─────┬──────┴──────┬──────┴───────┬───────┘
       │            │             │              │
       └────────────┴─────────────┴──────────────┘
                           │
                    ┌──────▼──────┐
                    │   Scanner   │ (Discovers & indexes files)
                    └──────┬──────┘
                           │
                ┌──────────▼──────────┐
                │  Location Registry  │ (Tracks file locations)
                │    (SQLite/JSON)    │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │   Search Index      │
                │  (Meilisearch +     │
                │   Vector DB)        │
                └──────────┬──────────┘
                           │
                    ┌──────▼──────┐
                    │ Alice API   │
                    └─────────────┘
```

### 4. Implementation Plan

#### Phase 1: Multi-Path Support
```yaml
# settings.yaml
storage:
  locations:
    primary:
      type: local
      path: /Users/sandro/Pictures/AI
      purpose: organized  # Where to put organized files
    
    inbox:
      type: local
      path: /Users/sandro/Downloads
      scan: true  # Monitor for new files
    
    archive:
      type: s3
      bucket: my-ai-archive
      prefix: images/
      purpose: long-term  # Move old files here
    
    external:
      type: local
      path: /Volumes/External/AI
      scan: true
      
  rules:
    - match: "*.mp4"
      location: archive  # Videos go to S3
    - match: "project:client-*"
      location: external  # Client work on external
    - default: primary
```

#### Phase 2: Search Architecture
1. **Meilisearch** for primary search (tags, prompts, descriptions)
2. **SQLite** for location registry and quick lookups
3. **Qdrant** for semantic similarity search (optional)

#### Phase 3: Metadata Strategy
```python
# Embedded in file (via EXIF/XMP)
{
    "alice:tags": {
        "style": ["photorealistic", "portrait"],
        "mood": ["dramatic", "moody"],
        "subject": ["woman", "close-up"]
    },
    "alice:prompt": "Generated prompt...",
    "alice:hash": "sha256:abc123...",
    "alice:understanding": {
        "providers": ["anthropic", "openai"],
        "timestamp": "2024-01-01T00:00:00Z"
    }
}

# In search index (Meilisearch)
{
    "id": "sha256:abc123...",
    "locations": [
        {"type": "local", "path": "/path/to/file.jpg"},
        {"type": "s3", "url": "s3://bucket/file.jpg"}
    ],
    "tags": ["photorealistic", "portrait", "dramatic"],
    "prompt": "...",
    "embedding": [0.1, 0.2, ...],  # For vector search
    "last_seen": "2024-01-01T00:00:00Z"
}
```

### 5. Migration Strategy
1. Start with SQLite for simplicity
2. Add Meilisearch when search becomes slow
3. Add vector database when semantic search needed
4. PostgreSQL remains for:
   - Event sourcing
   - Workflow orchestration
   - User preferences (future)

### 6. Benefits of This Approach
- **Resilient**: Can rebuild from files alone
- **Flexible**: Easy to add new storage locations
- **Scalable**: Can handle millions of files
- **Fast**: Dedicated search index
- **Cost-effective**: Only index what you need
- **Future-proof**: Can add AI features gradually