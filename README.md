# AliceMultiverse - AI Native Creative Workflow Hub

<div align="center">

**Connect AI assistants with your creative workflows through natural conversation**

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

## 🎯 What is AliceMultiverse?

AliceMultiverse is transitioning from a command-line tool to an AI-native service. It enables AI assistants like Claude and ChatGPT to help you organize media, manage creative projects, and automate workflows through natural conversation.

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

- "Organize my AI-generated images by quality and source"
- "Find all my cyberpunk-style portraits from last week"
- "Show me statistics about my creative projects"
- "Tag these images as references for my new project"
- "Find similar images to this one"

## 📦 Requirements

### System Dependencies

```bash
# macOS
brew install ffmpeg redis

# Ubuntu/Debian
sudo apt-get install ffmpeg redis-server

# Start Redis (required for event system)
redis-server
```

### Python Dependencies

Core dependencies are installed automatically, but Redis must be running:
- **Redis**: Required for event system (workflow tracking, real-time updates)
- **FFmpeg**: Required for video metadata extraction

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

## 📋 Configuration

Create `settings.yaml` for persistent settings:
```yaml
paths:
  inbox: ~/Downloads/AI-Images
  organized: ~/Pictures/AI-Organized

processing:
  quality: true        # Enable quality assessment
  watch: false         # Enable watch mode

pipeline:
  default_mode: standard  # basic, standard, premium
```

### API Keys

For advanced features, configure API keys:
```bash
alice keys setup
```

This will guide you through setting up:
- **Anthropic Claude**: Advanced image understanding and tagging
- **OpenAI GPT-4**: Vision analysis and prompt generation
- **Google AI**: Free tier image analysis
- **DeepSeek**: Cost-effective batch processing

## 🏗️ Architecture

AliceMultiverse uses an event-driven architecture designed for AI orchestration:

- **Structured APIs**: AI translates natural language to precise operations
- **Event System**: Monitor long-running operations in real-time
- **Service Boundaries**: Clean separation for reliable AI control
- **Persistent State**: Maintains context between conversations

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

## 🔮 Roadmap

AliceMultiverse is evolving into a comprehensive creative workflow orchestrator:

1. **Current**: Media organization with AI understanding
2. **Phase 1**: Full AI-native interface (in progress)
3. **Phase 2**: Multi-agent creative workflows
4. **Phase 3**: Integration with creative tools (ComfyUI, Photoshop, etc.)

See [ROADMAP.md](ROADMAP.md) for detailed plans.

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Empowering AI assistants to manage your creative workflows**

[Documentation](https://github.com/Alysonhower/AliceMultiverse/docs) • 
[Issues](https://github.com/Alysonhower/AliceMultiverse/issues) • 
[Discussions](https://github.com/Alysonhower/AliceMultiverse/discussions)

</div>