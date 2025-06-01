# AliceMultiverse Roadmap

## Vision

AliceMultiverse is an AI-native creative workflow orchestrator that enables collaborative exploration between humans and AI. It excels at understanding large image collections, facilitating creative discovery, and supporting multiple video creation workflows - from storyboard-driven to emergent visual narratives. The system maintains context across extended creative sessions, helping users navigate from thousands of possibilities to polished video stories.

## Critical Questions (Re-evaluate Daily)

1. **Are we solving real problems?** 
   - Media organization ✓
   - Collaborative image discovery ✓ 
   - Video creation workflows ✓
   - Large collection navigation ✓
2. **Is the architecture still simple?** 
   - Understanding over quality ✓
   - File-first metadata ✓
   - AI-native interface ✓
3. **What would users pay for?** 
   - Creative workflow acceleration
   - AI-assisted curation from thousands to dozens
   - Intelligent prompt generation for video
   - Collaborative exploration with context
4. **What's broken RIGHT NOW?** 
   - Recursion bug in metadata loading
   - Need image presentation in chat UI
   - Missing similarity search
   - No soft-delete workflow

## ✅ CRITICAL: Code Cleanup COMPLETED

**Status:** Service is now stable and ready for continued development.
Following instructions.md: "a working service/application has always priority over features"

### Immediate (This Session - BLOCKING)
- [x] **Fix broken imports** - Removed obsolete quality test files, updated remaining to understanding system
- [x] **Implement missing create_pipeline_stages()** function with dynamic import system
- [x] **Commit or revert** 21 uncommitted files - New features committed, critical fixes committed
- [x] **Fix test suite** - Core imports work, service foundation stable

### IMMEDIATE: Fix Critical Issues (HIGHEST PRIORITY)
- [x] **Fix Image Presentation API test failures** - All 18 tests now passing
- [x] **Fix recursion bug** - Fixed circular dependency in pipeline_organizer.py
- [x] **Fix PYTHONPATH requirement** - Created cli_entry.py wrapper for proper imports
- [x] **Fix deprecation warnings** - MetadataCache, SQLAlchemy, AsyncIO warnings
  - [x] Update SQLAlchemy declarative_base import
  - [x] Fix AsyncIO get_event_loop() deprecations
  - [x] Suppress MetadataCache warning in UnifiedCache
  - [x] Document migration path in docs/developer/deprecation-guide.md
- [ ] **Complete test coverage** for new modules
  - [ ] comparison/ module - test Elo system and web UI
  - [ ] understanding/ module - test all providers
  - [ ] storage/ module - test location registry
  - [ ] Document test requirements for each module
- [x] **Add integration tests** for new understanding system
  - [x] Test multi-provider analysis - 3 tests covering single, multi, and failure scenarios
  - [x] Test metadata embedding - 3 tests for embed/extract, persistence, and cache integration
  - [x] Test tag search functionality - 2 tests for basic search and exclusion filtering
  - [x] Document test scenarios - Created README_UNDERSTANDING_TESTS.md

### Additional Issues
- [x] **Write ADRs** for major architectural changes ✅ DONE
  - ADR-007: Quality → Understanding System
  - ADR-008: DuckDB for Metadata Search
  - ADR-009: File-First Metadata Architecture
- [x] **Update documentation** - CLAUDE.md still references removed quality features ✅ UPDATED
- [x] **Fix deprecation warnings** - MetadataCache, SQLAlchemy, AsyncIO warnings
  - [x] Update SQLAlchemy declarative_base import
  - [x] Fix AsyncIO get_event_loop() deprecations
  - [x] Suppress MetadataCache warning in UnifiedCache
  - [x] Document migration path in docs/developer/deprecation-guide.md
- [x] **Add integration tests** for new understanding system
  - [x] Test multi-provider analysis - 3 tests covering single, multi, and failure scenarios
  - [x] Test metadata embedding - 3 tests for embed/extract, persistence, and cache integration
  - [x] Test tag search functionality - 2 tests for basic search and exclusion filtering
  - [x] Document test scenarios - Created README_UNDERSTANDING_TESTS.md

### Important (This Week - MEDIUM PRIORITY)
- [ ] **Complete test coverage** for new modules
  - [ ] comparison/ module - test Elo system and web UI
  - [ ] understanding/ module - test all providers
  - [ ] storage/ module - test location registry
  - [ ] Document test requirements for each module
