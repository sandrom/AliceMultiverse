# AliceMultiverse Quick Start

## 🤖 AI Assistant Quick Start (Recommended)

### With Claude Desktop (2 minutes)

1. **Install AliceMultiverse**:
   ```bash
   pip install -e .
   
   # First time? Run setup wizard:
   alice setup
   ```

2. **Configure Claude Desktop**:
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

3. **Start Chatting**:
   ```
   You: "Hi Claude, can you help organize my AI-generated images?"
   Claude: "I'll help you organize your AI-generated images using Alice..."
   ```

### Example Conversations

**Basic Organization**:
```
You: "I have a bunch of Midjourney images in my Downloads folder"
Claude: "I'll organize your Midjourney images from Downloads. Let me check what's there and sort them by date and project..."
```

**Content Understanding**:
```
You: "Can you find my most detailed AI portraits?"
Claude: "I'll search for portrait images with rich details and artistic styles..."
```

**Project Management**:
```
You: "Show me all the cyberpunk images I generated last week"
Claude: "Let me search for cyberpunk-style images from last week..."
```

## 🚀 First-Time Setup (New!)

If you're new to Alice, we have an interactive setup wizard:

```bash
# Run the setup wizard
alice setup

# This will help you:
# ✓ Check system requirements
# ✓ Configure API keys (with recommendations)
# ✓ Set up directories
# ✓ Test everything works
```

## 🔧 Debug CLI (Developers Only)

⚠️ **The CLI is deprecated for normal use.** Alice is an AI-native service.

### For Debugging Only
```bash
# Install for development
git clone https://github.com/yourusername/AliceMultiverse.git
cd AliceMultiverse
pip install -e .

# Setup and configuration
alice setup                   # Interactive setup wizard (NEW!)
alice keys setup              # Configure API keys only

# Debug commands
alice --debug --dry-run       # Test organization logic
alice --check-deps            # Verify dependencies
```

See [Debug CLI Reference](docs/user-guide/cli-usage.md) if you're a developer.

## 📁 How It Works

AliceMultiverse automatically:
1. **Detects** AI-generated content (15+ tools supported)
2. **Organizes** by date, project, and source
3. **Analyzes** content with AI understanding
4. **Maintains** metadata for instant search

### Supported Content
✅ **Images**: PNG, JPG, WebP, HEIC  
✅ **Videos**: MP4, MOV  
✅ **AI Tools**: Midjourney, DALL-E, Stable Diffusion, + 12 more

### Output Structure
```
organized/
├── 2024-03-15/              # Date
│   └── project-name/        # Project
│       └── midjourney/      # AI tool
│           ├── portraits/   # Content category
│           │   └── image1.png
│           └── 4-star/
│               └── image2.jpg
```

## 🎯 How to Use Alice

**Alice is an AI-native service.** Use it through AI assistants:

✅ **Recommended**: Chat with Claude or another AI assistant
🔧 **Debugging only**: Use CLI with --debug flag

### Why AI-Native?
- Zero learning curve
- Natural language is intuitive
- AI handles complexity for you
- Better error handling and guidance

## 🚀 Next Steps

### For AI Users
1. Ask Claude to organize your latest downloads
2. Have Claude search for specific styles or moods
3. Let Claude manage your creative projects

### For Developers
1. Use debug mode: `alice --debug --dry-run`
2. Check logs: `alice --debug --verbose`
3. Configure API keys: `alice keys setup`

## ❓ Common Questions

**Q: Do I need API keys?**  
A: Only for AI understanding features (Claude, GPT-4, etc.). Basic organization is free.

**Q: Can I still use the CLI?**  
A: Only for debugging with --debug flag. Normal usage is through AI assistants.

**Q: Where are my files organized to?**  
A: Default: `~/Pictures/AI-Organized`. Change in `settings.yaml`.

---

**AliceMultiverse**: Empowering AI assistants to manage your creative workflows 🎨