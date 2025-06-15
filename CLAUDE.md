# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**IMPORTANT**: Always follow the guidelines in `instructions.md` for development practices.

## Project Overview

AliceMultiverse is an AI-native service that operates exclusively through AI assistants. The CLI has been deprecated and is maintained only for debugging purposes. The system excels at detecting, organizing, and understanding AI-generated content, serving as an intelligent orchestrator between AI assistants (Claude, ChatGPT) and creative tools/APIs.

**Current Status**: AI-native service (CLI deprecated for normal use)
**Current Focus**: Media organization through AI assistant conversations
**Future Vision**: Complete creative workflow orchestration (see ROADMAP.md)
**Architecture**: Event-driven, designed for AI orchestration

## Usage During Transition Phase

### AI Assistant Interface (Recommended)

Alice is designed to be used through AI assistants:

```bash
# Start MCP server for Claude Desktop
alice mcp-server

# Configure in Claude Desktop settings instead:
# Add to ~/Library/Application Support/Claude/claude_desktop_config.json:
{
  "mcpServers": {
    "alice": {
      "command": "alice",
      "args": ["mcp-server"]
    }
  }
}
```

### Debug CLI (Developers Only)

**⚠️ Note**: Direct CLI usage is deprecated. Use --debug flag for development.

**✓ Fixed**: alice CLI no longer requires PYTHONPATH to be set.

**Note**: If you encounter import issues with the installed `alice` command, use `./alice` from the project root or `python -m alicemultiverse`.

```bash
# Organize AI-generated media (uses default folders from settings.yaml)
alice

# Specify directories
alice -i ~/Downloads/ai-images                       # Using -i flag
alice --inbox ~/Downloads/ai-images                  # Using --inbox flag
alice -o ~/Pictures/AI                               # Output folder only
alice -i ~/Downloads/ai-images -o ~/Pictures/AI     # Both folders (short form)
alice --inbox ~/Downloads/ai-images --organized ~/Pictures/AI  # Both folders (long form)

# Watch mode: continuously monitor for new files
alice -w        # Short form
alice --watch   # Long form

# Enable image understanding (semantic tagging)
alice --understand
alice -u        # Short form

# Watch mode with understanding
alice -w -u
alice --watch --understand

# Override settings via command line
alice --paths.inbox=~/Downloads --understanding.providers=openai,anthropic

# Understanding providers (can combine multiple)
alice --understand --providers openai          # Use OpenAI Vision
alice --understand --providers anthropic       # Use Claude Vision
alice --understand --providers google          # Use Google AI
alice --understand --providers all             # Use all available providers

# Custom understanding with specific providers
alice --understand --providers "openai,anthropic"

# Understanding with API keys (better to use 'alice keys setup')
alice --understand --openai-key "sk-..."
alice --understand --anthropic-key "sk-ant-..."

# Understanding with cost limit
alice --understand --cost-limit 10.0

# Dry run to preview understanding
alice --understand --dry-run

# Move files instead of copying
alice --move
alice -m      # Short form

# Dry run to preview organization
alice --dry-run
alice -n         # Short form

# Force re-analysis (bypass cache)
alice --force-reindex
alice -f              # Short form

# Note: The quality assessment system has been replaced with the understanding system.
# Use --understand for semantic tagging and content analysis.
```

### Dependencies Installation

```bash
# Core dependencies
pip install pillow numpy opencv-python tqdm

# For understanding system (optional providers)
pip install openai anthropic google-generativeai

# For database support
pip install duckdb redis

# System dependencies (macOS)
brew install ffmpeg
```

## Architecture

The system processes AI-generated media through a pipeline:

1. **Input**: `/inbox/` directory containing project folders with AI-generated media
   - **Supported formats**: PNG, JPG/JPEG, WebP, HEIC/HEIF (images), MP4, MOV (videos)
   - All formats support metadata embedding for self-contained assets
2. **Detection**: Identifies AI source through metadata and filename patterns
3. **Organization**: Creates structured output in `/organized/YYYY-MM-DD/project/source-type/`
4. **Understanding**: Optional semantic tagging and content analysis with metadata embedding

### Key Modules

