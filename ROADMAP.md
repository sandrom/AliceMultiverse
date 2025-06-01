# AliceMultiverse Roadmap

## Vision

AliceMultiverse is an AI-native service that operates exclusively through AI assistants. It bridges creative professionals with AI generation tools and APIs, excelling at detecting, organizing, and assessing AI-generated content while maintaining context across extended creative sessions.

## Critical Questions (Re-evaluate Daily)

1. **Are we solving real problems?** Media organization ✓, Image understanding ✓, Multi-location storage ✓
2. **Is the architecture still simple?** Quality code removed ✓, Flexible storage ✓, Self-contained files ✓
3. **What would users pay for?** Sound effects > Semantic search > Cross-platform sync > AI insights
4. **What's broken RIGHT NOW?** Quality assessment removed - need docs update

## Next Up (Priority Order)

### 1. ElevenLabs Sound Effects ✅
- [x] Implement ElevenLabs provider for AI sound effects
- [x] Support text-to-sound generation
- [x] Add duration and format parameters
- [x] Enable sound effects in video workflows
- [x] Create audio-focused workflow templates

### 2. Midjourney Integration
- [ ] Research proxy API options (no official API)
- [ ] Implement Discord bridge or third-party API
- [ ] Handle asynchronous generation pattern
- [ ] Parse and extract seed/parameters

### 3. DuckDB + Redis Streams Migration (IN PROGRESS)
- [x] Replace PostgreSQL with DuckDB for all metadata/search (OLAP)
- [x] Implement DuckDB search cache with content-addressed storage
- [x] Write comprehensive tests for DuckDB (13 tests passing)
- [x] Create file scanner to rebuild cache from embedded metadata
- [x] Update metadata embedder for new structure
- [ ] Implement Redis Streams for event system (in progress)
- [ ] Migrate existing PostgreSQL event consumers
- [ ] Update all event publishers to use Redis Streams
- [ ] Native array/JSON support for complex queries
- [ ] Direct Parquet file queries for archival data

### 4. Multi-Location Storage System
- [ ] Implement storage location registry in DuckDB
- [ ] Support local, S3/GCS, network drives
- [ ] Content-addressed file tracking
- [ ] Automatic file discovery across locations
- [ ] Storage rules engine (what goes where)

### 5. Model Comparison & Rating System
- [ ] Web interface for blind A/B comparison
- [ ] Simple keyboard controls: A/←, B/→, =/Space
- [ ] Optional strength rating (1-3) after picking winner
- [ ] Elo rating system to track model performance
- [ ] Store individual model outputs separately
- [ ] Auto-select models based on Elo ratings
- [ ] AI-initiated but human-rated workflow

### 6. Advanced Image Understanding
- [ ] Expand tag categories for better search
- [ ] Add custom instruction support per project
- [ ] Implement batch analysis for existing files
- [ ] Cost optimization with provider selection
- [ ] Semantic similarity search with DuckDB VSS extension
- [ ] Model selection based on performance data

## Backlog (Re-evaluate Weekly)

### Search & Discovery
- DuckDB columnar storage for fast analytical queries
- DuckDB VSS extension for vector similarity search
- Direct S3/GCS querying with DuckDB
- Rebuild search index from file metadata
- Cloud metadata integration (GCS/S3)

### Storage & Sync
- Multi-device synchronization
- Conflict resolution for moved files
- Bandwidth-aware sync strategies
- Incremental metadata updates

## Completed ✅

### Providers
- **Magnific/Freepik**: Upscaling with Magnific, Mystic image generation
- **Adobe Firefly**: Generative fill/expand, style reference, all v3 features
- **Google AI**: Imagen 3 ($0.03/image), Veo 2 video (8-second clips)
- **Ideogram**: Superior text rendering, V2/V2-Turbo/V3 models
- **Leonardo.ai**: Phoenix, Flux, PhotoReal, Alchemy, Elements system
- **Hedra**: Character-2 talking avatars from image + audio
- **fal.ai**: FLUX family, Kling video, mmaudio, specialized models
- **ElevenLabs**: AI sound effects generation with duration control, multiple formats