- [ ] **Clean up temporary files and old code**
  - [ ] Remove research docs that are outdated
  - [ ] Fix services/asset-processor structure
  - [ ] Delete deprecated quality assessment code
  - [ ] Archive old experiments properly
- [x] **Align all documentation**
  - [x] Update README.md with current features - Replaced quality with understanding
  - [x] Update QUICKSTART.md - Removed quality assessment references
  - [x] Update storage-location-registry.md - Changed quality_stars to tags
  - [x] Remove references to deprecated features - BRISQUE, pipeline, quality ratings
- [ ] **Performance testing** of DuckDB integration
  - [ ] Benchmark search operations
  - [ ] Test with large datasets (10k+ images)
  - [ ] Document performance characteristics
  - [ ] Compare with old PostgreSQL performance

## Next Up: Creative Workflow Support

- [x] **Image Presentation API** - Return images to AI for display in chat ✅
  - [x] Write comprehensive tests for image retrieval ✅
  - [x] Document API endpoints and response formats ✅
  - [x] Implement core functionality ✅
  - [x] Run tests - 9/18 passing, 9 need fixes ✅
  - [x] Integrate with MCP server ✅
- [ ] **Selection Tracking** - Record which images user selected and why
  - [x] Test selection persistence and retrieval ✅
  - [x] Document feedback data structure ✅
  - [ ] Remove deprecated tracking code
- [ ] **Similarity Search** - "Find more like these selected ones"
  - [ ] Implement with full test coverage
  - [ ] Document similarity algorithms used
  - [ ] Clean up old search implementations
- [ ] **Soft Delete API** - Move rejected images to 'sorted-out' folder
  - [x] Test file movement and tracking ✅
  - [x] Document soft-delete workflow ✅
  - [ ] Clean up hard-delete code
- [ ] **Exclusion List** - Skip 'sorted-out' folders in scans
  - [x] Test exclusion logic thoroughly ✅
  - [x] Document folder structure conventions ✅
  - [ ] Remove old filtering code
- [ ] **Prompt Generation** - Create engaging Kling prompts from selected images
  - [ ] Test prompt quality and variety
  - [ ] Document prompt templates and strategies
  - [ ] Clean up old prompt generation attempts
- [ ] **Flux Kontext Integration** - Enable image editing/combination workflows
  - [ ] Implement Flux Kontext provider for image editing
  - [ ] Create keyframe generation workflow
  - [ ] Test multi-image combination capabilities
  - [ ] Document editing strategies for video sequences
  - [ ] Build templates for common transitions (zoom, pan, object addition)
  - [ ] Integrate with selection tracking for workflow continuity
  
### Implementation Plan for Image Discovery Workflow

**User Story**: "I have thousands of images and need to find a small set for video creation"

1. **Initial Browse**
   - AI shows grid of images based on initial query
   - User clicks to select/deselect with reasons
   - AI learns preferences in real-time

2. **Iterative Refinement**
   - "Show me more cyberpunk but less neon"
   - "These three work well together, find complementary ones"
   - "This style but different subjects"

3. **Curation Tools**
   - Mark broken/unwanted → moves to 'sorted-out/broken/'
   - Mark maybe-later → moves to 'sorted-out/archive/'
   - These folders excluded from future searches

4. **Video Preparation with Flux Kontext**
   - **Keyframe Creation**: Use Flux Kontext to edit/reframe selected images
     - Describe changes to existing images (zoom, pan, add objects)
     - Combine multiple images into cohesive keyframes
     - Create variations for smooth transitions
   - **Multi-frame Workflows**:
     - Generate initial frames from any source (Midjourney, DALL-E, etc.)
     - Use Flux Kontext to create intermediate keyframes
     - Export keyframe sequence for Kling video generation
   - **Advanced Editing**:
     - Add/remove objects between frames
     - Adjust composition for video flow
     - Maintain style consistency across edits
   - **Kling Frames Integration**:
     - Generate prompts optimized for Kling Frames
     - Support optional start/end keyframes
     - Suggest motion types based on keyframe differences
     - Export complete storyboard with frame sequences

### Technical Requirements

