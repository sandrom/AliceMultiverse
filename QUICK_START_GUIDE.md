# AliceMultiverse Quick Start Guide

## 🎯 Your Next Steps (In Order)

### 1. **Start the MCP Server** (Do This First!)

```bash
# In the AliceMultiverse directory
python -m alicemultiverse mcp-server
```

Then add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "alice": {
      "command": "python",
      "args": ["-m", "alicemultiverse", "mcp-server"],
      "cwd": "/Users/sandro/Documents/AI/AliceMultiverse"
    }
  }
}
```

Restart Claude Desktop and you'll have access to **106 AI creative tools**!

### 2. **Set Up Your API Keys**

```bash
# Run the provider setup script
python examples/setup_providers.py

# Or use the CLI
python -m alicemultiverse keys setup
```

Recommended providers:
- **OpenAI**: Best for understanding image content
- **Anthropic**: Great for artistic analysis
- **Google AI**: Good for technical details

### 3. **Test Basic Organization**

```bash
# Test organizing your AI images
python examples/test_organization.py

# Or use the CLI directly
python -m alicemultiverse debug organize \
  -i ~/Downloads/ai-images \
  -o ~/Pictures/AI-Organized \
  --dry-run
```

### 4. **Explore Advanced Features**

Once MCP is connected, ask Claude to:

#### 🔍 **Search & Discovery**
- "Find all my cyberpunk portraits from last week"
- "Show me images similar to this one"
- "Find all images generated with DALL-E 3"

#### 📊 **Analytics & Insights**
- "Analyze my creation patterns"
- "Show me which styles I use most"
- "Track my API costs this month"

#### 🎬 **Video Creation**
- "Create a video sequence from these images"
- "Suggest transitions between scenes"
- "Generate B-roll suggestions"

#### 🎨 **Creative Workflows**
- "Help me create variations of this style"
- "Organize my project assets"
- "Track prompt effectiveness"

### 5. **Monitor Performance**

```bash
# Check system performance
python -m alicemultiverse debug performance

# View event stream
python scripts/event_monitor.py --verbose
```

## 💡 Pro Tips

### Batch Processing
```python
# Process large collections efficiently
from alicemultiverse.storage.batch_operations import BatchOperations

batch_ops = BatchOperations(batch_size=100)
# Process thousands of files without memory issues
```

### Understanding System
```bash
# Enable AI understanding for semantic tagging
python -m alicemultiverse debug organize \
  --understand \
  --providers openai,anthropic \
  --cost-limit 10.0
```

### Event Monitoring
```bash
# Watch real-time events
python scripts/event_monitor.py --follow
```

## 🚀 Advanced Workflows

### 1. **Deduplication Pipeline**
Use MCP tools to:
- Find duplicate images
- Identify similar variations
- Clean up your collection

### 2. **Project Management**
- Create project structures
- Track asset relationships
- Export for video editing

### 3. **Style Development**
- Analyze successful generations
- Track style evolution
- Create style guides

## 📚 Resources

- **106 MCP Tools**: See `docs/MCP_TOOLS_REFERENCE.md`
- **API Documentation**: Check `docs/developer/`
- **Examples**: Browse `examples/` directory
- **Roadmap**: Read `ROADMAP.md` for upcoming features

## 🎉 You're Ready!

With the MCP server running and API keys configured, you now have:
- AI-powered media organization
- Semantic search across collections
- Creative workflow automation
- Performance tracking
- And 100+ more capabilities!

Start with simple commands and gradually explore the advanced features. The system is designed to grow with your needs.

**Happy creating with AliceMultiverse! 🚀**