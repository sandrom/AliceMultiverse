# DuckDB Implementation Consolidation Report

## Executive Summary

AliceMultiverse currently has two separate DuckDB implementations that serve different but overlapping purposes:
1. **DuckDBSearchCache** (`storage/duckdb_cache.py`) - A cache for fast search with focus on file locations
2. **DuckDBSearch** (`storage/duckdb_search.py`) - A search engine with focus on query capabilities

These implementations should be consolidated into a single, unified system.

## Detailed Analysis

### 1. DuckDBSearchCache (`duckdb_cache.py`)

**Purpose**: A search cache that can be rebuilt from files at any time. Emphasizes that files are the source of truth.

**Key Features**:
- Multi-location tracking (same content can exist in multiple places)
- Storage type awareness (local, s3, gcs, network)
- Structured understanding and generation metadata
- Embeddings support for similarity search
- Export to Parquet for analytics
- Nested tag structure with custom tags as JSON

**Schema Design**:
```sql
- assets (content_hash, locations[], media_type, file_size, created_at, modified_at)
- asset_tags (content_hash, style[], mood[], subject[], color[], technical[], objects[], custom_tags JSON)
- asset_understanding (content_hash, understanding STRUCT, model_outputs JSON, embedding FLOAT[1536])
- asset_generation (content_hash, generation STRUCT)
```

**Used By**:
- ImagePresentationAPI (for collaborative browsing)
- MCP Server (for image presentation)
- Storage demos and tests
- Multi-path scanner
- Auto-migration system

### 2. DuckDBSearch (`duckdb_search.py`)

**Purpose**: Search functionality for AliceMultiverse, replacing PostgreSQL implementation.

**Key Features**:
- Full-text search on prompts and descriptions
- Faceted search with aggregations
- Perceptual hash support for similarity search
- Advanced filtering (date ranges, quality ratings, dimensions)
- Direct compatibility with search API models
- Performance optimizations with indexes

**Schema Design**:
```sql
- assets (content_hash, file_path, media_type, file_size, width, height, ai_source, quality_rating, metadata JSON, prompt TEXT, description TEXT)
- asset_tags (content_hash, tags[], style_tags[], mood_tags[], subject_tags[], etc.)
- perceptual_hashes (content_hash, phash, dhash, ahash)
```

**Used By**:
- OptimizedSearchHandler (main search interface)
- Video creation workflows
- Media organizer
- Selection service
- Search demos

## Key Differences

### 1. **Architecture Philosophy**
- **DuckDBSearchCache**: Explicitly a cache that can be rebuilt, emphasizes file-first approach
- **DuckDBSearch**: Positioned as primary search engine, more database-centric

### 2. **Location Handling**
- **DuckDBSearchCache**: Sophisticated multi-location support with array of location structs
- **DuckDBSearch**: Single file_path string field

### 3. **Metadata Storage**
- **DuckDBSearchCache**: Structured approach with separate tables for understanding/generation
- **DuckDBSearch**: JSON blobs for metadata and generation_params

### 4. **Tag Organization**
- **DuckDBSearchCache**: Clean separation by category with custom_tags as JSON
- **DuckDBSearch**: Both combined tags[] and separate category arrays

### 5. **Search Capabilities**
- **DuckDBSearchCache**: Basic tag and text search
- **DuckDBSearch**: Advanced search with facets, filters, and query optimization

### 6. **Similarity Search**
- **DuckDBSearchCache**: Embeddings support (1536-dim vectors)
- **DuckDBSearch**: Perceptual hashes (phash, dhash, ahash)

## Usage Patterns

### DuckDBSearchCache Usage:
```python
# Multi-location awareness
cache.upsert_asset(
    content_hash="abc123",
    file_path=Path("/local/path/image.jpg"),
    metadata=metadata,
    storage_type="local"
)

# Tag-based search
results = cache.search_by_tags({
    "style": ["cyberpunk", "neon"],
    "mood": ["dark", "atmospheric"]
})
```

### DuckDBSearch Usage:
```python
# Index with full metadata
search_db.index_asset({
    "content_hash": "abc123",
    "file_path": "/local/path/image.jpg",
    "media_type": "image",
    "tags": ["cyberpunk", "neon"],
    "prompt": "A cyberpunk scene with neon lights"
})

# Advanced search with filters
results, total = search_db.search(
    filters={
        "tags": ["cyberpunk"],
        "quality_rating": {"min": 80},
        "date_range": {"start": "2024-01-01"}
    },
    sort_by="quality_rating",
    limit=50
)
```

## Consolidation Recommendations

### 1. **Unified Schema Design**

Combine the best of both approaches:

