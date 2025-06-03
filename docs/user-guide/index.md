# User Guide - How I Use AliceMultiverse

This is how I use my personal tool. Your workflow might be different, and that's fine - fork it and make it yours!

## 🚀 Getting Started

<div class="grid cards" markdown>

- **[AI Conversations](ai-conversations.md)** 🤖
    
    Learn to use Alice through natural conversation with AI assistants

- **[Claude Integration](claude-integration.md)** 
    
    Set up direct integration with Claude Desktop

- **[CLI Usage](cli-usage.md)** 💻
    
    Traditional command-line interface reference

- **[Quick Start](../../QUICKSTART.md)**
    
    Get up and running in 2 minutes

</div>

## 📚 Core Features

<div class="grid cards" markdown>

- **[Basic Usage](basic-usage.md)**
    
    Fundamental concepts and workflows

- **[Quality Assessment](quality-assessment.md)**
    
    Understanding BRISQUE scores and star ratings

- **[Watch Mode](watch-mode.md)**
    
    Continuous monitoring for new files

- **[Pipeline System](pipeline-system.md)**
    
    Multi-stage quality assessment

- **[API Keys](api-keys.md)**
    
    Setting up and managing API credentials

- **[FLUX Kontext Guide](flux-kontext-guide.md)** ✨
    
    Iterative image editing with FLUX Kontext models

- **[fal.ai Provider](fal-provider.md)**
    
    Generate images and videos with FLUX and Kling

- **[Selection Workflow](selection-workflow-guide.md)** 🎯
    
    Collaborative image selection and curation

- **[Video Creation Workflow](video-creation-workflow-guide.md)** 🎬
    
    Turn selected images into engaging videos

- **[Multi-Path Storage Guide](multi-path-storage-guide.md)** 📁
    
    Complete guide to managing assets across multiple storage locations

</div>

## 🎯 Usage Modes

### AI-First (Recommended)

Alice is designed to work through natural conversation:

```
You: "Hey Claude, I need help organizing my AI images"
Claude: "I'll help you organize your AI-generated images. Let me scan your Downloads folder..."

You: "Find my best cyberpunk portraits"
Claude: "Searching for high-quality cyberpunk portraits..."
```

**Benefits:**
- Natural language interaction
- Context-aware assistance
- Guided workflows
- No commands to memorize

### Traditional CLI

For direct control and automation:

```bash
alice --quality --pipeline premium
alice --watch --inbox ~/Downloads
```

**Benefits:**
- Precise control
- Scriptable automation
- Debugging capabilities
- Batch processing

## 🔄 Typical Workflows

### For AI Users

1. **Daily Organization**
   ```
   "Claude, organize today's new AI images"
   ```

2. **Quality Curation**
   ```
   "Show me only 5-star images from this week"
   ```

3. **Project Management**
   ```
   "Create a portfolio collection from my best work"
   ```

### For CLI Users

1. **Basic Organization**
   ```bash
   alice
   ```

2. **Quality Pipeline**
   ```bash
   alice --quality --pipeline standard
   ```

3. **Continuous Monitoring**
   ```bash
   alice --watch --quality
   ```

## 📊 Key Concepts

### Organization Structure
```
organized/
└── 2024-01-28/          # Date
    └── project-name/    # Project
        └── midjourney/  # AI source
            ├── 5-star/  # Quality rating
            ├── 4-star/
            └── 3-star/
```

### Quality Ratings

| Stars | BRISQUE | Description |
|-------|---------|-------------|
| ⭐⭐⭐⭐⭐ | 0-25 | Exceptional |
| ⭐⭐⭐⭐ | 25-45 | Great |
| ⭐⭐⭐ | 45-65 | Good |
| ⭐⭐ | 65-80 | Fair |
| ⭐ | 80-100 | Poor |

### Pipeline Options

| Pipeline | Cost | Components |
|----------|------|------------|
| Basic | Free | BRISQUE only |
| Standard | ~$0.001 | + SightEngine |
| Premium | ~$0.003 | + Claude AI |

## 🎓 Learning Path

### New to Alice?

1. Start with [AI Conversations](ai-conversations.md) for natural interaction
2. Or jump to [CLI Usage](cli-usage.md) for traditional commands
3. Explore [Quality Assessment](quality-assessment.md) to understand ratings
4. Set up [API Keys](api-keys.md) for advanced features

### Ready for More?

- [Pipeline System](pipeline-system.md) - Advanced quality processing
- [Watch Mode](watch-mode.md) - Automated monitoring
- [fal.ai Provider](fal-provider.md) - Generate new content

## 💡 Best Practices

### For AI Usage
- Be descriptive in your requests
- Ask for clarification when needed
- Let the AI guide complex workflows
- Review AI actions before confirming

### For CLI Usage
- Start with dry runs (`--dry-run`)
- Use configuration files for consistency
- Monitor costs with pipeline limits
- Keep backups when using `--move`

## 🆘 Getting Help

### In AI Conversation
```
"Claude, how do I organize by quality?"
"Can you explain what star ratings mean?"
"Help me set up API keys"
```

### In CLI
```bash
alice --help
alice keys --help
alice interface --help
```

### Community
- [GitHub Issues](https://github.com/yourusername/AliceMultiverse/issues)
- [Discussions](https://github.com/yourusername/AliceMultiverse/discussions)
- [Contributing Guide](../../CONTRIBUTING.md)

---

<div align="center">

**Choose your path:** [AI Conversations](ai-conversations.md) 🤖 or [CLI Usage](cli-usage.md) 💻

</div>