- **alice**: Main command with unified caching system (UnifiedCache class) for performance. Handles 15+ AI generation tools. Includes understanding system with --understand flag and watch mode (-w) for continuous monitoring.
- **Cache Migration**: The system uses MetadataCacheAdapter for backward compatibility while transitioning to the new UnifiedCache system.
- **Understanding system**: Multi-provider image analysis that generates semantic tags for content discovery and organization.
- **Video providers**: Support for 7 video generation services (Runway, Pika, Luma, MiniMax, Kling, Hedra, Veo3) with MCP integration.
- **Deduplication**: Advanced duplicate detection using perceptual hashing (aHash, pHash, dHash, wHash) and FAISS similarity search.

### Understanding System Integration

When using `--understand` flag with alice:
- Images are analyzed by AI providers to generate semantic tags
- Tags describe content, style, mood, colors, and technical aspects
- Multiple providers can be used for comprehensive analysis
- Tags are embedded directly in file metadata (EXIF/XMP)
- Analysis results are cached to avoid re-processing
- Final structure: `organized/YYYY-MM-DD/project/source/file.png`
- **Tags enable semantic search**: Find images by content, not just filename
- **Portable metadata**: Tags travel with files when moved or shared

**Tag Categories**:
- **Content**: Objects, people, scenes (e.g., "portrait", "landscape", "cat")
- **Style**: Artistic style (e.g., "cyberpunk", "minimalist", "baroque")
- **Mood**: Emotional tone (e.g., "serene", "dramatic", "playful")
- **Technical**: Camera/render details (e.g., "shallow depth of field", "high contrast")
- **Colors**: Dominant colors and schemes (e.g., "blue tones", "warm palette")

The understanding system provides objective content description instead of subjective quality ratings.

### Metadata Storage Strategy

**All metadata is stored at the source level, NEVER in the destination:**
- A single `.metadata/` folder is created in the inbox root directory
- Files are tracked by content hash, allowing reorganization within inbox
- Understanding results and semantic tags are saved by content hash
- The organized folder contains ONLY the reorganized media files
- This allows you to delete and recreate the organized folder with different structures anytime
- Files can be moved around within the inbox without losing their metadata
- No re-analysis is needed unless you use `--force-reindex`

### Watch Mode

Use `-w` or `--watch` flag to continuously monitor the inbox for new files:
- Processes new files as they appear (checks every 5 seconds)
- Tracks processed files to avoid reprocessing
- Can be combined with --understand for automatic content analysis
- Press Ctrl+C to stop watching

```bash
# Watch default folders
alice -w

# Watch custom folders with understanding
alice -i ~/Downloads -o ~/Pictures/AI -w -u

# Long form equivalent
alice --inbox ~/Downloads --organized ~/Pictures/AI --watch --understand
```

### Understanding System Details

The understanding system analyzes images to generate semantic tags for search and discovery:

#### Provider Capabilities:
- **OpenAI Vision**: Excellent at object detection and scene understanding
- **Claude Vision**: Superior at artistic style and mood analysis
- **Google AI**: Strong technical analysis and color detection
- **DeepSeek**: Cost-effective general understanding

#### Multi-Provider Analysis:
Combine multiple providers for comprehensive understanding:

```yaml
understanding:
  providers:
    - name: openai
      focus: ["objects", "scenes", "text"]
      model: gpt-4-vision-preview
    - name: anthropic
      focus: ["style", "mood", "composition"]
      model: claude-3-haiku
    - name: google
      focus: ["technical", "colors", "lighting"]
      model: gemini-pro-vision
```

#### Tag Hierarchy:
Tags are organized hierarchically for better search:
```
art_style/
├── digital_art/
│   ├── cyberpunk
│   ├── vaporwave
│   └── glitch_art
├── traditional/
│   ├── oil_painting
│   └── watercolor
└── photography/
    ├── portrait
    └── landscape
```

#### Metadata Embedding:
Tags are embedded directly in files using standard formats:
- **JPEG/PNG**: EXIF and XMP metadata
- **WebP**: XMP metadata
- **HEIC**: EXIF metadata
- **Videos**: MP4 metadata tags

