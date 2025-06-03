# AliceMultiverse - Sandro's Personal AI Creative Tool

<div align="center">

**My personal workflow for organizing AI-generated media through Claude**

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*This is not a product - it's my personal tool that I'm sharing*

</div>

## 🎯 What is AliceMultiverse?

I'm Sandro, and I built AliceMultiverse to solve my specific problem: managing thousands of AI-generated images scattered across folders, finding the right ones for video projects, and tracking what I've already used. This is a personal tool built for my workflow - organizing through natural conversation with Claude rather than clicking through UIs.

**Why I built this:**
- I generate 100-500 images per day across multiple AI tools
- I need to find specific images quickly ("that cyberpunk portrait from last week")
- I want to track which images I've used in videos
- I prefer talking to Claude over using traditional UIs
- I need to control API costs (those AI calls add up fast!)

You're welcome to fork and adapt it for your needs, but be aware that I make changes based on my daily workflow, not general use cases.

> **🚀 New**: Direct integration with Claude Desktop via MCP (Model Context Protocol)

## 🤖 AI-First Usage (Recommended)

### Claude Desktop Integration

1. **Install AliceMultiverse**:
   ```bash
   pip install -e .
   ```

2. **Configure Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

3. **Start chatting with Claude**:
   ```
   You: "Hi Claude, I need help organizing my AI-generated images"
   Claude: "I'll help you organize your AI-generated images using Alice..."
   
   You: "Check the quality of images in my Downloads folder"
   Claude: "I'll assess the quality of images in your Downloads folder..."
   ```

### What Can You Ask?

**Search & Discovery:**
- "Find all my cyberpunk images with neon lighting"
- "Show me portraits from last week"
- "Find images similar to this one" (after selecting an image)
- "What moody landscape images do I have?"

**Organization & Curation:**
- "Organize my AI-generated images from Downloads"
- "Move these rejected images to sorted-out folder"
- "Track which images I selected for the video project"

**Understanding Content:**
- "What's in this image?" (semantic tagging)
- "Find all images with cats"
- "Show me minimalist style images"

## 📦 Requirements

### System Dependencies

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian  
sudo apt-get install ffmpeg
```

### Python Dependencies

Core dependencies are installed automatically:
- **FFmpeg**: Required for video metadata extraction
- **Redis**: Optional, only needed for future microservices architecture

## 🔧 Debug CLI (Developers Only)

⚠️ **Direct CLI usage is deprecated.** The CLI is maintained only for debugging purposes.

```bash
# Debugging examples
alice --debug --dry-run              # Debug organization logic
alice --debug --check-deps           # Check dependencies
alice keys setup                     # Still available for API key setup
alice mcp-server                     # Start MCP server
```

For normal usage, please use Alice through AI assistants as shown above.

## 🎯 Why I Built This

I work with multiple AI generation tools daily (Midjourney, DALL-E, Stable Diffusion, Kling, etc.) and needed a way to:
1. **Find specific images** from thousands without manual tagging
2. **Talk naturally** to search ("that cyberpunk cat from last week")
3. **Track my creative decisions** during curation
4. **Keep costs under control** with multiple AI APIs

## ✨ Key Features

### Media Organization
- **🤖 AI Detection**: Recognizes content from 15+ AI tools (Midjourney, DALL-E, Stable Diffusion, etc.)
- **⭐ Quality Assessment**: Multi-stage pipeline with BRISQUE, SightEngine, and Claude
- **📁 Smart Organization**: Automatically sorts by date, project, source, and quality
- **🏷️ Semantic Tagging**: Tag assets by style, mood, subject for easy discovery

### Creative Workflows
- **📊 Project Management**: Track assets across multiple projects
- **🔍 Smart Search**: Find assets using natural descriptions
- **🔄 Event Monitoring**: Real-time visibility into all operations
- **🎨 Style Analysis**: Understand and categorize your creative outputs

## 🚀 Getting Started

### First-Time Setup (New!)

Run the interactive setup wizard:
```bash
alice setup
```

This will help you:
- ✓ Check system requirements
- ✓ Configure API keys with provider recommendations
- ✓ Set up your directories
- ✓ Test that everything works

### Manual Configuration

Or create `settings.yaml` manually (see `settings.yaml.example`):
```yaml
paths:
  inbox: ~/Downloads/AI-Images
  organized: ~/Pictures/AI-Organized

