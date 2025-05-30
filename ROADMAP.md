# AliceMultiverse Roadmap

## Vision

AliceMultiverse is an AI-native service that operates exclusively through AI assistants. It bridges creative professionals with AI generation tools and APIs, excelling at detecting, organizing, and assessing AI-generated content while maintaining context across extended creative sessions.

## Critical Questions (Re-evaluate Monthly)

1. **Are we solving real problems?** Media organization ✓, Quality assessment ✓, Generation tracking ✓
2. **Is the architecture still simple?** 4,100 lines removed ✓, PostgreSQL-only ✓, One provider base ✓
3. **What would users pay for?** Generation tracking > Hedra avatars > Midjourney integration
4. **What's broken RIGHT NOW?** 
   - 1 remaining test failure (isolation issue)
   - Search performance needs optimization
   - No Hedra integration yet (user's requested feature)

## Next Up (Priority Order)

### 1. Fix What's Broken (Working Service First!) ✅
- [x] Fix remaining test failures (89% → 99.7% pass rate)
- [x] Add retry logic for all API calls (exponential backoff with jitter)
- [x] Implement provider health monitoring with circuit breakers
- [x] Fix database connection pool exhaustion issues

### 2. Observability & Monitoring (Know What's Broken) ✅
- [x] Add structured logging with correlation IDs
- [x] Implement Prometheus metrics for API calls
- [x] Create health check endpoints for each provider
- [x] Add performance profiling for slow queries

### 3. Provider Integrations (Direct User Value) ✅
- [x] Hedra (AI avatar videos) - Character-2 API for talking avatars
- [x] mmaudio (multimodal audio generation) - Already integrated via fal.ai provider

### 4. Search Performance (Measured Improvements) ✅
- [x] Profile and fix N+1 queries in asset search - Implemented eager loading with selectinload/joinedload
- [x] Add database indexes for common query patterns - Created composite and partial indexes via migration
- [x] Implement pagination for large result sets - Added search_with_count() and proper offset/limit
- [x] Cache embeddings in Redis for semantic search - Built RedisCache with search result caching

## Backlog (Re-evaluate Weekly)

### Workflow Engine (Deferred - No Evidence of Need Yet)
- Define workflow format (JSON/YAML)
- Implement sequential execution
- Add retry and error handling
- Enable persistence and resumption

### Performance Improvements
- Optimize database queries (N+1 issues)
- Implement connection pooling properly
- Add Redis caching for embeddings
- Batch API calls where possible

### Additional Providers
- Midjourney (via proxy API) - Most requested by creatives
- Suno (music generation) - For music video production
- Stable Diffusion (local/cloud)
- RunwayML (video generation)
- Replicate (multiple models)
- Together AI (open models)

### Multi-User Support (Consider for Next Up?)
- User authentication and sessions
- Team workspaces with shared projects
- Role-based access control
- Usage quotas per user/team

### Advanced Features
- Music video production (beat sync, timeline)
- ComfyUI workflow integration
- Real-time collaboration
- Advanced workflow orchestration

### Technical Debt
- Increase test coverage to 95%+
- Add missing type hints
- Document internal APIs
- Performance profiling

## Recently Completed ✅

### Search Performance Optimization (Jan 2025)
- Fixed N+1 queries by implementing eager loading for relationships
- Added strategic database indexes including composite and partial indexes
- Implemented proper pagination with separate count queries
- Built Redis caching layer for search results with 5-minute TTL
- Created optimized search handler replacing inefficient metadata search
- Documented performance improvements achieving ~10-20x speedup

### mmaudio Integration Verification (Jan 2025)
- Discovered mmaudio-v2 was already integrated in fal.ai provider
- Added comprehensive tests for mmaudio functionality
- Created example code for video-to-audio generation
- Verified all parameters work correctly (duration, cfg_strength, etc.)
- Supports adding synchronized audio to any video file

### Hedra Provider Integration (Jan 2025)
- Implemented complete Hedra Character-2 API support for talking avatars
- Support for generating AI avatar videos from image + audio inputs
- Aspect ratio and resolution options (16:9, 9:16, 1:1 / 540p, 720p)
- Async upload and polling for video generation
- Comprehensive test coverage for all provider methods

### Generation Tracking & Reproducibility (Jan 2025)
- Implemented comprehensive generation context tracking
- Store prompts, settings, and context in 3 places (metadata, database, sidecar)
- Added multi-reference support for FLUX Kontext models
- Changed sidecar files from JSON to YAML for better readability
- Enable easy recreation of any generation with full context
- Track source → output relationships in database

### Infrastructure Improvements (Jan 2025)
- Added exponential backoff with jitter for all API calls
- Implemented circuit breaker pattern for provider health
- Enhanced database connection pool management
- Added structured logging with correlation IDs
- Integrated Prometheus metrics for monitoring
- Fixed test suite from 89% to 99.7% pass rate

### Provider Model Updates (Jan 2025)
- Added Kling 2.1 Pro and Master variants for video generation
- Added complete FLUX Kontext family (Pro, Max) for iterative image editing
- Added BFL provider for direct Black Forest Labs API access
- Support for both fal.ai and bfl.ai endpoints for FLUX models
- Added specialized FLUX models: Fill, Canny, Depth control
- Updated pricing tiers to reflect quality differences

### Architecture Simplification (Jan 2025)
- Reduced event system from 2,600 to 300 lines using PostgreSQL NOTIFY/LISTEN
- Simplified provider abstractions from 4 layers to 1 unified base class
- Fixed all bare exception blocks per instructions.md
- Implemented video content hashing with ffmpeg
- Added comprehensive input validation and rate limiting
- Updated all documentation to reflect AI-native architecture
- Removed 79 empty/unused files and ~4,100 lines of over-engineered code

### Project Management Layer (Jan 2025)
- Created database models with budget tracking fields
- Implemented ProjectService with comprehensive budget management
- Added automatic project pausing when budget exceeded
- Integrated 5 new methods into Alice interface
- Created detailed cost tracking by provider and model
- Added 17 comprehensive tests for full coverage
- Published events for all project state changes

### Event System Enhancement (Jan 2025)
- Created EventStore abstraction for flexible persistence backends
- Added SQLite backend for simpler deployments (no Redis required)
- Implemented event schema versioning with migration support
- Added consumer groups and dead letter queue
- Integrated persistence into EnhancedEventBus
- Created comprehensive migration guide

### Provider Abstraction (Jan 2025)
- Extracted base provider interface with budget management
- Created provider registry with cost tracking
- Added OpenAI provider (DALL-E 3, GPT-4 Vision)
- Added Anthropic provider (Claude 3 models with vision)
- Implemented comprehensive test coverage

### Test Suite Restoration (Jan 2025)
- Fixed import errors throughout test suite
- Updated event system references (removed v2 modules)
- Fixed datetime deprecation warnings
- Verified Kubernetes deployment
- Achieved 89% test pass rate (232/264 tests passing)

## Previously Completed

### Foundation
- ✅ Content-Addressed Storage
- ✅ Unified Metadata System
- ✅ Event-Driven Architecture
- ✅ Database Layer with migrations
- ✅ Alice Orchestration Interface

### Integrations
- ✅ fal.ai provider (FLUX, Kling models)
- ✅ Alice structured interface (Phase 1)
- ✅ Natural language asset search
- ✅ Context-aware responses
- ✅ Creative decision tracking

## Design Principles

- **Working Service First**: Stability and reliability over new features
- **Pragmatic & Direct**: Simple solutions, no over-engineering
- **AI-Native**: Built for AI assistants, not human CLI users
- **Progressive Enhancement**: Each phase delivers working software
- **Continuous Re-evaluation**: Adapt based on real usage and findings

## Implementation Guide

### After Each Step
```bash
# Verify working state:
alice --help                    # Still works
python -m pytest tests/unit/    # All tests pass
python scripts/event_monitor.py # Events flow correctly

# Provider testing:
alice --pipeline custom --stages "openai,anthropic" --dry-run
```

### When Context Resets
1. Check "Current Work" section for active task
2. Run `git status` for uncommitted work
3. Check last CHANGELOG.md entry
4. Continue from next unchecked step

### Adding New Work
1. Complete current work first
2. Re-evaluate priorities based on learnings
3. Move highest priority item from "Next Up" to "Current Work"
4. Update based on new insights

### Priority Re-evaluation (Per instructions.md)
- **Weekly**: Full backlog review - what delivers most value NOW?
- **After failures**: Quality/reliability issues jump to top priority
- **After user feedback**: Real usage trumps planned features
- **Test coverage < 90%**: Testing becomes priority
- **Performance issues**: Fix before adding features
- Document priority changes in commit messages

## Architecture Decisions

- **Alice as Orchestrator**: Not an AI, but coordinates between AIs and tools
- **Structured APIs Only**: No natural language processing in core
- **Event-First**: All features must publish/subscribe to events
- **Provider Abstraction**: All AI integrations through common interface

## How to Contribute

1. **Focus on Current Work** - Complete blocking tasks first
2. **One Step = One Commit** - Each checkbox is a working state
3. **Test Everything** - Unit tests + integration verification
4. **Update Docs** - Keep documentation current with changes
5. **Use ADRs** - Document significant architecture decisions

---

**Note**: This roadmap follows kanban principles. We work on the most important task, learn from implementation, and continuously re-evaluate priorities. No artificial timelines - we're optimizing for quality and learning.