# AliceMultiverse Roadmap

## Vision

AliceMultiverse is an AI-native service that operates exclusively through AI assistants. It bridges creative professionals with AI generation tools and APIs, excelling at detecting, organizing, and assessing AI-generated content while maintaining context across extended creative sessions.

## Critical Questions (Re-evaluate Daily)

1. **Are we solving real problems?** Media organization ✓, Quality assessment ✓, Generation tracking ✓
2. **Is the architecture still simple?** 4,100 lines removed ✓, PostgreSQL-only ✓, One provider base ✓
3. **What would users pay for?** Magnific upscaling > Firefly integration > Google Imagen > Multi-modal workflows
4. **What's broken RIGHT NOW?** Nothing critical - all tests passing, providers working

## Next Up (Priority Order)

### 1. High-Value Provider Integrations (User Requested)

#### Magnific/Freepik API (Highest Priority - You use this a lot!) ✅
- [x] Implement Freepik API provider (exposes Magnific upscaler)
- [x] Add Mystic image model support through Freepik
- [x] Test with your typical upscaling workflows
- [x] Document pricing and rate limits

#### Adobe Firefly API ✅
- [x] Implement Firefly provider for generative fill/expand
- [x] Add support for all Firefly v3 capabilities
- [x] Integrate style and structure reference features
- [x] Support for async job polling and all endpoints

#### Google AI APIs (Veo & Imagen) ✅
- [x] Add Google AI provider base class with dual backend support
- [x] Implement Imagen 3 for high-quality image generation
- [x] Add Veo 2 for video generation (8-second clips)
- [x] Support for both Gemini API and Vertex AI backends

### 2. Additional Creative Providers

#### Ideogram API
- [ ] Implement Ideogram provider for text rendering
- [ ] Add support for typography-focused generation
- [ ] Enable logo and design-oriented features

#### Leonardo.ai API  
- [ ] Implement Leonardo provider with all models
- [ ] Add support for custom trained models
- [ ] Enable real-time canvas features
- [ ] Integrate Elements system for style control

### 3. Multi-Modal Workflow Support
- [ ] Create workflow templates for common tasks
- [ ] Image → Upscale → Variation pipeline
- [ ] Video → Audio → Enhancement pipeline
- [ ] Support for provider chaining (output → input)
- [ ] Cost optimization across provider selection

## Backlog (Re-evaluate Weekly)

### Midjourney Integration (Complex but High Value)
- Research proxy API options (no official API)
- Implement Discord bridge or third-party API
- Handle asynchronous generation pattern
- Parse and extract seed/parameters

### Performance & Scale
- Implement vector search for semantic similarity
- Add Elasticsearch for prompt/description search
- Create provider-specific caching strategies
- Optimize for batch operations

### Enhanced Quality Assessment
- Integrate aesthetic scoring models
- Add composition analysis
- Implement style consistency checks
- Create quality profiles per use case

### Workflow Engine (When patterns emerge)
- Define workflow format based on actual usage
- Start with simple sequential execution
- Add conditional logic based on quality
- Enable cost/quality optimization

## Recently Completed ✅

### Google AI (Imagen & Veo) Integration (Jan 2025)
- Implemented complete Google AI provider with Imagen 3 and Veo 2 support
- Dual backend architecture supporting both Gemini API and Vertex AI
- Text-to-image generation with Imagen 3 ($0.03/image)
- Text-to-video and image-to-video with Veo 2 (8-second clips)
- Support for all aspect ratios, negative prompts, and batch generation
- Comprehensive tests achieving 100% pass rate (20/20)
- Full documentation with examples for both backends

### Adobe Firefly API Integration (Jan 2025)
- Implemented complete Adobe Firefly v3 provider with all capabilities
- Supports text-to-image, generative fill, expand, composite, and similar
- Added authentication with Adobe IMS token management
- Implemented async job polling for long-running operations
- Created comprehensive tests achieving 100% pass rate
- Added style presets, structure reference, and advanced features
- Documented all capabilities with usage examples

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

### Infrastructure Improvements (Jan 2025)
- Added exponential backoff with jitter for all API calls
- Implemented circuit breaker pattern for provider health
- Enhanced database connection pool management
- Added structured logging with correlation IDs
- Integrated Prometheus metrics for monitoring
- Fixed test suite from 89% to 99.7% pass rate

## Design Principles

1. **Working Service First**: Never break existing functionality
2. **User Value Focus**: Prioritize features users actually request and use
3. **Provider Diversity**: Support the tools creatives actually use
4. **Cost Awareness**: Always track and optimize generation costs
5. **Simple Integration**: Each provider should work standalone

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

### Priority Changes

Based on instructions.md and your feedback:
- **Magnific/Freepik** jumps to #1 (you use it a lot)
- **Adobe Firefly** is #2 (makes sense for creatives)
- **Google AI** is #3 (cutting edge capabilities)
- Dropped workflow engine priority (no evidence of need yet)
- Added specific features you'd use for each provider

## Questions for You

1. **Magnific Usage**: What resolution/quality settings do you typically use?
2. **Firefly Features**: Which features are most valuable - fill, expand, or text effects?
3. **Workflow Patterns**: What's your typical pipeline? Generate → Upscale → Edit?
4. **Cost Sensitivity**: What's acceptable cost per operation for these tools?

---

**Note**: This roadmap follows kanban principles. We work on the highest value task that you'll actually use, learn from implementation, and continuously re-evaluate priorities.

## Archive - Previously Completed (2024)

<details>
<summary>Click to expand completed work from 2024</summary>

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
- Achieved 89% → 99.7% test pass rate

### Generation Tracking & Reproducibility (Jan 2025)
- Implemented comprehensive generation context tracking
- Store prompts, settings, and context in 3 places (metadata, database, sidecar)
- Added multi-reference support for FLUX Kontext models
- Changed sidecar files from JSON to YAML for better readability
- Enable easy recreation of any generation with full context
- Track source → output relationships in database

### Provider Model Updates (Jan 2025)
- Added Kling 2.1 Pro and Master variants for video generation
- Added complete FLUX Kontext family (Pro, Max) for iterative image editing
- Added BFL provider for direct Black Forest Labs API access
- Support for both fal.ai and bfl.ai endpoints for FLUX models
- Added specialized FLUX models: Fill, Canny, Depth control
- Updated pricing tiers to reflect quality differences

</details>