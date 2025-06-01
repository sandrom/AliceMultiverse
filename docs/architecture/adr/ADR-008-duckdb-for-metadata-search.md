# ADR-008: DuckDB for Metadata Search and Analytics

**Status**: Accepted  
**Date**: 2025-01-31  
**Context**: PostgreSQL overhead for analytical queries

## Context

AliceMultiverse's search and metadata queries are fundamentally analytical (OLAP) rather than transactional (OLTP):
- Complex tag searches with array operations
- Aggregations across large datasets
- Read-heavy workload (99%+ reads)
- No real-time transaction requirements

PostgreSQL, while excellent for OLTP, introduced unnecessary operational complexity:
- Required server management
- Connection pooling overhead
- Suboptimal for columnar analytical queries
- Complex deployment in containerized environments

## Decision

Adopt DuckDB as the primary metadata storage and search engine:
- Embedded database (just a file)
- Columnar storage optimized for analytics
- Native array and JSON support
- Direct Parquet/S3 querying capability
- Zero operational overhead

Keep Redis Streams for real-time event streaming (already in use).

## Rationale

### Why DuckDB

1. **Performance**: 10-100x faster for analytical queries
2. **Simplicity**: No server to manage, just a file
3. **Features**: Native support for our query patterns
4. **Portability**: Database travels with the application
5. **Cost**: No infrastructure costs

### Query Performance Comparison

```sql
-- Finding images with specific tags (PostgreSQL)
SELECT * FROM assets 
WHERE tags && ARRAY['cyberpunk', 'neon']
-- Time: ~450ms on 100k records

-- Same query (DuckDB)
SELECT * FROM assets 
WHERE list_contains(tags, 'cyberpunk') 
  AND list_contains(tags, 'neon')
-- Time: ~12ms on 100k records
```

### Alternatives Considered

1. **SQLite**: Considered but lacks advanced array operations
2. **ClickHouse**: Too heavy for embedded use case
3. **Optimize PostgreSQL**: Still requires server management
4. **Pure Redis**: Not suitable for complex queries

## Consequences

### Positive
- Massive performance improvement for searches
- Simplified deployment (no database server)
- Reduced infrastructure costs
- Better developer experience
- Can query external data directly (S3, Parquet)

### Negative
- Migration effort required
- Loss of some PostgreSQL-specific features
- Need to rewrite some queries
- Less mature ecosystem

## Migration Strategy

1. Implement DuckDB alongside PostgreSQL
2. Mirror writes to both systems
3. Gradually migrate read queries
4. Validate data consistency
5. Remove PostgreSQL dependency

## Implementation Details

- `alicemultiverse/storage/duckdb_cache.py` - DuckDB implementation
- `alicemultiverse/metadata/search.py` - Search queries
- Migration scripts in `alembic/versions/`

## References

- [DuckDB Migration Plan](../duckdb-migration-plan.md)
- [Performance Benchmarks](../../benchmarks/search-performance.md)
- DuckDB Documentation: https://duckdb.org/
- Issue #312: Search performance problems