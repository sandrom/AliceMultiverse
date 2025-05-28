# AliceMultiverse Roadmap

## Vision

AliceMultiverse is evolving from a media organization tool into a comprehensive creative workflow hub that bridges AI assistants with creative tools and APIs. Our goal is to support creative professionals who work iteratively with AI over extended periods, maintaining context and continuity across sessions.

## Development Phases

### Phase 1: Foundation ✅ (Current)

**Status**: Completed foundations, actively implementing

- ✅ **Content-Addressed Storage** - Files tracked by content hash, not paths
- ✅ **Unified Metadata System** - Single source of truth for all metadata
- ✅ **Event-Driven Architecture** - Foundation for future microservices
- ✅ **Database Layer** - SQLAlchemy models with migration support
- ✅ **Alice Orchestration Interface** - Intelligent endpoint for AI assistants

### Phase 2: Integration 🚧 (Q1-Q2 2025)

**Focus**: Provider integrations and project management

> **⚠️ CRITICAL**: Provider abstraction MUST be completed before adding more providers.

#### 2.1 Provider System (Weeks 1-2)
- 🔲 **Provider Abstraction** [BLOCKING]
  - [ ] Step 1: Extract base interface from fal_provider → **Commit**: "Extract provider interface"
  - [ ] Step 2: Create provider registry with cost tracking → **Commit**: "Add provider registry"
  - [ ] Step 3: Add OpenAI provider (DALL-E 3) → **Commit**: "Add OpenAI provider"
  - [ ] Step 4: Add Anthropic provider (Claude vision) → **Commit**: "Add Anthropic provider"
- ✅ **fal.ai Integration**
  - FLUX and Kling models implemented ✅
  - Needs refactoring to use abstraction 🔄

#### 2.2 Event System Enhancement (Week 3)
- 🔲 **Schema Versioning**
  - [ ] Step 1: Add version field to events + migration utils → **Commit**: "Add event schema versioning"
  - [ ] Write ADR-006 for versioning strategy
- 🔲 **Redis Persistence** (Optional)
  - [ ] Step 2: Add optional Redis persistence → **Commit**: "Add optional Redis persistence"
  - [ ] Update ADR-002 with implementation

#### 2.3 Project Management (Weeks 4-5)
- 🔲 **Project Models**
  - [ ] Step 1: Create project models + migrations → **Commit**: "Add project management models"
  - [ ] Step 2: Implement project service + budget tracking → **Commit**: "Add project service"
  - [ ] Step 3: Integrate into Alice interface → **Commit**: "Integrate projects into Alice"

#### 2.4 Workflow Engine (Future)
- 🔲 **Pipeline Orchestration**
  - Reusable creative workflows
  - Multi-step generation pipelines
  - Progress tracking and resumption

- ✅ **Enhanced Alice Interface**
  - Natural language asset search ✅
  - Context-aware responses ✅
  - Creative decision tracking ✅
  - Creative memory system ✅
  - Pattern recognition 🔄

### Phase 3: Music Video Production 🎬 (Q2-Q3 2025)

**Focus**: Specialized features for music video creation

- 🔲 **Audio Analysis**
  - Beat detection and tempo mapping
  - Mood analysis over time
  - Section detection (verse/chorus)

- 🔲 **Timeline Generation**
  - Frame-accurate synchronization
  - Multiple export formats (AAF, EDL, FCPXML)
  - Beat grid alignment

- 🔲 **Visual Generation**
  - Beat-synchronized image creation
  - Style consistency across scenes
  - Batch generation management

### Phase 4: Distribution 🌐 (Q3-Q4 2025)

**Focus**: Scaling and team collaboration

- 🔲 **Service Extraction**
  - Asset processing service
  - Workflow execution service
  - Project management service

- 🔲 **Dapr Integration**
  - Infrastructure abstraction
  - Pub/sub communication
  - State management

- 🔲 **Team Features**
  - Multi-user projects
  - Permission management
  - Collaborative workflows

### Phase 5: Scale & Polish 🚀 (2026)

**Focus**: Production readiness and optimization

- 🔲 **Performance Optimization**
  - GPU resource pooling
  - Intelligent caching layers
  - Batch processing optimization

- 🔲 **Advanced Integrations**
  - ComfyUI workflows
  - DaVinci Resolve plugins
  - Real-time collaboration

- 🔲 **Enterprise Features**
  - Cloud deployment options
  - Audit trails
  - SLA guarantees

## Current Priorities

1. **Provider Abstraction** [BLOCKING] - Must complete before adding more providers
2. **Event Schema Versioning** - Prevent future migration issues  
3. **Project Management Layer** - Enable creative context preservation

**Execution**: Check boxes above as you complete each step. Each step = one working commit.

## Design Principles

- **Creative Chaos**: Support how creative minds actually work
- **Local-First**: User data sovereignty with optional cloud
- **Progressive Enhancement**: Each phase delivers working software
- **Event-Driven**: Loose coupling for organic evolution

## Implementation Guide

### Testing Each Step
```bash
# After each commit, verify:
alice --help                    # Still works
python -m pytest tests/unit/    # All tests pass
python scripts/event_monitor.py # Events flow correctly

# Provider testing:
alice --pipeline custom --stages "openai,anthropic" --dry-run
```

### When Context Resets
1. Check ROADMAP.md Phase 2 checkboxes
2. Run `git status` for uncommitted work
3. Check last CHANGELOG.md entry
4. Continue from next unchecked step

## How to Contribute

1. **Check Current Phase** - Focus on active phase items
2. **Review Events** - New features should publish/subscribe to events
3. **Follow Architecture** - Maintain separation of concerns
4. **Test Everything** - Comprehensive test coverage required

## Metrics for Success

- **Phase 1**: 100% of operations publish events
- **Phase 2**: AI can resume projects after 3+ months
- **Phase 3**: Frame-accurate beat synchronization
- **Phase 4**: <100ms inter-service communication
- **Phase 5**: 99.9% uptime for production deployments

## Getting Involved

- **Discord**: [Coming Soon]
- **Issues**: [GitHub Issues](https://github.com/yourusername/AliceMultiverse/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/AliceMultiverse/discussions)

---

**Note**: This roadmap is a living document. Priorities may shift based on user feedback and technical discoveries. The full technical specification is available in [todo/02 alice-multiverse-big-refactor-into-a-bigger-scope.md](todo/02%20alice-multiverse-big-refactor-into-a-bigger-scope.md).