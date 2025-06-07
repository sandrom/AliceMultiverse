# AliceMultiverse Quick Reference

## 🚀 Most Common Commands

### Start MCP Server (for Claude Desktop)
```bash
alice mcp-server
```

### Organize Media
```bash
# Default folders from settings.yaml
alice

# Custom folders
alice -i ~/Downloads/ai-images -o ~/Pictures/AI

# Watch mode (continuous monitoring)
alice -w

# With AI understanding
alice --understand
```

### Search Assets
```bash
# Search by tags
alice search --tags "cyberpunk,portrait"

# Search by date
alice search --after 2025-01-01

# Search by AI source
alice search --source midjourney
```

### Manage Prompts
```bash
# Search prompts
alice prompts search "sunset"

# List effective prompts
alice prompts list --min-effectiveness 0.8

# Track prompt usage
alice prompts stats
```

### Generate Content
```bash
# Generate image
alice generate image "cyberpunk city" --model flux-pro

# Generate video with Veo 3
alice generate video "ocean waves with sound" --model veo-3 --enable-audio

# Remix with reference
alice remix image.png "make it cyberpunk" --model flux-dev-kontext
```

## 📁 Key Directories

- **Inbox**: `~/AliceMultiverse/inbox/` (AI downloads)
- **Organized**: `~/AliceMultiverse/organized/` (sorted media)
- **Projects**: `~/AliceMultiverse/projects/` (project files)
- **Prompts**: `{project}/.prompts/` (YAML prompt files)
- **Cache**: `~/.alice/` (metadata, events, cache)

## 🔧 Configuration

### API Keys
```bash
alice keys setup        # Interactive setup
alice keys list        # Show configured providers
alice keys usage       # Check API usage/costs
```

### Settings Override
```bash
# Override any setting via CLI
alice --understanding.providers=openai,anthropic
alice --paths.inbox=~/Downloads
alice --processing.quality=true
```

## 🎯 Claude Desktop Integration

### Available MCP Tools
- `search_assets` - Find media by tags, date, source
- `organize_media` - Sort downloads into organized folders  
- `find_similar_images` - Similarity search
- `generate_image` - Create images with any provider
- `generate_veo3_video` - Create videos with audio
- `manage_prompts` - Track effective prompts
- `create_selection` - Curate asset collections
- Plus 50+ more tools...

### Example Claude Requests
- "Find all my cyberpunk portraits from this week"
- "Organize my AI downloads and tag them"
- "Generate a video of ocean waves with natural sound"
- "Show me images similar to this selection"
- "What prompts worked well for fantasy landscapes?"

## 🎨 Supported Formats

### Images
PNG, JPG/JPEG, WebP, HEIC/HEIF

### Videos  
MP4, MOV, AVI, MKV, WebM

### AI Sources (Auto-Detected)
Midjourney, DALL-E, Stable Diffusion, Flux, Leonardo, Firefly, Freepik, Ideogram, Kling, RunwayML, Pika, LumaLabs, and more...

## 💡 Pro Tips

1. **Batch Operations**: Use watch mode (`-w`) for hands-free organization
2. **Semantic Search**: Enable understanding (`--understand`) for content-based search
3. **Project Context**: Prompts are automatically associated with current project
4. **Cost Control**: Set `--cost-limit` when using understanding features
5. **Fast Preview**: Use `--dry-run` to preview operations without changes

---
*Quick Reference v1.0 - January 2025*