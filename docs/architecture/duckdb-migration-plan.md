# DuckDB Migration & Event System Redesign Plan

## Overview
Migrate from PostgreSQL to DuckDB for metadata/search (OLAP) and evaluate alternatives for event streaming.

## Current State
- PostgreSQL used for everything (metadata, search, events)
- Most queries are analytical (OLAP), not transactional
- Event system uses PostgreSQL NOTIFY/LISTEN

## Target State
- DuckDB for all metadata, search, and analytics
- Lightweight event streaming solution
- Simpler architecture with less operational overhead

## Phase 1: DuckDB Metadata Store (Week 1)

### 1.1 Create DuckDB Schema
```python
# alicemultiverse/storage/duckdb_store.py
class DuckDBMetadataStore:
    """
    CREATE TABLE assets (
        -- Identity
        content_hash VARCHAR PRIMARY KEY,
        
        -- Locations (array of paths/URLs)
        locations STRUCT(
            path VARCHAR,
            type VARCHAR,  -- local, s3, gcs
            last_verified TIMESTAMP
        )[],
        
        -- Core metadata
        media_type VARCHAR,
        file_size BIGINT,
        created_at TIMESTAMP,
        
        -- Tags as nested structure
        tags STRUCT(
            style VARCHAR[],
            mood VARCHAR[],
            subject VARCHAR[],
            color VARCHAR[],
            technical VARCHAR[],
            custom MAP(VARCHAR, VARCHAR[])
        ),
        
        -- AI Understanding
        understanding STRUCT(
            description TEXT,
            generated_prompt TEXT,
            negative_prompt TEXT,
            provider VARCHAR,
            model VARCHAR,
            cost DECIMAL(10,6),
            analyzed_at TIMESTAMP
        ),
        
        -- Embeddings for similarity
        embedding FLOAT[1536],  -- OpenAI ada-002 size
        
        -- Full metadata as JSON
        metadata JSON
    );
    
    -- Indexes
    CREATE INDEX idx_media_type ON assets(media_type);
    CREATE INDEX idx_created ON assets(created_at);
    """
```

### 1.2 Migration Tools
- [ ] Create DuckDB adapter matching current interface
- [ ] Build migration script from PostgreSQL
- [ ] Implement Parquet export/import
- [ ] Add backward compatibility layer

### 1.3 Search Optimization
```sql
-- Tag search (DuckDB's array functions)
SELECT * FROM assets
WHERE list_contains(tags.style, 'cyberpunk')
   OR list_contains(tags.mood, 'dramatic');

-- Full-text search on descriptions
SELECT * FROM assets
WHERE regexp_matches(understanding.description, 'portrait.*woman');

-- Similarity search (with vss extension)
SELECT * FROM assets
ORDER BY array_distance(embedding, ?::FLOAT[]) 
LIMIT 20;
```

## Phase 2: Storage Location Tracking (Week 2)

### 2.1 Location Registry in DuckDB
```sql
CREATE TABLE locations (
    name VARCHAR PRIMARY KEY,
    type VARCHAR,  -- local, s3, gcs, network
    config JSON,
    purpose VARCHAR[],  -- inbox, organized, archive
    scan_enabled BOOLEAN,
    last_scan TIMESTAMP
);

-- Track where each file is
CREATE TABLE file_locations (
    content_hash VARCHAR,
    location_name VARCHAR,
    path VARCHAR,
    exists BOOLEAN,
    last_verified TIMESTAMP,
    metadata_embedded BOOLEAN,
    cloud_metadata JSON,
    PRIMARY KEY (content_hash, location_name)
);
```

### 2.2 Multi-Location Queries
```python
def find_file_everywhere(content_hash: str):
    return db.execute("""
        SELECT 
            l.name, 
            l.type,
            fl.path,
            fl.exists
        FROM file_locations fl
        JOIN locations l ON fl.location_name = l.name
        WHERE fl.content_hash = ?
        AND fl.exists = true
    """, [content_hash])
```

## Phase 3: Event System Alternatives (Week 3)

### Option A: Redis Streams (Recommended)
```python
# Lightweight, perfect for events
class RedisEventStream:
    def publish(self, event_type: str, data: dict):
        self.redis.xadd(
            f"alice:events:{event_type}",
            {"data": json.dumps(data)}
        )
    
    def subscribe(self, event_types: List[str]):
        # Consumer groups for reliability
        for message in self.redis.xreadgroup(...):
            yield Event.from_redis(message)
```

**Pros:**
- Built for streaming
- Consumer groups ensure delivery
- Automatic expiration
- Pub/sub + persistence
- Already using Redis for caching

**Cons:**
- Another dependency (but we already have it)

