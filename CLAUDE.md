# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**IMPORTANT**: Always follow the guidelines in `instructions.md` for development practices.

## Project Overview

AliceMultiverse is an AI-native service that operates exclusively through AI assistants. The CLI has been deprecated and is maintained only for debugging purposes. The system excels at detecting, organizing, and assessing AI-generated content, serving as an intelligent orchestrator between AI assistants (Claude, ChatGPT) and creative tools/APIs.

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

```bash
# Organize AI-generated media (uses default folders from settings.yaml)
alice

# Specify directories
alice -i ~/Downloads/ai-images                       # Using -i flag
alice --inbox ~/Downloads/ai-images                  # Using --inbox flag
alice -o ~/Pictures/AI                               # Output folder only
alice -i ~/Downloads/ai-images -o ~/Pictures/AI     # Both folders (short form)
alice --inbox ~/Downloads/ai-images --organized ~/Pictures/AI  # Both folders (long form)

# Organize with quality assessment (adds star rating folders)
alice --quality
alice -q        # Short form

# Watch mode: continuously monitor for new files
alice -w        # Short form
alice --watch   # Long form

# Watch mode with quality assessment
alice -w -q
alice --watch --quality

# Override settings via command line
alice --paths.inbox=~/Downloads --quality.thresholds.3_star.max=70

# Pipeline variants (4 main options)
alice --pipeline brisque                      # 1. BRISQUE only (free)
alice --pipeline brisque-sightengine          # 2. BRISQUE + SightEngine (~$0.001/image)
alice --pipeline brisque-claude               # 3. BRISQUE + Claude (~$0.002/image for Haiku)
alice --pipeline brisque-sightengine-claude   # 4. BRISQUE + SightEngine + Claude (~$0.003/image)

# Convenience aliases
alice --pipeline basic      # Same as 'brisque'
alice --pipeline standard   # Same as 'brisque-sightengine'
alice --pipeline premium    # Same as 'brisque-sightengine-claude'
alice --pipeline full       # Same as 'brisque-sightengine-claude'

# Custom pipeline with specific stages
alice --pipeline custom --stages "brisque,sightengine"

# Pipeline with API keys (better to use 'alice keys setup')
alice --pipeline standard --sightengine-key "user,secret"
alice --pipeline premium --anthropic-key "sk-ant-..."

# Pipeline with cost limit
alice --pipeline premium --cost-limit 10.0

# Dry run to estimate costs
alice --pipeline premium --dry-run

# Resume interrupted pipeline
alice --pipeline premium --resume

# Move files instead of copying
alice --move
alice -m      # Short form

# Dry run to preview organization
alice --dry-run
alice -n         # Short form

# Force re-analysis (bypass cache)
alice --force-reindex
alice -f              # Short form

# Note: The separate detect-claude.py and detect-sightengine.py scripts have been 
# removed. All quality assessment is now integrated into the pipeline system. 
# Use --pipeline options as shown above.
```

### Dependencies Installation

```bash
# Core dependencies
pip install pillow numpy opencv-python tqdm

# For photo quality assessment
pip install image-quality

# For database support
pip install sqlalchemy alembic

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
4. **Quality Assessment**: Optional quality scoring and defect detection with persistent metadata embedding

### Key Modules

- **alice**: Main command with unified caching system (UnifiedCache class) for performance. Handles 15+ AI generation tools. Includes integrated BRISQUE quality assessment with --quality flag and watch mode (-w) for continuous monitoring.
- **Pipeline system**: Integrated quality assessment with BRISQUE, SightEngine, and Claude stages that can be combined in 4 different configurations.

### Quality Assessment Integration

When using `--quality` flag with alice:
- Images are assessed using BRISQUE scores (0-100, lower is better)
- Organized into star rating subfolders (5-star, 4-star, etc.)
- Videos are skipped for quality assessment
- Quality scores are cached in `.metadata` folders alongside source files
- Images are re-assessed only if the source file is modified
- Final structure: `organized/YYYY-MM-DD/project/source/5-star/file.png`
- **Image numbering is consistent at the project level** - numbers increment sequentially across all quality folders, ensuring stable references (e.g., `project-00023.png` remains the same image regardless of quality folder)
- **Automatic re-creation**: If you delete the organized folder, the system will recreate it with the same structure and quality ratings using cached metadata from source folders

**Quality Thresholds** (optimized for studio shots):
- 5-star: 0-25 (was 0-20) - Excellent quality
- 4-star: 25-45 (was 20-40) - Good quality  
- 3-star: 45-65 (was 40-60) - Average quality (many great studio shots)
- 2-star: 65-80 - Below average
- 1-star: 80-100 - Poor quality

The thresholds have been adjusted because BRISQUE sometimes rates high-quality studio shots with simple backgrounds as lower quality. You can further adjust via `settings.yaml` or command line.

### Metadata Storage Strategy

**All metadata is stored at the source level, NEVER in the destination:**
- A single `.metadata/` folder is created in the inbox root directory
- Files are tracked by content hash, allowing reorganization within inbox
- Quality assessments and analysis results are saved by content hash
- The organized folder contains ONLY the reorganized media files
- This allows you to delete and recreate the organized folder with different structures anytime
- Files can be moved around within the inbox without losing their metadata
- No re-analysis is needed unless you use `--force-reindex`

### Watch Mode

Use `-w` or `--watch` flag to continuously monitor the inbox for new files:
- Processes new files as they appear (checks every 5 seconds)
- Tracks processed files to avoid reprocessing
- Can be combined with --quality for automatic quality assessment
- Press Ctrl+C to stop watching

```bash
# Watch default folders
alice -w

