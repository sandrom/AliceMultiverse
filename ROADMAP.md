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
- **AI-Native Interface**: 33 MCP tools for complete workflow control
- **Semantic Search**: Find images by content, style, mood, tags
- **Multi-Path Storage**: Assets across multiple locations with rules
- **Cost Tracking**: Detailed spending reports and budget warnings
- **Video Workflows**: Storyboards, Kling prompts, Flux keyframes
- **File-Based Everything**: No database servers required
- **Project Management**: Full creative context tracking via MCP
- **Quick Selection**: Instant marking of favorites/hero shots
- **Duplicate Detection**: Find and manage exact duplicates
- **Batch Analysis**: 20-40% cost savings with similarity detection
- **Local Vision Models**: Free analysis with Ollama integration
- **Tag Hierarchies**: Semantic organization with clustering
- **Style Analysis**: Visual DNA extraction and similarity search

### ⚠️ What's Actually Broken
1. **DuckDB Duplication**: Maintaining two implementations = double the bugs
2. **Music sync is manual**: Have to count beats myself = tedious
3. **Export is manual**: Re-create timelines every time = time waste
4. **No large-scale testing**: Will it handle 10k images? Unknown

## Immediate Priorities (Fix What's Broken)

### 1. DuckDB Consolidation 🔧
**Why**: Two implementations = double maintenance = confusion

- [ ] Merge DuckDBSearchCache and DuckDBSearch
  - [ ] Map all usage points for both implementations
  - [ ] Create unified interface preserving both APIs
  - [ ] Migrate MCP server to unified version
  - [ ] Migrate search handler to unified version
  - [ ] Remove deprecated implementation
  - [ ] Update all imports and tests

### 2. Video Creation 2.0 - Music Integration 🎵
**Why**: Manual sync is tedious, music drives emotion

- [x] Basic music analyzer module created (music_analyzer.py)
- [ ] Integrate music analyzer with MCP tools
  - [ ] Add `analyze_music` tool for beat/mood detection
  - [ ] Add `sync_to_music` tool for timeline generation
  - [ ] Add `suggest_cuts` tool based on rhythm
- [ ] Connect mood analysis to image selection
  - [ ] Match image tags to music mood
  - [ ] Create emotional arc suggestions
- [ ] Export sync data to editors
  - [ ] DaVinci Resolve markers at beat points
  - [ ] CapCut timing JSON

### 3. Export Templates 📹
**Why**: Re-creating export settings every time wastes time

- [ ] Add DaVinci Resolve EDL/XML export
  - [ ] Timeline with markers for beat sync
  - [ ] Color metadata preservation
  - [ ] Compound clips for sequences
- [ ] Build CapCut project export
  - [ ] JSON format for mobile editing
  - [ ] Transition suggestions
  - [ ] Effect presets
- [ ] Include proxy generation for smooth editing

## Recently Completed (2025-06)

### Enhanced Understanding System ✅
- **Batch Analysis Optimization**: 20-40% cost savings via similarity detection
- **Local Vision Models**: Ollama integration for free, private analysis
- **Intelligent Tag Hierarchies**: Semantic organization with clustering
- **Style Similarity Clusters**: Visual DNA extraction and matching

### Workflow Improvements ✅
- **Project Management**: Full MCP integration with creative context
- **Quick Selection**: Instant marking system for favorites
- **Duplicate Detection**: Find and manage exact duplicates
- **Code Cleanup**: Removed deprecated files, documented future removals

## My Actual Workflow (What Matters)

1. **Discover & Import**
   - Download AI generations → inbox/
   - Auto-detect source (Midjourney, DALL-E, etc.)
   - Extract all metadata

2. **Search & Select**
   - "Show me cyberpunk portraits from last week"
   - "Find similar to these three"
   - Mark favorites with quick_mark
   - Track why I selected each

3. **Prepare for Video**
   - Generate storyboards
   - Create Kling prompts
   - Export organized sets
   - (Missing: Music sync automation)

## Next Focus Areas

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
- [ ] **Editor presets**: One-click export for my tools
  - DaVinci Resolve EDL/XML with full metadata
  - CapCut JSON for mobile editing
- [ ] **Asset preparation**: Ready-to-edit packages
  - Consistent resolution/format
  - Color space management (Resolve ACES workflow)
  - Proxy generation for 4K+ content
  - Organized bin structure
- [ ] **Metadata preservation**: Keep all context
  - Embed AI generation prompts
  - Shot descriptions and tags
  - Music sync markers
  - Scene transition notes

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
- [ ] Mobile companion app for on-the-go selection
- [ ] Plugin system for custom providers
- [ ] Perceptual hash deduplication (beyond exact matches)

## Development Principles

1. **Working > Perfect**: Fix what's broken before adding new
2. **Track costs**: Every API call = money spent
3. **Simple > Complex**: Less code = less bugs
4. **Files > Servers**: Everything portable and local
5. **Test reality**: Focus on actual daily workflow
6. **Document clearly**: Future me needs to understand

## Success Metrics

- Can I find any image in seconds using natural queries?
- Is my monthly AI spend under control and visible?
- Does my daily workflow have zero friction?
- Can I explain what each module does in one sentence?

## Priority Framework

**Daily Reality Check** (from top of file):
1. What's broken TODAY? → Immediate priority
2. What costs money? → Track and optimize
3. What's complex? → Simplify it
4. What's unused? → Delete it

---

**Remember**: This is MY personal tool. Every decision should optimize for my specific workflow, not hypothetical users.