### Option B: SQLite with Triggers
```python
# Minimal approach - SQLite for events
class SQLiteEventStore:
    """
    CREATE TABLE events (
        id INTEGER PRIMARY KEY,
        event_type TEXT,
        data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Trigger for notifications
    CREATE TRIGGER event_notify
    AFTER INSERT ON events
    BEGIN
        SELECT emit_event(NEW.event_type, NEW.data);
    END;
    """
```

**Pros:**
- Zero additional dependencies
- Simple file-based storage
- Can distribute event logs

**Cons:**
- No built-in pub/sub
- Polling required

### Option C: NATS/NATS JetStream
```python
# Modern cloud-native messaging
class NATSEventStream:
    async def publish(self, subject: str, data: dict):
        await self.nc.publish(
            f"alice.events.{subject}",
            json.dumps(data).encode()
        )
```

**Pros:**
- Designed for microservices
- Persistent + streaming
- Excellent performance
- Cloud-native

**Cons:**
- New dependency
- More complex than needed?

### Option D: Simple File-Based Events
```python
# Ultra-simple approach
class FileEventLog:
    def append(self, event: Event):
        # Append to daily log file
        with open(f"events/{date.today()}.jsonl", "a") as f:
            f.write(json.dumps(event.dict()) + "\n")
    
    def tail(self, follow=True):
        # Like 'tail -f' for events
        ...
```

**Pros:**
- Dead simple
- No dependencies
- Can use standard tools

**Cons:**
- No real-time pub/sub
- Manual cleanup needed

## Phase 4: Implementation Timeline

### Week 1: DuckDB Core
- [ ] Create DuckDBMetadataStore class
- [ ] Implement search interface
- [ ] Migration script from PostgreSQL
- [ ] Unit tests

### Week 2: Multi-Location Support
- [ ] Location registry
- [ ] File tracking across locations
- [ ] Content-addressed operations
- [ ] S3/GCS adapters

### Week 3: Event System
- [ ] Evaluate options with PoC
- [ ] Implement chosen solution
- [ ] Migrate existing events
- [ ] Update event consumers

### Week 4: Integration
- [ ] Update all components
- [ ] Performance testing
- [ ] Documentation
- [ ] Rollback plan

## Decision Matrix

| Criteria | PostgreSQL | DuckDB + Redis | DuckDB + SQLite | DuckDB + Files |
|----------|------------|----------------|------------------|----------------|
| Complexity | High | Medium | Low | Very Low |
| Performance | Good | Excellent | Good | Fair |
| Ops Overhead | High | Medium | None | None |
| Scalability | Excellent | Excellent | Limited | Limited |
| Cost | $$$ | $$ | Free | Free |
| Real-time Events | Yes | Yes | Polling | Polling |

## Recommendation

**Primary Choice: DuckDB + Redis Streams**
- DuckDB for all OLAP (search, analytics, metadata)
- Redis Streams for events (we already use Redis)
- Both are embedded/lightweight
- Excellent performance
- Minimal operational overhead

**Fallback Choice: DuckDB + SQLite**
- If we want zero additional dependencies
- SQLite for simple event log
- Polling for event consumption
- Perfect for single-instance deployment

## Migration Strategy

1. **Parallel Run**: Run DuckDB alongside PostgreSQL
2. **Gradual Migration**: Move read queries first
3. **Validation**: Ensure results match
4. **Cutover**: Switch writes to DuckDB
5. **Cleanup**: Remove PostgreSQL dependency

## Code Examples

### DuckDB Search Implementation
```python
class DuckDBSearch:
    def search_by_tags(self, tags: Dict[str, List[str]]):
        """Search using DuckDB's native array functions."""
        conditions = []
        params = []
        
        for category, values in tags.items():
            conditions.append(
                f"list_has_any(tags.{category}, ?::VARCHAR[])"
            )
            params.append(values)
        
        query = f"""
            SELECT * FROM assets
            WHERE {' OR '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT 100
        """
        return self.conn.execute(query, params).fetchall()
```

### Event Publishing Comparison
```python
# Redis (recommended)
await redis.xadd("alice:asset.processed", {
    "hash": content_hash,
    "path": file_path,
    "tags": json.dumps(tags)
})

# SQLite (simple)
db.execute(
    "INSERT INTO events (type, data) VALUES (?, ?)",
    ["asset.processed", json.dumps(event_data)]
)

# File-based (minimal)
with open("events.jsonl", "a") as f:
    f.write(json.dumps({
        "type": "asset.processed",
        "data": event_data,
        "ts": datetime.now().isoformat()
    }) + "\n")
```

## Next Steps

1. **Prototype**: Build DuckDB PoC with subset of data
2. **Benchmark**: Compare query performance
3. **Event PoC**: Test Redis Streams vs SQLite
4. **Decision**: Choose event system
5. **Implement**: Follow phased approach