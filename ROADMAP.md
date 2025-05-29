# AliceMultiverse Roadmap

## Vision

AliceMultiverse is an AI-native service that operates exclusively through AI assistants. It bridges creative professionals with AI generation tools and APIs, excelling at detecting, organizing, and assessing AI-generated content while maintaining context across extended creative sessions.

## Critical Questions (Re-evaluate Monthly)

1. **Are we solving real problems?** Current focus on organization is proven. Workflow engine might be premature.
2. **Is the architecture still simple?** After simplification, yes. Keep monitoring for complexity creep.
3. **What would users pay for?** Provider integrations (Midjourney, Hedra) > workflow engine.
4. **What's broken right now?** 11% test failures, no retry logic, missing provider health checks.

## Next Up (Priority Order)

### 1. Provider Integrations (Direct Value)
- [ ] Hedra (AI avatar videos) - Character-1 API for talking avatars
- [ ] Midjourney (via proxy API) - Most requested by creatives
- [ ] ElevenLabs (voice generation) - Complete audio pipeline
- [ ] Suno (music generation) - For music video production

### 2. Enhanced Search & Discovery (Core Functionality)
- [ ] Fix existing search performance issues
- [ ] Add media_type and tag-based filtering
- [ ] Implement date range and quality filters
- [ ] Create batch search API for AI assistants

### 3. Workflow Engine (Future Vision)
- [ ] Define minimal workflow format (JSON/YAML)
- [ ] Implement sequential execution only (no DAG yet)
- [ ] Add basic retry and error handling
- [ ] Enable workflow persistence and resumption

## Backlog (Re-evaluate Weekly)

### Quality & Reliability (Should be higher priority?)
- Fix remaining test failures (89% → 100%)
- Add integration tests for all providers
- Implement retry logic for API failures
- Add provider health monitoring

### Performance Improvements
- Optimize database queries (N+1 issues)
- Implement connection pooling properly
- Add Redis caching for embeddings
- Batch API calls where possible

### Additional Providers
- Stable Diffusion (local/cloud)
- RunwayML (video generation)
- Replicate (multiple models)
- Together AI (open models)

### Advanced Features
- Music video production (beat sync, timeline)
- Multi-user support (teams, permissions)
- ComfyUI workflow integration
- Real-time collaboration

### Technical Debt
- Increase test coverage to 95%+
- Add missing type hints
- Document internal APIs
- Performance profiling

## Recently Completed ✅

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