# Watch custom folders with quality
alice -i ~/Downloads -o ~/Pictures/AI -w -q

# Long form equivalent
alice --inbox ~/Downloads --organized ~/Pictures/AI --watch --quality
```

### Multi-Stage Pipeline Assessment

The `--pipeline` flag enables quality refinement through multiple assessment stages:

#### Pipeline Modes:
- **basic**: BRISQUE only (free, local processing)
- **standard**: BRISQUE → SightEngine (~$0.001/image)
- **premium**: BRISQUE → SightEngine → Claude (~$0.003/image)
- **custom**: Define your own stages with `--stages`

#### Quality Refinement:
The pipeline combines scores from multiple sources to refine the star rating:
1. **BRISQUE**: Local quality assessment (0-100, lower is better)
2. **SightEngine**: Technical quality check (0-1, higher is better)
3. **Claude**: AI defect detection (penalizes anatomical/rendering errors)

#### Configurable Scoring Weights:
Edit `settings.yaml` to adjust how scores are combined:

```yaml
pipeline:
  scoring_weights:
    # Standard pipeline weights (must sum to 1.0)
    standard:
      brisque: 0.6      # 60% weight on BRISQUE
      sightengine: 0.4  # 40% weight on SightEngine
    
    # Premium pipeline weights (must sum to 1.0)
    premium:
      brisque: 0.4      # 40% weight on BRISQUE
      sightengine: 0.3  # 30% weight on SightEngine
      claude: 0.3       # 30% weight on Claude
  
  # Adjust star rating thresholds (0-1 scale)
  star_thresholds:
    5_star: 0.80  # Combined score >= 0.80 gets 5 stars
    4_star: 0.65  # Combined score >= 0.65 gets 4 stars
                  # Combined score < 0.65 gets 3 stars
```

#### Folder Structure:
Images are distributed across star-rating folders based on combined scores:
```
organized/2024-03-15/project/stablediffusion/
├── 5-star/   # Best quality (combined score >= 0.80)
├── 4-star/   # Good quality (combined score >= 0.65)
└── 3-star/   # Average quality (combined score < 0.65)
```

#### Cost Optimization:
- Progressive filtering: Higher-cost APIs only process higher-quality images
- Use `--dry-run` to preview without API calls
- Set `--cost-limit` to cap spending
- Cached results prevent reprocessing

## Important Notes

- **AI-Native Service**: Migration complete - use through AI assistants only
- API keys are managed securely - use `alice keys setup` for configuration
- The metadata cache in alice significantly improves performance for large collections
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

## Database Setup

AliceMultiverse uses PostgreSQL for all database operations:

### Local Development
```bash
# Start PostgreSQL with docker-compose
docker-compose up -d postgres

# Run database migrations
alembic upgrade head

# Database connection (set in environment)
export DATABASE_URL="postgresql://alice:alice@localhost:5432/alicemultiverse"
```

### Production (Kubernetes)
The database is managed by CloudNativePG operator and connection is provided via environment variable:
```bash
# Migrations are run automatically on deployment
# Connection string is injected from Kubernetes secret
DATABASE_URL=postgresql://alice:password@postgres-rw:5432/alicemultiverse
```

See README_DATABASE.md for details on the content-addressed storage system and PostgreSQL configuration.

## Event System

AliceMultiverse now includes an event-driven architecture foundation:

### Monitoring Events
```bash
# Monitor all events in real-time
python scripts/event_monitor.py

# Verbose mode with full event data
python scripts/event_monitor.py --verbose

# Collect metrics
python scripts/event_monitor.py --metrics
```

### Event Types
- **Asset Events**: `asset.discovered`, `asset.processed`, `asset.organized`, `quality.assessed`
- **Workflow Events**: `workflow.started`, `workflow.completed`, `workflow.failed`
- **Creative Events**: `project.created`, `style.chosen`, `context.updated`

See `docs/architecture/event-driven-architecture.md` for full documentation.