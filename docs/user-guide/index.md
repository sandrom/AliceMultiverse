# User Guide

Welcome to the AliceMultiverse User Guide! This comprehensive guide covers all features and workflows for organizing your AI-generated media.

## Guide Overview

<div class="grid cards" markdown>

- **[Basic Usage](basic-usage.md)**
    
    Learn the fundamental commands and workflows

- **[Quality Assessment](quality-assessment.md)**
    
    Understanding BRISQUE scores and star ratings

- **[Watch Mode](watch-mode.md)**
    
    Continuous monitoring for new files

- **[Pipeline System](pipeline-system.md)**
    
    Multi-stage quality assessment

- **[API Keys](api-keys.md)**
    
    Setting up and managing API credentials

</div>

## What You'll Learn

### 🎯 Core Concepts

1. **File Organization** - How AliceMultiverse structures your media
2. **AI Detection** - How sources are identified
3. **Quality Metrics** - Understanding scores and ratings
4. **Caching System** - How performance optimization works

### 🛠️ Practical Skills

1. **Running Organizations** - Basic and advanced commands
2. **Configuring Quality** - Adjusting thresholds
3. **Setting Up Pipelines** - Cost-effective processing
4. **Managing API Keys** - Secure credential storage

### 📊 Advanced Features

1. **Custom Pipelines** - Building your own stages
2. **Batch Processing** - Handling large collections
3. **Performance Tuning** - Optimizing for speed
4. **Integration Options** - Using as a Python library

## Typical Workflows

### 1. First-Time User

```mermaid
graph LR
    A[Install] --> B[Configure]
    B --> C[Basic Organize]
    C --> D[Add Quality]
    D --> E[Try Pipeline]
```

1. Start with [Basic Usage](basic-usage.md)
2. Try quality assessment
3. Set up API keys if needed
4. Explore advanced features

### 2. Regular Organization

```mermaid
graph LR
    A[New Media] --> B[Watch Mode]
    B --> C[Auto Organize]
    C --> D[Quality Sort]
    D --> A
```

1. Keep watch mode running
2. Drop files into inbox
3. Review organized output
4. Adjust settings as needed

### 3. Large Collection Processing

```mermaid
graph LR
    A[Collection] --> B[Dry Run]
    B --> C[Adjust Config]
    C --> D[Process]
    D --> E[Verify]
```

1. Preview with dry run
2. Tune quality thresholds
3. Run with appropriate pipeline
4. Verify results

## Key Concepts

### Organization Structure

```
organized/
└── 2024-03-15/          # Date
    └── project-name/    # Your project
        └── midjourney/  # AI source
            └── 5-star/  # Quality rating
```

### Quality Ratings

| Stars | BRISQUE Score | Description |
|-------|--------------|-------------|
| ⭐⭐⭐⭐⭐ | 0-25 | Exceptional quality |
| ⭐⭐⭐⭐ | 25-45 | Great quality |
| ⭐⭐⭐ | 45-65 | Good quality |
| ⭐⭐ | 65-80 | Fair quality |
| ⭐ | 80-100 | Poor quality |

### Pipeline Stages

<div class="pipeline-stages">
<span class="pipeline-stage free">BRISQUE (Free)</span>
→
<span class="pipeline-stage cheap">SightEngine (~$0.001)</span>
→
<span class="pipeline-stage premium">Claude (~$0.02)</span>
</div>

## Quick Reference

### Essential Commands

```bash
# Basic organization (uses defaults from settings.yaml)
alice

# With quality assessment
alice --quality

# Watch mode
alice --watch

# Pipeline processing (4 options)
alice --pipeline brisque                     # BRISQUE only (free)
alice --pipeline brisque-sightengine         # BRISQUE + SightEngine (~$0.001/image)
alice --pipeline brisque-claude              # BRISQUE + Claude (~$0.02/image)
alice --pipeline brisque-sightengine-claude  # All three (~$0.021/image)

# Dry run preview
alice --dry-run
```

### Common Options

| Option | Short | Description |
|--------|-------|-------------|
| `--quality` | `-q` | Enable quality assessment |
| `--watch` | `-w` | Watch mode |
| `--move` | `-m` | Move instead of copy |
| `--dry-run` | `-n` | Preview only |
| `--force-reindex` | `-f` | Bypass cache |

## Getting Help

### In Documentation

- Use the search function (top of page)
- Check the table of contents (left sidebar)
- Browse related topics (bottom of page)

### In Application

```bash
# General help
alice --help

# Command-specific help
alice organize --help
alice keys setup --help
```

### Community

- GitHub Issues for bugs
- Discussions for questions
- Pull requests for contributions

## Best Practices

### 1. Start Simple
Begin with basic organization before adding quality assessment or pipelines.

### 2. Use Dry Runs
Always preview large operations with `--dry-run` first.

### 3. Monitor Costs
Check pipeline costs before processing large collections.

### 4. Regular Backups
Keep backups of your original files, especially when using `--move`.

### 5. Cache Wisely
Let the cache work for you - avoid `--force-reindex` unless necessary.

## Next Steps

Ready to start? Here's your learning path:

1. **[Basic Usage](basic-usage.md)** - Master the fundamentals
2. **[Quality Assessment](quality-assessment.md)** - Understand quality metrics
3. **[API Keys](api-keys.md)** - Set up external services
4. **[Pipeline System](pipeline-system.md)** - Advanced processing

---

<div align="center">

**Need help?** Check our [FAQ](faq.md) or [open an issue](https://github.com/yourusername/AliceMultiverse/issues)

</div>