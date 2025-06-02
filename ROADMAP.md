# AliceMultiverse Roadmap

## Vision

AliceMultiverse is an AI-native creative workflow orchestrator that enables collaborative exploration between humans and AI. It excels at understanding large image collections, facilitating creative discovery, and supporting multiple video creation workflows - from storyboard-driven to emergent visual narratives. The system maintains context across extended creative sessions, helping users navigate from thousands of possibilities to polished video stories.

## Critical Questions (Re-evaluate Daily)

1. **Are we solving real problems?** 
   - Media organization ✓
   - Collaborative image discovery ✓ (semantic tags working!)
   - Video creation workflows ✓
   - Large collection navigation ✓ (semantic search via DuckDB)
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
   - Redis connection errors need better documentation
   - API keys must be configured for understanding to work

## Immediate: Restore Core Functionality (HIGHEST PRIORITY)

### Fix Hardcoded Storage Paths ✅ COMPLETED
- [x] **Update hardcoded paths to use configuration**
  - [x] Fix FileProjectService to use `config.storage.project_paths` instead of "test_data/projects"
  - [x] Fix SearchHandler to use `config.storage.search_db` instead of "test_data/search.duckdb"
  - [x] Update comparison system to use configured paths
  - [x] Update web server image serving to use configured paths
  - [x] Test all path configurations work correctly
  - [x] Created test_path_configuration.py to verify no hardcoded paths remain

### DuckDB Search Implementation ✅
- [x] **Implement DuckDB search backend**
  - [x] Create DuckDB metadata schema with assets and tags tables
  - [x] Port search logic from PostgreSQL
  - [x] Add indexing for fast tag searches
- [x] **Restore search API functionality**
  - [x] Update search_handler.py to use DuckDB
  - [x] Implement faceted search (tags, sources, media types)
  - [ ] Add similarity search support (needs perceptual hashing)

### Project Management Without Database ✅
- [x] **File-based project storage**
  - [x] Design project.yaml format for metadata and context
  - [x] Implement FileProjectService with full functionality
  - [x] Support project folder structure:
    ```
    project-name/
    ├── project.yaml         # Metadata, budget, context
    ├── .alice/              # Alice-specific data
    │   ├── selections.json  # Asset selections with reasons
    │   └── sessions/        # Conversation history
    ├── created/             # Assets created for this project
    │   └── 2024-01-15/      # Organized by date/source
    ├── selected/            # Assets copied from global library
    ├── rounds/              # Selection rounds for curation
    │   ├── round-1/
    │   └── final/
    └── exports/             # Final deliverables
    ```
  - [x] Registry stored in first configured storage path
  - [x] Find project from current directory
  - [x] Budget tracking with cost breakdown by provider

### Search Index Population
- [ ] **Populate search index from existing files**
  - [x] Create SearchIndexBuilder class
  - [x] Create rebuild_search_index.py script
  - [x] Add index rebuilding to alice CLI (`alice index rebuild/update/verify/stats`)
  - [ ] Fix metadata extraction to work with current metadata format
    - Current cache (v3.0) contains quality assessment data, not semantic tags
    - Options:
      1. Update UnifiedCache to run understanding system during organization
      2. Run understanding as part of index building (expensive)
      3. Create migration script to add tags to existing cache
    - Recommendation: Option 1 - integrate understanding with organization flow
  - [ ] Auto-index new files during organization
  - [ ] Background indexing for watch mode

### Configuration Updates ✅
- [x] **Storage configuration exists in settings.yaml**
  - [x] StorageConfig dataclass implemented
  - [x] search_db, project_paths, asset_paths configured
- [x] **Fix code to use configuration**
  - [x] All hardcoded test_data/ paths removed
  - [x] Services now use configuration values

## Next Up: Fix Understanding Integration ✅

### Understanding System Integration  
- [x] **Connect understanding to caching system**
  - [x] Update UnifiedCache to store understanding results
  - [x] Ensure tags are embedded in image metadata
  - [x] Update cache format to v4.0 with understanding data
  - [x] Test tag extraction and storage
- [x] **Enable understanding by default**
  - [x] Change processing.understanding default to true
  - [x] Document cost implications in settings.yaml
  - [x] Provider selection configurable

## Completed Today (January 6, 2025)

