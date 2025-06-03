# AliceMultiverse Roadmap - Personal Development Plan

## Vision

AliceMultiverse is my personal creative workflow orchestrator that I access through natural conversation with Claude. Built for my specific needs: managing thousands of AI-generated images, finding specific content through semantic search, and preparing assets for video creation. This is a tool by me, for me - though others are welcome to fork and adapt it.

## Critical Questions (Re-evaluate Daily)

1. **Is this solving MY problems?** 
   - Finding specific images in my collection ✓
   - Natural language search through Claude ✓ 
   - Tracking creative decisions ✓
   - Managing API costs ✓ (cost warnings + CLI tools)
2. **Is the architecture still simple?** 
   - File-first approach ✓
   - AI-native interface ✓
   - DuckDB for search ✓
   - Redis optional ✓ (file-based events by default)
3. **What am I spending money on?** 
   - Understanding API calls tracked ✓
   - Cost warnings before operations ✓
   - Budget limits enforced ✓
   - `alice cost report` for visibility ✓
4. **What's broken RIGHT NOW?** 
   - Documentation implies this is a product (needs update) ✅ (fixed)
   - No --understand CLI flag (uses config only) ✅ (fixed)
   - First-run experience could be smoother ✅ (improved)
   - Repository needs cleanup (duplicate files, old code, media in git)

## 🧹 Repository Cleanup Plan (HIGH PRIORITY)

### Why This Matters
The repo has accumulated cruft during rapid development. A clean repo = easier maintenance, faster AI context loading, and clearer for anyone (including future me) to understand.

### Phase 1: Immediate Cleanup (Do First)
- [ ] **Fix .gitignore**
  - [ ] Add: `*.egg-info/`, `__pycache__/`, `.pytest_cache/`
  - [ ] Add: `inbox/`, `organized/`, `output/`, `training/` (except READMEs)
  - [ ] Add: `*.log`, `data/*.duckdb` (user-specific)
  - [ ] Remove tracked files that should be ignored
- [ ] **Remove media files from git**
  - [ ] Delete all images/videos in inbox/, organized/, output/, training/
  - [ ] Add placeholder READMEs explaining these directories
- [ ] **Commit current changes**
  - [ ] main_cli.py (--understand flag addition)
  - [ ] first_run.py (improved setup wizard)

### Phase 2: Code Cleanup
- [ ] **Remove deprecated interface files**
  - [ ] Verify alice_structured.py is the current API
  - [ ] Remove alice_interface.py, alice_interface_v2.py
  - [ ] Consolidate cli_handler.py and cli_handler_structured.py
- [ ] **Clean up migration files**
  - [ ] Remove PostgreSQL event migration code
  - [ ] Move completed migrations to legacy/ folder
  - [ ] Update docs to reflect current architecture
- [ ] **Consolidate storage modules**
  - [ ] Review overlapping functionality in storage modules
  - [ ] Merge or remove redundant code
  - [ ] Update imports and tests

### Phase 3: Documentation Cleanup
- [ ] **Consolidate settings examples**
  - [ ] Merge settings.yaml.example and settings.yaml.multipath.example
  - [ ] Create one comprehensive example with all options
- [ ] **Remove temporary docs**
  - [ ] Integrate README_STORAGE.md into main docs
  - [ ] Complete and remove REDIS_REMOVAL_PLAN.md
  - [ ] Update all Redis references to show it's optional
- [ ] **Update stale documentation**
  - [ ] Remove references to deprecated features
  - [ ] Ensure all examples use current API

### Phase 4: Final Polish
- [ ] **Clean test/temporary files**
  - [ ] Remove MagicMock directory
  - [ ] Clean up one-time maintenance scripts
  - [ ] Archive or remove old test data
- [ ] **Verify everything works**
  - [ ] Run full test suite
  - [ ] Test fresh install experience
  - [ ] Update CHANGELOG.md with cleanup notes

### Success Criteria
- Repository size reduced by >50% (removing media files)
- No duplicate or deprecated code
- Clear, consistent structure
- All tests pass
- Fresh clone + install works perfectly

## Completed: Multi-Path Storage ✅

### Multi-Path Storage: Core Features
- [x] **Fix DuckDB Compatibility** - Aligned queries with schema
- [x] **File Operations** - Implemented copy/move between locations
- [x] **Foreign Key Constraints** - Fixed update issues in tests

### Multi-Path Storage: Advanced Features
- [x] **Progress Tracking** - Add progress bars for large file operations ✅
- [x] **Cloud Storage** - Add S3/GCS scanner implementations ✅
  - [x] S3 scanner with upload/download support
  - [x] GCS scanner with upload/download support
  - [x] Integrated with MultiPathScanner
  - [x] Example configuration for cloud storage
- [x] **Auto-Migration** - Rule-based file movement system ✅
  - [x] AutoMigrationService for analyzing files based on rules
  - [x] Execute migrations (copy or move files)
  - [x] MigrationScheduler for periodic runs
  - [x] CLI command `alice storage migrate`
  - [x] Dry-run support for previewing migrations