processing:
  understanding: true   # Enable AI understanding
  copy_mode: true      # Copy instead of move (safer)

understanding:
  providers:
    - google    # Free tier: 50/day
    - deepseek  # Cheapest: ~$0.001/image
```

### API Keys

Configure API keys for AI features:
```bash
alice keys setup
```

Supported providers:
- **Google AI**: Free tier (50 images/day) - RECOMMENDED
- **DeepSeek**: Most cost-effective (~$0.001/image)
- **Anthropic Claude**: Best quality understanding
- **OpenAI GPT-4**: Alternative vision analysis

### 💰 Cost Management (New!)

I added cost tracking because API calls add up FAST:

```bash
# See what you're spending
alice cost report

# Set budget limits
alice cost set-budget --daily 1.00 --monthly 20.00

# Compare provider costs
alice cost providers --category understanding
```

**Cost warnings**: Before any expensive operation, you'll see:
```
💸 COST ESTIMATE FOR AI UNDERSTANDING
======================================
Provider: anthropic
Images to analyze: 50
Estimated cost: $0.25

💡 Cheaper alternatives:
  • DeepSeek: ~$0.0002 per image
  • Google AI: FREE (50 images/day)

Proceed with analysis? (y/N):
```

## 🏗️ Architecture Philosophy

Designed for my workflow:

- **AI-First Interface**: I talk to Claude, Claude talks to Alice
- **File-Based Truth**: All metadata lives with files, portable and simple
- **Cost Aware**: Track every API call (it's my money)
- **Pragmatic Choices**: DuckDB for search, files for storage, simplicity over scale

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md)
- [AI Integration Guide](docs/integrations/claude-desktop.md)
- [Architecture Overview](docs/architecture/)
- [API Reference](docs/api/reference/)

## 🎓 Examples

### AI Assistant Conversation
```
You: "I just generated 50 new images with Midjourney, can you help organize them?"

Claude: "I'll help organize your Midjourney images. Let me analyze your Downloads folder 
and organize them by content and style. I'll use AI understanding to tag and 
categorize them..."

[Alice analyzes and organizes images with semantic tags]

Claude: "I've organized 50 images from your Downloads folder:
- 18 portraits (realistic, stylized, fantasy)
- 22 landscapes (sci-fi, nature, abstract)  
- 10 conceptual art pieces

They're now in Pictures/AI-Organized/2024-03-15/midjourney/
Each image has been tagged with style, mood, and subject. 
Would you like me to show you specific types?"
```

### Debugging
```bash
# For developers only
alice --debug --dry-run --verbose
```

## 🔮 My Personal Roadmap

This tool evolves based on what I need for my daily workflow:

1. **Current**: Natural language search through Claude ("show me cyberpunk portraits")
2. **Just Added**: Cost warnings before expensive operations (saved me $50 last week!)
3. **Next**: Better first-run experience (setting up API keys is confusing)
4. **Future**: Complete video pipeline (select → storyboard → Kling prompts)

See [ROADMAP.md](ROADMAP.md) for what I'm actually working on.

## 🤝 Want to Use This?

This is my personal tool, not a supported product. You're welcome to:
- Fork it and adapt to your needs
- Submit PRs if you fix bugs I might care about
- Open issues, but I'll only fix what affects my workflow

**Warnings:**
- I break things that I don't use
- Documentation might be out of date
- It's optimized for my MacBook + my folder structure
- API costs can add up quickly without proper configuration

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

*Built by Sandro for Sandro's workflow*

If you find it useful, great! But remember, this is a personal tool, not a product.

</div>