```sql
CREATE TABLE assets (
    -- Identity
    content_hash VARCHAR PRIMARY KEY,
    
    -- Locations (from DuckDBSearchCache)
    locations STRUCT(
        path VARCHAR,
        storage_type VARCHAR,
        last_verified TIMESTAMP,
        has_embedded_metadata BOOLEAN
    )[],
    
    -- Core metadata
    media_type VARCHAR,
    file_size BIGINT,
    width INTEGER,
    height INTEGER,
    
    -- Quality and source (from DuckDBSearch)
    ai_source VARCHAR,
    quality_rating DOUBLE,
    
    -- Timestamps
    created_at TIMESTAMP,
    modified_at TIMESTAMP,
    discovered_at TIMESTAMP,
    last_file_scan TIMESTAMP,
    
    -- Search fields (from DuckDBSearch)
    prompt TEXT,
    description TEXT,
    
    -- Flexible metadata
    metadata JSON,
    generation_params JSON
);

-- Unified tags table
CREATE TABLE asset_tags (
    content_hash VARCHAR PRIMARY KEY,
    
    -- All tags for general search
    tags VARCHAR[],
    
    -- Categorized tags (best of both)
    style VARCHAR[],
    mood VARCHAR[],
    subject VARCHAR[],
    color VARCHAR[],
    technical VARCHAR[],
    objects VARCHAR[],
    
    -- Custom tags as JSON for flexibility
    custom_tags JSON,
    
    FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
);

-- Keep separate tables for complex data
CREATE TABLE asset_understanding (
    -- From DuckDBSearchCache
);

CREATE TABLE asset_generation (
    -- From DuckDBSearchCache
);

CREATE TABLE perceptual_hashes (
    -- From DuckDBSearch
);

CREATE TABLE embeddings (
    -- New: combine both similarity approaches
    content_hash VARCHAR PRIMARY KEY,
    embedding_type VARCHAR,  -- 'openai-ada-002', 'clip', etc.
    embedding FLOAT[],
    FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
);
```

### 2. **Unified API**

Create a single class that provides both interfaces:

```python
class UnifiedDuckDBStorage:
    """Unified DuckDB storage for AliceMultiverse."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        self.conn = duckdb.connect(str(db_path) if db_path else ":memory:")
        self._init_schema()
    
    # Methods from DuckDBSearchCache
    def upsert_asset(self, content_hash: str, file_path: Path, metadata: Dict, storage_type: str = "local") -> None:
        """Add or update an asset with location tracking."""
        pass
    
    def search_by_tags(self, tags: Dict[str, List[str]], limit: int = 100) -> List[Dict]:
        """Search by categorized tags."""
        pass
    
    # Methods from DuckDBSearch  
    def search(self, filters: Dict, sort_by: str = "created_at", limit: int = 50) -> Tuple[List[Dict], int]:
        """Advanced search with filters and facets."""
        pass
    
    def get_facets(self, filters: Dict = None) -> Dict[str, List[Dict]]:
        """Get search facets for UI."""
        pass
    
    # New unified methods
    def find_similar(self, content_hash: str, method: str = "phash", threshold: float = 0.9) -> List[Dict]:
        """Find similar assets using specified method."""
        pass
```

### 3. **Migration Strategy**

1. **Phase 1**: Create unified implementation with compatibility layer
2. **Phase 2**: Update all imports to use compatibility layer
3. **Phase 3**: Migrate data from both schemas to unified schema
4. **Phase 4**: Remove old implementations

### 4. **Benefits of Consolidation**

1. **Reduced Complexity**: One implementation to maintain
2. **Better Performance**: Single database connection, optimized queries
3. **Feature Completeness**: All features available everywhere
4. **Consistent API**: Same interface throughout codebase
5. **Easier Testing**: One set of tests to maintain

## Implementation Priority

Based on usage analysis:

1. **High Priority Features** (used by many components):
   - Multi-location support (from DuckDBSearchCache)
   - Advanced search and facets (from DuckDBSearch)
   - Tag categorization (from both)
   - Content hash as primary key (from both)

2. **Medium Priority Features**:
   - Perceptual hashes (from DuckDBSearch)
   - Embeddings (from DuckDBSearchCache)
   - Export to Parquet (from DuckDBSearchCache)
   - Full-text search (from DuckDBSearch)

3. **Low Priority Features**:
   - Some specific metadata fields can be migrated gradually

## Next Steps

1. **Design Review**: Review the proposed unified schema with the team
2. **Compatibility Layer**: Create a compatibility layer that implements both interfaces
3. **Test Coverage**: Ensure comprehensive tests for all functionality
4. **Gradual Migration**: Migrate components one by one to the unified implementation
5. **Performance Testing**: Benchmark the unified implementation
6. **Documentation**: Update all documentation to reflect the unified approach

## Conclusion

The two DuckDB implementations serve complementary purposes but have significant overlap. Consolidating them will:
- Simplify the codebase
- Improve maintainability
- Provide a more powerful and flexible storage solution
- Better align with the file-first architecture principle

The unified implementation should preserve the best features of both while eliminating redundancy and confusion.