- [x] **Sync Tracking** - Handle conflicts and versioning ✅
  - [x] SyncTracker for detecting sync status and conflicts
  - [x] Multiple conflict resolution strategies (newest, largest, primary wins)
  - [x] Sync queue for batch processing
  - [x] VersionTracker for maintaining file history
  - [x] CLI commands: `sync-status`, `resolve-conflict`, `sync-process`

## Next Up: Video Creation Workflow

### Video Creation Workflow (IN PROGRESS ⚡)
- [x] **Prompt Generation** - Create engaging Kling prompts from selected images ✅
  - [x] Study successful Kling prompts (analyzed existing provider)
  - [x] Build prompt templates (5 styles: cinematic, documentary, etc.)
  - [x] Add motion suggestions (11 camera motion types)
- [x] **Flux Kontext Integration** - Enable image editing/combination workflows ✅
  - [x] Implement Flux Kontext provider (already exists in fal_provider)
  - [x] Create keyframe workflows (prepare_flux_keyframes)
  - [x] Test multi-image combinations (flux-kontext-multi support)
  - [x] Build transition templates (morph, dissolve, fade)
- [x] **MCP Tools Added** ✅
  - [x] analyze_for_video - Analyze images for video potential
  - [x] generate_video_storyboard - Create complete storyboards
  - [x] create_kling_prompts - Format prompts for Kling
  - [x] prepare_flux_keyframes - Enhanced keyframes with Flux
  - [x] create_transition_guide - Video editing guides

## My Actual Workflow

**Real scenario**: "I generated 200 images yesterday, need 20 for a video"

1. **Search & Select** via Claude
   - "Show me cyberpunk portraits from this week"
   - "Find more like these three"
   - "Exclude anything with neon"

2. **Curate & Clean**
   - Mark rejects → 'sorted-out/rejected/'
   - Mark maybe-later → 'sorted-out/archive/'
   - Track selections with reasons

3. **Prepare for Video**
   - Generate storyboard from selections
   - Create Kling prompts with camera movements
   - Use Flux Kontext for keyframe variations

4. **Project Organization**
   ```
   project-name/
   ├── created/     # New generations
   ├── selected/    # From global library
   ├── rounds/      # Curation iterations
   └── exports/     # Final deliverables
   ```

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
- [x] **Improved Error Messages** ✅ (Partially Complete)
  - [x] Add suggestions for common issues
    - Created `error_handling.py` with context-aware suggestions
    - Handles API keys, file paths, permissions, dependencies, costs
  - [x] Better file path debugging
    - Shows exact paths and permission check commands
  - [x] Clear API error responses
    - Enhanced AuthenticationError with provider context
    - Wrapped errors show user-friendly messages
  - [ ] Migration guides (future enhancement)

## Recent Achievements (January 2025)

### This Week's Completions ✅
1. **Multi-Path Storage Architecture** - Store assets across multiple locations with rules
2. **Video Creation Workflow** - Complete system for turning images into videos
3. **Selection & Curation Tools** - Track selections, find similar, soft delete
4. **Cost Management** - Track spending, free tier limits, budget alerts
5. **First-Run Experience** - Interactive setup wizard, better error messages
6. **Understanding Integration** - AI analysis with semantic tags
7. **Auto-Indexing** - Files indexed during organization
8. **Similarity Search** - Perceptual hashing (pHash, dHash, aHash)

### Today's Completions (January 6) ✅
1. **Redis Removal** - Made Redis optional, file-based events by default
2. **Cost Warnings** - Shows cost estimate before expensive operations
3. **Cost CLI Commands** - `alice cost report/set-budget/providers`
4. **Event Monitor Fixed** - Works with both Redis and file backends

### Architecture Improvements
- File-based event system (Redis now optional)
- DuckDB for search (PostgreSQL removed)
- Configuration-driven paths (no hardcoded test_data/)
- File-first metadata with content addressing
- Cost tracking integrated throughout

## Current State (January 6, 2025)

### What's Working ✅
- **AI-Native Interface**: Search and organize through Claude/ChatGPT
- **Semantic Search**: Tags, similarity, and natural language queries
- **Multi-Path Storage**: Assets across multiple locations with rules
- **Cost Tracking**: Know exactly what you're spending
- **Project Management**: File-based with budget tracking
- **Video Workflows**: Storyboards, Kling prompts, Flux keyframes

### Known Issues ⚠️
1. **Documentation Confusion**: Still implies this is a product (it's not)
2. **Performance at Scale**: Not tested with 100k+ images yet
3. **Understanding Flag**: No --understand CLI flag (uses config only)

## My Development Principles

1. **It has to work**: I use this daily, can't break it
2. **My money matters**: Track every API call
3. **Simplicity**: I maintain this alone
4. **Natural workflow**: Talk to Claude, not click UIs
5. **File-based**: I want portable data
6. **Test what matters**: Core workflows must work
7. **Document for future me**: I forget things


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