# Search Performance Improvements

This document describes the search performance optimizations implemented in AliceMultiverse.

## Overview

The search system has been optimized to handle large-scale asset collections efficiently through:

1. **N+1 Query Prevention** - Eager loading of relationships
2. **Database Indexing** - Strategic indexes for common query patterns  
3. **Proper Pagination** - Efficient result set handling
4. **Redis Caching** - Fast repeated query responses

## Implementation Details

### 1. N+1 Query Prevention

**Problem**: When fetching assets with related data (tags, projects, relationships), each asset would trigger additional queries to load its relationships.

**Solution**: Implemented eager loading using SQLAlchemy's `selectinload` and `joinedload`:

```python
# In repository.py
query = query.options(
    selectinload(Asset.tags),           # Load all tags in one query
    joinedload(Asset.project),          # Join project data
    selectinload(Asset.known_paths),    # Load paths efficiently
    selectinload(Asset.parent_relationships),
    selectinload(Asset.child_relationships)
)
```

### 2. Database Indexes

Created strategic indexes via Alembic migration (`ab0645bf664b_add_search_performance_indexes.py`):

**Composite Indexes**:
- `idx_assets_search` on (media_type, source_type, rating)
- `idx_assets_date_type` on (first_seen DESC, media_type)
- `idx_tags_search` on (tag_type, tag_value, asset_id)

**Partial Indexes** (PostgreSQL only):
- `idx_assets_high_rating` for assets with rating >= 4
- `idx_assets_images` for image assets sorted by date

**Covering Index**:
- `idx_tags_covering` includes all needed columns to avoid table lookups

### 3. Pagination Implementation

**New Repository Method**: `search_with_count()`
- Returns both results and total count efficiently
- Separates count query from data fetch
- Applies eager loading only to final result set

```python
# Get count without eager loading
total_count = query.count()

# Apply eager loading for actual results
query = query.options(...)
assets = query.offset(offset).limit(limit).all()

return assets, total_count
```

### 4. Redis Caching

**Cache Infrastructure** (`redis_cache.py`):
- Configurable TTL (default 5 minutes for search)
- Support for Redis Sentinel (high availability)
- Graceful fallback when Redis unavailable

**Search Result Caching**:
- Cache key based on query parameters
- Stores serialized results with facets
- Automatic cache invalidation after TTL

**Configuration**:
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=your_password  # Optional
```

## Performance Gains

Expected improvements:

1. **N+1 Prevention**: 
   - Before: 1 + N queries (N = number of assets)
   - After: 3-5 queries total regardless of result size

2. **Index Usage**:
   - Tag searches: ~10x faster with covering index
   - Date range queries: ~5x faster with composite index
   - High-quality filter: ~20x faster with partial index

3. **Caching**:
   - Repeated queries: <5ms (from cache)
   - Cache hit rate: ~60-80% for typical usage

4. **Pagination**:
   - Large result sets: Constant memory usage
   - Total count: Single optimized query

## Usage

The optimizations are transparent to API users:

```python
# All optimizations apply automatically
result = alice.search_assets(SearchRequest(
    filters={
        "media_type": MediaType.IMAGE,
        "tags": ["cyberpunk", "portrait"],
        "quality_rating": {"min": 4}
    },
    limit=50,
    offset=0
))
```

## Monitoring

### Database Queries

Use the profiling script to analyze query patterns:

```bash
python scripts/profile_search_performance.py
```

### Cache Statistics

```python
from alicemultiverse.database.redis_cache import RedisCache

cache = RedisCache()
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

## Future Enhancements

1. **Elasticsearch Integration** - For full-text search on prompts
2. **Embedding Search** - Vector similarity search for semantic queries
3. **Query Result Streaming** - For extremely large result sets
4. **Materialized Views** - For complex aggregations
5. **Read Replicas** - Scale read operations horizontally