#### Cost Optimization:
- Use specific providers based on your needs
- Set `--cost-limit` to control spending
- Cached results prevent re-analysis
- Batch processing for efficiency

## Important Notes

- **AI-Native Service**: Migration complete - use through AI assistants only
- API keys are managed securely - use `alice keys setup` for configuration
- The unified cache system in alice significantly improves performance for large collections
- Video metadata extraction requires ffprobe (installed with ffmpeg)
- **Event-driven architecture** - All new features should publish/subscribe to events
- **Keep documentation updated** - README.md, ROADMAP.md, and architecture docs
- **Follow the vision** - AI-native service architecture (see docs/architecture/ai-native-vision.md)
- **Structured APIs only** - Alice uses structured search, not natural language (see docs/architecture/alice-interface-design.md)
- **Tags are semantic** - Use media_type for technical classification, tags for all semantic concepts
- **AI-First Documentation**: New docs should show AI conversations, not just CLI commands

## API Key Setup

Run the interactive setup wizard:
```bash
alice keys setup
```

This will store your API keys securely in macOS Keychain. For containerized environments, use environment variables:
- `SIGHTENGINE_API_USER` and `SIGHTENGINE_API_SECRET`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_AI_API_KEY`

For video generation providers:
- `RUNWAY_API_KEY`
- `PIKA_API_KEY`
- `LUMA_API_KEY`
- `MINIMAX_API_KEY`
- `KLING_API_KEY`
- `HEDRA_API_KEY`

## Recent Updates (June 2025)

- **Cache Migration Fix**: Fixed inheritance issues in EnhancedMetadataCacheAdapter to properly support the understanding system
- **Import Cleanup**: Resolved import issues with alice_events module (test_monorepo.py contains outdated imports)
- **Exception Handling**: Replaced all bare except statements with specific exception types
- **Code Quality**: Automated cleanup with ruff fixed 19,000+ style issues

## Storage System

AliceMultiverse uses a file-first approach with DuckDB for search:

### File-Based Storage
```bash
# All metadata stored in .metadata/ folders
# No database server required
# Search powered by embedded DuckDB

# Rebuild search index after adding files
alice index rebuild
```

### Configuration
```yaml
# settings.yaml
storage:
  search_db: data/search.duckdb
  project_paths:
    - ~/Projects/AI
```

See docs/architecture/storage/file-based-storage.md for details on the content-addressed storage system and file-based architecture.

## Event System

AliceMultiverse includes an event-driven architecture with two backend options:

### Event System Backends

1. **File-based Events (Default)**: Perfect for personal use and development
   - Events are written to JSON files in `~/.alice/events/`
   - No external dependencies required
   - Automatic daily log rotation
   - Simple and reliable

2. **Redis Streams (Optional)**: For distributed deployments
   - High-performance event streaming
   - Requires Redis server
   - Enable with: `export USE_REDIS_EVENTS=true`
   - Install with: `pip install -r requirements-redis.txt`

### Monitoring Events
```bash
# Monitor all events in real-time (works with both backends)
python scripts/event_monitor.py

# Verbose mode with full event data
python scripts/event_monitor.py --verbose

# Collect metrics
python scripts/event_monitor.py --metrics
```

### Event Types
- **Asset Events**: `asset.discovered`, `asset.processed`, `asset.organized`, `asset.analyzed`
- **Workflow Events**: `workflow.started`, `workflow.completed`, `workflow.failed`
- **Creative Events**: `project.created`, `style.chosen`, `context.updated`

### Cache System

Similarly, AliceMultiverse supports two cache backends:

1. **File-based Cache (Default)**: Local JSON file cache
   - Stored in `~/.alice/cache/`
   - No Redis required
   - Perfect for personal use

2. **Redis Cache (Optional)**: For high-performance caching
   - Enable with: `export USE_REDIS_CACHE=true`
   - Requires Redis server

See `docs/architecture/event-driven-architecture.md` for full documentation.

## Personal Tool Context

This is Sandro's personal tool, not a product. Design decisions should optimize for:
1. His specific workflow (thousands of AI images, natural search)
2. His money (API costs matter)
3. His maintenance burden (keep it simple)
4. His preferences (AI-native interface, file-based storage)