### Understanding System Fixed ✅
- [x] **API Key Loading** - Keys now loaded from keychain automatically
- [x] **Understanding Integration** - AI analysis runs during organization
- [x] **Semantic Tags Generated** - Rich tags in multiple categories (style, mood, subject, etc.)
- [x] **Metadata Embedding** - Tags embedded in image files (PNG, JPEG, WebP, HEIC)
- [x] **JSON Serialization** - Fixed enum serialization issues
- [x] **Cache Format v4.0** - New format stores understanding results

### Search & Organization Improvements
- [x] **Auto-indexing** - Files indexed automatically during organization
- [x] **Exclusion Lists** - Scanner skips 'sorted-out' folders
- [x] **Similarity Search** - Perceptual hashing fully integrated! ✅
  - [x] pHash (DCT-based) for robust similarity
  - [x] dHash (difference hash) for fast comparison
  - [x] aHash (average hash) for simple matching
  - [x] Hamming distance calculation
  - [x] DuckDB storage and search methods
  - [x] Automatic computation during organization

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
- [x] **Soft Delete API** - Move rejected images to 'sorted-out' folder ✅
  - [x] Test file movement and tracking ✅
  - [x] Document soft-delete workflow ✅
  - [x] Implement SoftDeleteManager class ✅
  - [x] Add soft_delete_assets to structured interface ✅
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

### Project-Based Asset Management

**Philosophy**: Assets created within a project stay in the project by default. Move to global library only when reuse is identified.

**Workflow**:
1. **Create in Project** - New generations go to `project/created/`
2. **Select from Library** - Copy existing assets to `project/selected/`
3. **Curate in Rounds** - Mix created & selected in `project/rounds/`
4. **Export Final** - Deliverables in `project/exports/`
5. **Promote to Global** - Move gems to global library when reuse identified

**Benefits**:
- Projects are self-contained archives
- Clear context for project-specific generations  
- Easy to share complete projects
- Flexible organization per project needs
- No pollution of global library with one-off assets

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

## Current State (January 6, 2025)

### What's Working ✅
1. **Path Configuration**: All paths configurable, no hardcoded test_data/
2. **Understanding Integration**: AI analysis runs automatically during organization
3. **Semantic Tags**: Rich tags generated in 11+ categories (style, mood, subject, color, etc.)
4. **Perceptual Hashing**: All three hash types computed and stored during organization
5. **Search Foundation**: DuckDB stores tags, metadata, and perceptual hashes
6. **Cache v4.0**: New format stores understanding results with semantic tags
7. **Metadata Embedding**: Tags embedded directly in image files for portability
8. **Similarity Search**: Can find similar images using perceptual hash comparison

### What Needs Work ⚠️  
1. **Search UI**: Need interface to actually search by tags (API exists)
2. **Redis Documentation**: Required dependency but errors are confusing
3. **API Key Setup**: Must run `alice keys setup` before understanding works

### Architecture Summary
- **Quality System**: Removed (was subjective and expensive)
- **Understanding System**: Integrated and working (objective content description)
- **Search System**: Working with semantic tags from understanding
- **Cache System**: UnifiedCache v4.0 with understanding support

## Design Principles

1. **Working Service First**: Never break existing functionality
2. **Files as Truth**: All data lives in files, databases are just caches
3. **Simple Architecture**: Fewer moving parts = fewer problems
4. **User Workflows**: Design for complete workflows, not features
5. **Cost Awareness**: Track and optimize AI spending
6. **Clean as You Go**: Remove old code when adding new
7. **Test Everything**: No feature without comprehensive tests
8. **Document First**: Write docs before implementation

## Migration Path (January 2025)

### Phase 1: Fix Critical Paths ✅ COMPLETED (January 6, 2025)
1. ✓ Updated all hardcoded test_data/ references
2. ✓ Tested with configurable directories
3. ✓ Created path configuration test suite

### Phase 2: Understanding Integration ✅ COMPLETED (January 6, 2025)
1. ✓ Updated UnifiedCache to run understanding when enabled
2. ✓ Tags stored in cache v4.0 format
3. ✓ Index builder extracts tags from new format
4. ✓ DuckDB search works with semantic tags

### Phase 3: Legacy Support ❌ SKIPPED
- No users yet, no need for migration
- Fresh start with v4.0 cache format
- Old quality assessment already removed

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