### Features
- **Multi-Modal Workflows**: Chain operations across providers with cost optimization
- **Image Understanding**: Multi-provider analysis with DeepSeek, OpenAI, Anthropic, Google
- **Flexible Storage**: Content-addressed tracking across multiple locations
- **Rich Tagging**: Semantic tags embedded in file metadata for portability
- **Search Performance**: 10-20x speedup with eager loading and Redis caching
- **Event System**: PostgreSQL-based with workflow events (migrating to Redis Streams)
- **Provider Infrastructure**: Unified base class with health monitoring

## Database Architecture Evolution

**Moving to DuckDB + Redis Streams** for better performance and simplicity:

- **DuckDB for OLAP**: All metadata, search, and analytics queries
- **Redis Streams for Events**: Real-time event streaming and pub/sub
- **PostgreSQL Removal**: Eliminating unnecessary complexity
- **Columnar Storage**: 10-100x faster for our analytical queries
- **Zero Ops**: DuckDB is just a file, Redis we already use

### Why DuckDB?
- We're doing analytics (OLAP), not transactions (OLTP)
- Native support for arrays, JSON, and nested data
- Can query Parquet files and S3 directly
- Columnar storage perfect for tag searches
- Embedded database with zero operational overhead

## Storage Architecture Vision

AliceMultiverse treats files as the source of truth, with all metadata embedded directly in the files. This enables:

- **True Portability**: Move files anywhere, metadata travels with them
- **Multi-Location Freedom**: Store on local drives, cloud (S3/GCS), network drives
- **Content-Addressed Discovery**: Find files by hash regardless of location
- **Resilient Search**: Rebuild search index from files at any time
- **Zero Lock-in**: Your files, your metadata, no proprietary database

### Example Configuration
```yaml
storage:
  locations:
    primary:
      type: local
      path: ~/Pictures/AI
      purpose: organized
    
    archive:
      type: s3
      bucket: ai-archive
      rules:
        - older_than: 90d
        - media_type: video
    
    external:
      type: local
      path: /Volumes/External
      scan: true
```

## Design Principles

1. **Files First**: All data lives in files, databases are just caches
2. **Working Service First**: Never break existing functionality
3. **User Value Focus**: Prioritize features users actually request and use
4. **Provider Diversity**: Support the tools creatives actually use
5. **Cost Awareness**: Always track and optimize generation costs
6. **Simple Integration**: Each provider should work standalone

## Implementation Guide

### Adding New Providers

1. Check existing patterns in `alicemultiverse/providers/`
2. Inherit from `BaseProvider` 
3. Implement required methods: `generate()`, `estimate_cost()`, `get_generation_time()`
4. Add comprehensive tests
5. Document API keys and setup
6. Add example usage

### Testing Requirements

```bash
# Before ANY commit:
python -m pytest tests/unit/test_new_provider.py
python -m pytest tests/integration/  # If applicable
alice --dry-run  # Verify CLI still works
```

### Recent Changes

**Major Pivot**: Removed quality assessment in favor of image understanding
- Quality scoring was too subjective for AI-generated content
- Replaced with semantic tagging and content analysis
- Multiple AI providers for comprehensive understanding
- Tags embedded in files for permanent searchability

**Storage Evolution**: Moving beyond single-folder organization
- Support for multiple storage locations
- Content-addressed file tracking
- Metadata lives with files, not in database
- Search index can be rebuilt anytime

**Database Evolution**: PostgreSQL → DuckDB + Redis Streams
- Recognized we're doing OLAP (analytics), not OLTP (transactions)
- DuckDB's columnar storage is 10-100x faster for tag searches
- Redis Streams perfect for lightweight event streaming
- Massive simplification: no more PostgreSQL server to manage

---

**Note**: This roadmap follows kanban principles. We work on the highest value task that you'll actually use, learn from implementation, and continuously re-evaluate priorities.