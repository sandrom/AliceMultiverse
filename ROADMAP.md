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
   - No database server required ✓
3. **What would users pay for?** 
   - Creative workflow acceleration
   - AI-assisted curation from thousands to dozens
   - Intelligent prompt generation for video
   - Collaborative exploration with context
4. **What's broken RIGHT NOW?** 
   - Search functionality (needs DuckDB implementation)
   - Project management (no storage without PostgreSQL)
   - Missing similarity search
   - No soft-delete workflow

## Immediate: Restore Core Functionality (HIGHEST PRIORITY)

### DuckDB Search Implementation
- [ ] **Implement DuckDB search backend**
  - [ ] Create DuckDB metadata schema
  - [ ] Port search logic from PostgreSQL
  - [ ] Add indexing for fast tag searches
  - [ ] Test with 10k+ images
- [ ] **Restore search API functionality**
  - [ ] Update search_handler.py to use DuckDB
  - [ ] Implement faceted search
  - [ ] Add similarity search support
  - [ ] Performance benchmarks

### Project Management Without Database
- [ ] **File-based project storage**
  - [ ] Design project.yaml format
  - [ ] Implement file-based ProjectService
  - [ ] Store in .alice/projects/ directory
  - [ ] Add project migration tool

## Next Up: Creative Workflow Support

### Selection & Curation Tools
- [ ] **Selection Tracking** - Record which images user selected and why
  - [x] Test selection persistence and retrieval ✅
  - [x] Document feedback data structure ✅
  - [ ] Implement file-based storage
- [ ] **Similarity Search** - "Find more like these selected ones"
  - [ ] Implement with DuckDB vector support
  - [ ] Add perceptual hash comparison
  - [ ] Test with various image types
- [ ] **Soft Delete API** - Move rejected images to 'sorted-out' folder
  - [x] Test file movement and tracking ✅
  - [x] Document soft-delete workflow ✅
  - [ ] Implement move operations
- [ ] **Exclusion List** - Skip 'sorted-out' folders in scans
  - [x] Test exclusion logic thoroughly ✅
  - [x] Document folder structure conventions ✅
  - [ ] Add to scanner configuration

### Video Creation Workflow
- [ ] **Prompt Generation** - Create engaging Kling prompts from selected images
  - [ ] Study successful Kling prompts
  - [ ] Build prompt templates
  - [ ] Add motion suggestions
- [ ] **Flux Kontext Integration** - Enable image editing/combination workflows
  - [ ] Implement Flux Kontext provider
  - [ ] Create keyframe workflows
  - [ ] Test multi-image combinations
  - [ ] Build transition templates

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
   - Create keyframes from selected images
   - Add/remove objects between frames
   - Generate variations for transitions
   - Export storyboard for Kling

## Backlog (Re-evaluate Weekly)

### Performance & Scale
- [ ] **DuckDB Performance Optimization**
  - [ ] Benchmark vs PostgreSQL baseline
  - [ ] Optimize for 100k+ image collections
  - [ ] Add query result caching
  - [ ] Document performance tips

### Cloud Integration
- [ ] **S3/GCS Direct Querying**
  - [ ] DuckDB cloud storage support
  - [ ] Metadata extraction from cloud
  - [ ] Cost-aware scanning strategies
  - [ ] Hybrid local/cloud search

### Developer Experience
- [ ] **Improved Error Messages**
  - [ ] Add suggestions for common issues
  - [ ] Better file path debugging
  - [ ] Clear API error responses
  - [ ] Migration guides

## Completed ✅

### Recent Achievements
- [x] **PostgreSQL Removal** - Simplified deployment (3,318 lines removed)
- [x] **Critical Bug Fixes** - Recursion, imports, deprecations all resolved
- [x] **Understanding System** - Multi-provider image analysis working
- [x] **Test Coverage** - 31 new tests for understanding system
- [x] **Documentation Alignment** - All docs updated for current features
- [x] **Code Cleanup** - Removed deprecated quality assessment system

### Architecture Decisions
- [x] ADR-007: Quality → Understanding System
- [x] ADR-008: DuckDB for Metadata Search  
- [x] ADR-009: File-First Metadata Architecture
- [x] ADR-010: Remove PostgreSQL Integration

### Provider Ecosystem (15+ Integrations)
- **Image Generation**: Midjourney, DALL-E, Stable Diffusion, Firefly, Leonardo, Ideogram
- **Video Generation**: Kling, Hedra, Google Veo 2
- **Image Enhancement**: Magnific, Flux Kontext
- **Audio**: ElevenLabs sound effects, mmaudio
- **Understanding**: Claude, GPT-4V, Gemini, DeepSeek

### Core Infrastructure
- **Event System**: Redis Streams with consumer groups
- **Metadata**: Embedded in files for portability
- **Caching**: Unified cache with Redis backend
- **Storage**: Multi-location registry with content addressing
- **Search**: DuckDB for OLAP queries (implementation pending)

## Design Principles

1. **Working Service First**: Never break existing functionality
2. **Files as Truth**: All data lives in files, databases are just caches
3. **Simple Architecture**: Fewer moving parts = fewer problems
4. **User Workflows**: Design for complete workflows, not features
5. **Cost Awareness**: Track and optimize AI spending
6. **Clean as You Go**: Remove old code when adding new
7. **Test Everything**: No feature without comprehensive tests
8. **Document First**: Write docs before implementation

## Development Guidelines

### Before Starting Any Task
1. Ask: "Is this solving a real user problem?"
2. Ask: "Will this make the system simpler or more complex?"
3. Ask: "Can we test this thoroughly?"
4. Ask: "Will users understand how to use this?"

### Implementation Checklist
- [ ] Write tests first (TDD)
- [ ] Update documentation
- [ ] Clean up old code
- [ ] Run full test suite
- [ ] Update CHANGELOG.md
- [ ] Consider writing an ADR

### Testing Requirements
```bash
# Before ANY commit:
pytest tests/unit/test_new_feature.py -v        # Unit tests
pytest tests/integration/ -v                    # Integration tests  
pytest --cov=alicemultiverse --cov-report=html # Coverage
alice --dry-run                                 # CLI smoke test
```

---

**Note**: This roadmap follows kanban principles. We work on the highest value task that solves real problems, learn from implementation, and continuously re-evaluate priorities.