# AliceMultiverse Roadmap

## Vision

AliceMultiverse is an AI-native service that operates exclusively through AI assistants. It bridges creative professionals with AI generation tools and APIs, excelling at detecting, organizing, and assessing AI-generated content while maintaining context across extended creative sessions.

## Critical Questions (Re-evaluate Daily)

1. **Are we solving real problems?** Media organization ✓, Quality assessment ✓, Generation tracking ✓
2. **Is the architecture still simple?** 4,100 lines removed ✓, PostgreSQL-only ✓, One provider base ✓
3. **What would users pay for?** Sound effects for videos > Multi-modal workflows > Enhanced quality assessment
4. **What's broken RIGHT NOW?** Nothing critical - all tests passing, providers working

## Next Up (Priority Order)

### 1. ElevenLabs Sound Effects (New Request!)
- [ ] Implement ElevenLabs provider for AI sound effects
- [ ] Support text-to-sound generation
- [ ] Add duration and format parameters
- [ ] Enable sound effects in video workflows
- [ ] Create audio-focused workflow templates

### 2. Midjourney Integration
- [ ] Research proxy API options (no official API)
- [ ] Implement Discord bridge or third-party API
- [ ] Handle asynchronous generation pattern
- [ ] Parse and extract seed/parameters

### 3. Enhanced Quality Assessment
- [ ] Integrate aesthetic scoring models
- [ ] Add composition analysis
- [ ] Implement style consistency checks
- [ ] Create quality profiles per use case

## Backlog (Re-evaluate Weekly)

### Performance & Scale
- Implement vector search for semantic similarity
- Add Elasticsearch for prompt/description search
- Create provider-specific caching strategies
- Optimize for batch operations

## Completed ✅

### Providers
- **Magnific/Freepik**: Upscaling with Magnific, Mystic image generation
- **Adobe Firefly**: Generative fill/expand, style reference, all v3 features
- **Google AI**: Imagen 3 ($0.03/image), Veo 2 video (8-second clips)
- **Ideogram**: Superior text rendering, V2/V2-Turbo/V3 models
- **Leonardo.ai**: Phoenix, Flux, PhotoReal, Alchemy, Elements system
- **Hedra**: Character-2 talking avatars from image + audio
- **fal.ai**: FLUX family, Kling video, mmaudio, specialized models

### Features
- **Multi-Modal Workflows**: Chain operations across providers with cost optimization
- **Search Performance**: 10-20x speedup with eager loading and Redis caching
- **Event System**: PostgreSQL-based with workflow events
- **Provider Infrastructure**: Unified base class with health monitoring

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

---

**Note**: This roadmap follows kanban principles. We work on the highest value task that you'll actually use, learn from implementation, and continuously re-evaluate priorities.