# AliceMultiverse Roadmap - Personal Creative Tool

## Vision

My personal AI creative workflow orchestrator, accessed through Claude. Built for managing thousands of AI-generated images, semantic search, and video creation. Not a product - a personal tool that solves my specific problems.

## Daily Reality Check

1. **What's broken TODAY?** Fix it first
2. **What costs money?** Track and optimize it
3. **What's complex?** Simplify it
4. **What's unused?** Remove it

## Current State (June 2025)

### ✅ What's Working
- **AI-Native Interface**: Search and organize through Claude MCP
- **Semantic Search**: Find images by content, style, mood
- **Multi-Path Storage**: Assets across multiple locations with rules
- **Cost Tracking**: Know exactly what I'm spending
- **Video Workflows**: Storyboards, Kling prompts, Flux keyframes
- **File-Based Everything**: No database servers required

### ⚠️ Active Pain Points
1. **Code Cleanup Needed**: Multiple deprecated interface files
2. **Documentation Confusion**: Still reads like a product in places
3. **Daily Workflow Friction**: Small annoyances that add up

## Immediate Priorities

### 1. Code Cleanup Sprint 🧹
**Why**: Clean code = easier maintenance = less frustration

- [x] Remove deprecated interface files
  - [x] Confirm alice_structured.py is current
  - [x] Delete alice_interface_v2.py (incomplete, unused)
  - [x] Keep alice_interface.py (still needed by MCP server)
- [x] Remove completed migration code
  - [x] Removed redis_event_migration.py example
  - [ ] Remove PostgreSQL migration files (if any remain)
- [ ] Consolidate duplicate functionality
  - [x] Identified overlapping storage modules:
    - DuckDBSearchCache (primary, used by MCP server)
    - DuckDBSearch (legacy/specialized, used by search handler)
  - [ ] Keep both CLI handlers (legacy + structured) for now

### Future Cleanup (Lower Priority)
- [x] Analyze DuckDB merge strategy (significant work, postponed)
- [x] Clean up PostgreSQL references in comments  
- [x] Document deprecated cache modules for v3.0 removal
  - Created v3-cleanup-plan.md with removal checklist
- [ ] Actually merge DuckDB implementations (major task)
- [ ] Consolidate storage modules further

### 2. Workflow Polish ✨
**Why**: Daily friction adds up

- [x] Check Claude MCP issues (no known issues, good docs)
- [x] Streamline project creation flow
  - [x] Added `create_project` MCP tool
  - [x] Added `list_projects` MCP tool
  - [x] Added `get_project_context` MCP tool
  - [x] Added `update_project_context` MCP tool
- [x] Better duplicate detection
  - [x] Added `find_duplicates` MCP tool for exact duplicates
  - [x] Shows wasted space and duplicate groups
  - [ ] TODO: Add perceptual hash similarity comparison
- [x] Quick selection workflow (mark favorites faster)
  - [x] Added `quick_mark` tool for instant favorites/hero/maybe marking
  - [x] Added `list_quick_marks` to view recent selections
  - [x] Added `export_quick_marks` to export marked assets
  - [x] Integrates with comprehensive selection service
  - [x] Daily quick selections auto-created by mark type

## My Actual Workflow (What Matters)

1. **Discover & Import**
   - Download AI generations → inbox/
   - Auto-detect source (Midjourney, DALL-E, etc.)
   - Extract all metadata

2. **Search & Select**
   - "Show me cyberpunk portraits from last week"
   - "Find similar to these three"
   - Track why I selected each

3. **Prepare for Video**
   - Generate storyboards
   - Create Kling prompts
   - Export organized sets

## Next Focus Areas

### Enhanced Understanding System 🧠
**Why**: Better tags = better search = finding exactly what I need

#### Batch Analysis Optimization ✅
- [x] **Smart batching**: Group similar images for single API calls
  - [x] Detect near-duplicates using perceptual hashing
  - [x] Analyze one representative per group
  - [x] Track cost savings from optimization
- [x] **Progressive analysis**: Start with cheap providers, escalate if needed
  - [x] Google AI first (free tier)
  - [x] Add Claude/GPT only if results insufficient
  - [x] Skip analysis for similar images in groups
- [x] **Optimization tools**: MCP integration
  - [x] Added `analyze_images_optimized` tool
  - [x] Added `estimate_analysis_cost` tool
  - [x] Shows savings percentage and API calls saved

#### Local Vision Models Integration
- [ ] **Ollama support**: Free, private, no API costs
  - LLaVA for basic object detection
  - CLIP for style understanding
  - Fallback to cloud for complex cases
