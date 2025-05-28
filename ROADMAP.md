# AliceMultiverse Roadmap

## Vision

AliceMultiverse is evolving from a media organization tool into a comprehensive creative workflow hub that bridges AI assistants with creative tools and APIs. Our goal is to support creative professionals who work iteratively with AI over extended periods, maintaining context and continuity across sessions.

## Current Work

### 🚨 CRITICAL: Architecture Simplification
Deep review revealed over-engineering that violates our "pragmatic, direct, no bullshit" principle. Must simplify before new features.

**Event System Simplification (2,600 → 400 lines)**
- [x] **Step 1**: Create PostgreSQL-native event system → **Commit**: "Create PostgreSQL-native event system"
- [x] **Step 2**: Migrate event publishers → **Commit**: "Migrate event publishers to PostgreSQL events"
- [ ] **Step 3**: Remove legacy implementations → **Commit**: "Remove legacy event store implementations"

**Provider Abstraction Simplification (1,500 → 600 lines)**
- [ ] **Step 4**: Create unified provider base → **Commit**: "Create unified provider base class"
- [ ] **Step 5**: Migrate providers → **Commit**: "Migrate providers to unified base class"
- [ ] **Step 6**: Create simple registry → **Commit**: "Create simplified provider registry"
- [ ] **Step 7**: Remove old abstractions → **Commit**: "Remove legacy provider abstractions"

**Critical Issues**
- [ ] **Step 8**: Fix exception handling (33 files) → **Commit**: "Fix exception handling throughout codebase"
- [ ] **Step 9**: Implement video hashing → **Commit**: "Implement video content hashing"
- [ ] **Step 10**: Move hardcoded values → **Commit**: "Move hardcoded values to configuration"

**Additional Improvements**
- [ ] **Step 11**: Add input validation → **Commit**: "Add input validation for API endpoints"
- [ ] **Step 12**: Clean up empty files → **Commit**: "Remove empty and unused files"
- [ ] **Step 13**: Add type hints → **Commit**: "Add comprehensive type hints"
- [ ] **Step 14**: Update documentation → **Commit**: "Update documentation to reflect AI-native architecture"

[See detailed plan: docs/architecture/simplification-plan.md]

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