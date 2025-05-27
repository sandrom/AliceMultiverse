# AliceMultiverse - AI Assistant Interface & Creative Workflow Hub

<div align="center">

**A powerful interface for AI assistants (Claude, ChatGPT) with integrated creative workflow tools**

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

## 🎯 What is AliceMultiverse?

AliceMultiverse is an extensible interface that connects AI assistants like Claude and ChatGPT with your local development environment and creative tools. It provides AI assistants with powerful capabilities including file operations, media management, code execution, and workflow automation.

### Core Capabilities:
- **🤖 AI Assistant Interface** - Direct integration with Claude Desktop and other AI assistants via MCP
- **📁 Smart Media Organization** - Automatically organize AI-generated images by source, date, and quality
- **🎨 Creative Workflows** - Manage projects, assets, and creative processes
- **🔧 Development Tools** - File operations, code execution, and project management
- **🔄 Event-Driven Architecture** - Extensible system for building custom workflows

## 🚀 Quick Start

### 1. Install
```bash
pip install -e .
```

### 2. Use as AI Assistant Tool (Claude Desktop)
Add to your Claude Desktop configuration:
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

### 3. Use Standalone Features
```bash
# Start interactive AI interface
alice interface

# Organize AI-generated media
alice --quality

# Monitor events in real-time
python scripts/event_monitor.py
```

## ✨ Key Features

### For AI Assistants
- **File System Access** - Read, write, and manage files
- **Media Processing** - Organize and analyze images/videos
- **Project Management** - Create and manage creative projects
- **Workflow Automation** - Execute complex multi-step processes

### For Users
- **🤖 AI Detection** - Recognizes content from 15+ AI tools (Midjourney, DALL-E, Stable Diffusion, etc.)
- **⭐ Quality Assessment** - Multi-stage pipeline with BRISQUE, SightEngine, and Claude
- **📊 Event Monitoring** - Real-time visibility into all operations
- **🔄 Watch Mode** - Continuous monitoring for new content

## 📋 Configuration

### Basic Usage
```bash
# Use with default settings
alice

# Specify custom directories
alice --inbox ~/Downloads/AI --organized ~/Pictures/AI-Sorted

# Enable quality assessment
alice --quality

# Start AI interface
alice interface
```

### Advanced Configuration
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

## 🎨 Media Organization Example

AliceMultiverse can organize your AI-generated content:

### Before:
```
Downloads/
├── 00123.png                    # What AI made this?
├── _9f7d8a6b-4c2e-11ee.png     # Midjourney? 
├── ComfyUI_00456_.png           # Another tool...
└── dalle-3-image.jpg            # Mixed together
```

### After:
```
organized/
├── 2024-03-15/
│   ├── project-cyberpunk/
│   │   ├── midjourney/
│   │   │   ├── 5-star/         # Best quality
│   │   │   ├── 4-star/         # Good quality
│   │   │   └── 3-star/         # Average
│   │   └── dalle/
│   │       └── 5-star/
│   └── project-nature/
│       └── stablediffusion/
```

## 🔧 Architecture

AliceMultiverse uses an event-driven architecture that makes it easy to extend:

- **Event System** - All operations publish events for monitoring and integration
- **Modular Pipeline** - Compose different processing stages
- **MCP Integration** - Direct integration with AI assistants
- **Caching Layer** - Intelligent caching for performance

## 🛠️ Development

### Running Tests
```bash
pytest tests/
```

### Monitoring Events
```bash
python scripts/event_monitor.py --verbose
```

### API Keys
For advanced features, set up API keys:
```bash
alice keys setup
```

## 📚 Documentation

- [Getting Started](docs/getting-started/quickstart.md)
- [AI Integration](docs/integrations/claude-desktop.md)
- [Architecture](docs/architecture/index.md)
- [API Reference](docs/api/reference/)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.