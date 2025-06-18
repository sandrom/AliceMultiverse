# AliceMultiverse - AI-Native Media Organization

<div align="center">

**Organize AI-generated media through natural conversation with Claude**

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*Personal tool by Sandro - fork and adapt as needed*

</div>

## 🎯 What is AliceMultiverse?

AliceMultiverse is an AI-native service for organizing AI-generated media. Instead of clicking through UIs, you talk to Claude (or other AI assistants) to:

- Organize thousands of AI-generated images automatically
- Find specific images through natural language ("cyberpunk portrait with neon")
- Track which images you've used in projects
- Generate videos with 7+ AI providers
- Create professional transitions and effects

## 🚀 Quick Start

### 1. Install
```bash
pip install -e .
```

### 2. Configure Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "alice": {
      "command": "alice",
      "args": ["mcp-server"]
    }
  }
}
```

### 3. Set API Keys
```bash
alice keys setup
```

### 4. Start Using Through Claude
```
You: "Organize my AI images from Downloads"
Claude: "I'll help organize your AI-generated images..."
```

## 💬 Example Conversations

### Finding Images
```
"Find all cyberpunk portraits with neon lighting"
"Show me dark moody landscapes from last week"
"Find images similar to the one I just selected"
```

### Organizing Media
```
"Move rejected images to sorted-out folder"
"Organize by project and AI source"
"Track which images I used in the video"
```

### Understanding Content
```
"What's in this image?"
"Find all images with cats"
"Show me minimalist style artwork"
```

### Video Creation
```
"Generate ocean waves video with sound using Veo 3"
"Create cinematic video with Runway Gen-3"
"Make a music video from these images"
"Suggest b-roll for this scene"
```

## 🏗️ Architecture (Simplified)

```
alicemultiverse/
├── mcp/              # MCP server and 100+ tools
├── interface/        # AI assistant interface
├── organizer/        # Media organization
├── understanding/    # AI-powered image analysis
├── providers/        # AI generation providers
├── workflows/        # Video creation workflows
└── assets/           # Media handling
```

### Key Design Principles
- **AI-Native**: Designed for AI assistants, not humans
- **File-First**: No database servers, metadata travels with files
- **Cost-Conscious**: Tracks and optimizes API usage
- **Simple**: Direct function calls, minimal abstractions

## 🛠️ Debug CLI (Advanced Users)

The CLI is for debugging only. Normal usage is through AI assistants.

```bash
# View debug commands
alice --debug

# Organize files (debug mode)
alice --debug organize -i ~/Downloads/ai-images -o ~/Pictures/AI

# Run deduplication
alice --debug dedup ~/Pictures/AI
```

## 📊 Features

### Core
- ✅ Automatic organization by date/project/source
- ✅ Content-based deduplication
- ✅ Semantic search through tags
- ✅ Watch mode for continuous organization
- ✅ **NEW**: Parallel processing for large collections
- ✅ **NEW**: Performance profiles (fast, memory_constrained, large_collection)
- ✅ **NEW**: Batch database operations for 15x faster processing

### Understanding
- ✅ Multi-provider image analysis (OpenAI, Claude, Google)
- ✅ Automatic tagging (style, mood, content)
- ✅ Metadata embedding in files
- ✅ Cost optimization

### Video & Creative
- ✅ 7 video generation providers
- ✅ Professional transitions (morphing, portals, match cuts)
- ✅ Music synchronization
- ✅ B-roll suggestions
- ✅ Multi-format export

## 🔧 Configuration

Settings in `~/.alicemultiverse/settings.yaml`:

```yaml
paths:
  inbox: ~/Downloads/ai-images
  organized: ~/Pictures/AI

understanding:
  providers: [openai, anthropic]
  cost_limit: 10.0

organization:
  watch_mode: true
  move_files: false
```

## ⚡ Performance

AliceMultiverse now handles large collections efficiently:

```bash
# Fast processing for powerful machines
export ALICE_PERFORMANCE=fast

# Memory-constrained mode for older systems  
export ALICE_PERFORMANCE=memory_constrained

# Optimized for thousands of files
export ALICE_PERFORMANCE=large_collection
```

See the [Performance Guide](docs/PERFORMANCE_GUIDE.md) for detailed configuration.

## 💰 Cost Management

AliceMultiverse tracks API costs:

```
You: "How much have I spent today?"
Claude: "Today's API usage: $2.47 across 156 operations..."

You: "Set daily limit to $5"
Claude: "I've set your daily API limit to $5.00"
```

## 🤝 Contributing

This is a personal tool that I update based on my needs. Feel free to:
- Fork for your own use
- Submit issues if you find bugs
- Share improvements that might help others

But remember: I make changes based on my workflow, not general use cases.

## 📄 License

MIT - Use however you want, but no warranty provided.

---

Built by Sandro for organizing AI-generated media through natural conversation.