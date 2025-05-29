# AliceMultiverse Roadmap

## Vision

AliceMultiverse is an AI-native service that operates exclusively through AI assistants. It bridges creative professionals with AI generation tools and APIs, excelling at detecting, organizing, and assessing AI-generated content while maintaining context across extended creative sessions.

## Next Up (Priority Order)

### 1. Workflow Engine
- [ ] Design workflow definition format
- [ ] Implement workflow executor
- [ ] Add progress tracking and resumption

### 2. Enhanced Search & Discovery
- [ ] Implement semantic search with embeddings
- [ ] Add advanced filtering and facets
- [ ] Create search API for AI assistants

### 3. More Provider Integrations
- [ ] Hedra (AI avatar videos) - Character-1 API for talking avatars
- [ ] Midjourney (via proxy API)
- [ ] Stable Diffusion (local/cloud)
- [ ] RunwayML for video generation

## Backlog (Unprioritized)

### Music Video Production Features
- Audio analysis (beat detection, mood, sections)
- Timeline generation (frame-accurate sync)
- Visual generation (beat-synchronized)

### Service Distribution
- Extract services (asset processing, workflow, projects)
- Dapr integration for infrastructure abstraction
- Multi-user and team features

### Performance & Scale
- GPU resource pooling
- Advanced caching strategies
- Batch processing optimization

### Integrations
- ComfyUI workflow support
- DaVinci Resolve plugins
- Real-time collaboration

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

- **Creative Chaos**: Support how creative minds actually work
- **Local-First**: User data sovereignty with optional cloud
- **Progressive Enhancement**: Each phase delivers working software
- **Event-Driven**: Loose coupling for organic evolution
- **Continuous Learning**: Adapt priorities based on implementation insights

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

### Priority Re-evaluation
- **Daily**: Review "Next Up" queue against backlog
- **After each commit**: Check if learnings change priorities
- **On significant findings**: Immediately re-order based on new information
- Items from backlog may jump to "Next Up" if they become critical
- Document why priorities changed in commit messages

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