1. **Search API Enhancements**
   ```python
   # Current: Simple tag search
   search(tags=["cyberpunk"])
   
   # Needed: Similarity and exclusion
   search(
       similar_to=["image_hash_1", "image_hash_2"],
       exclude_tags=["neon"],
       exclude_folders=["sorted-out/"],
       limit=20
   )
   ```

2. **Selection Tracking**
   ```python
   # Store user feedback
   track_selection({
       "image_hash": "abc123",
       "selected": True,
       "reason": "love the mood and color palette",
       "session_id": "exploration_001"
   })
   ```

3. **Soft Delete API**
   ```python
   # Move to sorted folder
   soft_delete({
       "image_hash": "def456",
       "reason": "broken/artifacts",
       "destination": "sorted-out/broken/"
   })
   ```



## Backlog (Re-evaluate Weekly)

### Search & Discovery
- Direct S3/GCS querying with DuckDB
- Cloud metadata integration (GCS/S3)
- Real-time search suggestions
- Faceted search interface

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
- **Midjourney**: All models (v4-v6.1, niji) via proxy APIs (UseAPI/GoAPI), parameter parsing

### Features
- **Multi-Modal Workflows**: Chain operations across providers with cost optimization
- **Image Understanding**: Multi-provider analysis with DeepSeek, OpenAI, Anthropic, Google
- **Flexible Storage**: Content-addressed tracking across multiple locations
- **Rich Tagging**: Semantic tags embedded in file metadata for portability
- **Search Performance**: 10-20x speedup with eager loading and Redis caching
- **Event System**: Redis Streams-based with consumer groups and retry logic
- **Provider Infrastructure**: Unified base class with health monitoring
- **DuckDB Search Cache**: OLAP-optimized metadata search with content addressing
- **ElevenLabs Sound Effects**: AI-generated sound effects with duration control
- **Midjourney Integration**: Full support via proxy APIs with parameter parsing
- **Multi-Location Storage**: Registry for tracking files across local/S3/GCS/network with rules engine
- **Model Comparison System**: Web-based blind A/B testing with Elo ratings and keyboard shortcuts
- **Advanced Image Understanding**: Hierarchical tagging, custom instructions, batch analysis, cost optimization

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
7. **Documentation First**: Every feature must be documented before release
8. **Test Coverage**: No feature without comprehensive tests
9. **Clean as You Go**: Remove old code when adding new
10. **User Workflows**: Design for complete creative workflows, not just features

## Implementation Guide

### Development Workflow for New Features

1. **Plan**
   - Write ADR if architectural change
   - Update roadmap with feature details
   - Design API with documentation first

2. **Implement**
   - Write tests FIRST (TDD approach)
   - Implement feature to pass tests
   - Clean up any old/deprecated code
   - Add comprehensive error handling

3. **Document**
   - Update relevant .md files
   - Add docstrings to all functions
   - Create usage examples
   - Update CHANGELOG.md

4. **Test**
   - Unit tests for all new code
   - Integration tests for workflows
   - Manual testing of user scenarios
   - Performance benchmarks if relevant

5. **Clean**
   - Remove commented-out code
   - Delete temporary test files
   - Archive old implementations
   - Update .gitignore if needed

### Adding New Providers

1. Check existing patterns in `alicemultiverse/providers/`
2. Inherit from `BaseProvider` 
3. Implement required methods: `generate()`, `estimate_cost()`, `get_generation_time()`
4. Add comprehensive tests (aim for 90%+ coverage)
5. Document API keys and setup
6. Add example usage
7. Clean up any similar old providers

### Testing Requirements

```bash
# Before ANY commit:
python -m pytest tests/unit/test_new_feature.py -v  # Unit tests
python -m pytest tests/integration/ -v              # Integration tests
python -m pytest --cov=alicemultiverse --cov-report=html  # Coverage
alice --dry-run  # Verify CLI still works

# Check for regressions:
python -m pytest tests/ -x  # Stop on first failure
```

### Documentation Standards

1. **Code Documentation**
   - Every public function needs a docstring
   - Complex logic needs inline comments
   - Type hints for all parameters

2. **User Documentation**
   - Update README.md for new features
   - Add to relevant docs/ sections
   - Include practical examples

3. **Developer Documentation**
   - Document architectural decisions
   - Explain non-obvious design choices
   - Add migration guides for breaking changes

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