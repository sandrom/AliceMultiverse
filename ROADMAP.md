# AliceMultiverse Roadmap

## Vision

AliceMultiverse is evolving from a media organization tool into a comprehensive creative workflow hub that bridges AI assistants with creative tools and APIs. Our goal is to support creative professionals who work iteratively with AI over extended periods, maintaining context and continuity across sessions.

## Current Work

### 🚨 CRITICAL: Fix Broken Tests
Working application takes priority over new features. Import errors are fixed, but some tests still fail.

- [x] Fix import errors in pipeline tests (alicemultiverse.keys → alicemultiverse.core.keys)
- [x] Update event tests to use current event module structure (remove v2 references)
- [x] Fix alice_orchestrator test imports (CreativeIntent missing)
- [ ] Fix remaining test failures (20 failed, 13 errors - mostly async mocks and logic issues)

## Next Up (Priority Order)

### 1. Provider Abstraction [BLOCKING]
Must complete before adding more providers. This architectural foundation prevents technical debt.

- [x] **Step 1**: Extract base interface from fal_provider → **Commit**: "Extract provider interface"
- [ ] **Step 2**: Create provider registry with cost tracking → **Commit**: "Add provider registry"
- [ ] **Step 3**: Add OpenAI provider (DALL-E 3) → **Commit**: "Add OpenAI provider"
- [ ] **Step 4**: Add Anthropic provider (Claude vision) → **Commit**: "Add Anthropic provider"

### 2. Event System Enhancement
- [ ] Add version field to events + migration utils → **Commit**: "Add event schema versioning"
- [ ] Write ADR-006 for versioning strategy
- [ ] Add optional Redis persistence → **Commit**: "Add optional Redis persistence"
- [ ] Update ADR-002 with implementation

### 3. Project Management Layer
- [ ] Create project models + migrations → **Commit**: "Add project management models"
- [ ] Implement project service + budget tracking → **Commit**: "Add project service"
- [ ] Integrate into Alice interface → **Commit**: "Integrate projects into Alice"

### 4. Workflow Engine
- [ ] Design workflow definition format
- [ ] Implement workflow executor
- [ ] Add progress tracking and resumption

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

## Completed ✅

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