- [ ] **Hybrid approach**: Local first, cloud for enhancement
  - Local: Basic tags, objects, colors
  - Cloud: Artistic style, mood, complex scenes
  - Cost tracking comparison
- [ ] **Model management**: Easy switching between providers
  - Provider capabilities matrix
  - Automatic model selection based on image type
  - Performance benchmarks per model

#### Intelligent Tag Hierarchies
- [ ] **Semantic relationships**: Tags that understand context
  ```
  portrait → person → face → expression → happy
  cyberpunk → sci-fi → futuristic → neon
  ```
- [ ] **Auto-grouping**: Similar concepts cluster together
  - "sunset/sunrise/golden hour" → lighting conditions
  - "oil painting/watercolor/acrylic" → traditional media
  - "3D render/CGI/digital art" → digital media
- [ ] **Custom taxonomies**: My personal organization style
  - Project-specific tag groups
  - Mood boards as tag collections
  - Export/import tag schemes

#### Style Similarity Clusters
- [ ] **Visual DNA**: Extract style fingerprints
  - Color palettes
  - Composition patterns
  - Texture characteristics
  - Lighting styles
- [ ] **Auto-collections**: Find images that "feel" similar
  - "More like this" but for style
  - Discover unexpected connections
  - Build mood boards automatically
- [ ] **Style transfer hints**: Identify reusable prompts
  - Extract style elements from successful images
  - Generate prompt suggestions
  - Track which styles work well together

### Video Creation 2.0 🎬
**Why**: Turn static images into compelling narratives

#### Music & Rhythm Integration
- [ ] **Beat detection**: Sync transitions to music
  - Upload audio track
  - Detect BPM and rhythm points
  - Generate cut points automatically
- [ ] **Mood matching**: Suggest images based on music
  - Analyze music mood/energy
  - Match with image tags
  - Create emotional arcs
- [ ] **Duration calculator**: Perfect timing for each shot
  - Based on music tempo
  - Scene complexity consideration
  - Viewer attention patterns

#### Advanced Scene Transitions
- [ ] **Motion matching**: Smooth visual flow
  - Analyze image composition
  - Find compatible entry/exit points
  - Suggest camera movements
- [ ] **Narrative transitions**: Tell a story
  - Time of day progression
  - Zoom in/out sequences
  - Color temperature shifts
  - Emotional journey mapping
- [ ] **Effect library**: Ready-to-use transition styles
  - Morph between similar subjects
  - Match cuts on movement
  - Color/light transitions
  - Portal/doorway effects

#### Export Optimization
- [ ] **Editor presets**: One-click export for different tools
  - Premiere Pro XML
  - DaVinci Resolve EDL
  - Final Cut Pro FCPXML
  - After Effects compositions
- [ ] **Asset preparation**: Ready-to-edit packages
  - Consistent resolution/format
  - Color space management
  - Proxy generation
  - Folder structure templates
- [ ] **Metadata preservation**: Keep all context
  - Embed project info
  - Shot descriptions
  - Original prompts
  - Edit decision lists

#### Smart Project Templates
- [ ] **Genre templates**: Common video types
  - Music video (beat-synced cuts)
  - Story progression (narrative arc)
  - Showcase reel (best of collection)
  - Social media (platform-optimized)
- [ ] **Workflow automation**: From selection to export
  - Auto-generate shot lists
  - Calculate optimal durations
  - Create rough cuts
  - Export multiple versions
- [ ] **Learning system**: Improve with usage
  - Track successful exports
  - Remember preferences
  - Suggest improvements
  - Build personal style

## Backlog (When Actually Needed)

### Performance (Future)
- [ ] Test with larger collections (10k+ images)
- [ ] Profile DuckDB queries
- [ ] Optimize hot paths
- [ ] Cache embeddings for similarity search

### Nice to Have
- [ ] Web UI for quick previews
- [ ] Mobile companion app
- [ ] Plugin system for providers
- [ ] Advanced deduplication

### Never
- [ ] Multi-user support (it's MY tool)
- [ ] Cloud hosting (local is fine)
- [ ] Enterprise features (not a product)

## Development Principles

1. **It works or it's deleted**
2. **Every API call costs money**
3. **Simpler > Clever**
4. **File-based > Database**
5. **Test the happy path**
6. **Document for future me**

## Success Metrics

- Can I find the image I'm thinking of quickly?
- Do I know what I spent this month?
- Does it work smoothly for my daily workflow?
- Can I explain it in one paragraph?

---

**Remember**: This is a personal tool. Every feature should make MY life easier, not impress hypothetical users.