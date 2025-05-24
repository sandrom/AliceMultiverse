# Quick Start Guide

Get AliceMultiverse up and running in 5 minutes! This guide covers the essential steps to start organizing your AI-generated media.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- 500MB free disk space
- macOS, Linux, or Windows

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/AliceMultiverse.git
cd AliceMultiverse
```

### 2. Install as Package (Recommended)

```bash
# Install with all features
pip install -e ".[quality,secure,premium]"

# Or minimal install
pip install -e .
```

### 3. Verify Installation

```bash
alice --version
# Output: AliceMultiverse v1.4.0
```

## Your First Organization

### 1. Prepare Your Media

Create a simple folder structure:

```
inbox/
└── my-project/
    ├── image1_midjourney.png
    ├── image2_dalle3.jpg
    └── video_runway_gen2.mp4
```

### 2. Run Basic Organization

```bash
# Use default folders from settings.yaml
alice

# Or specify folders
alice -i inbox -o organized
```

This will create:

```
organized/
└── 2024-03-15/
    └── my-project/
        ├── midjourney/
        │   └── my-project-00001.png
        ├── dalle/
        │   └── my-project-00001.jpg
        └── runway/
            └── my-project-00001.mp4
```

### 3. Add Quality Assessment

```bash
alice --quality
```

This creates star-rating folders based on BRISQUE scores:

```
organized/
└── 2024-03-15/
    └── my-project/
        └── midjourney/
            ├── 5-star/
            │   └── my-project-00001.png
            └── 4-star/
                └── my-project-00002.png
```

## Common Workflows

### Dry Run (Preview)

See what would happen without making changes:

```bash
alice --dry-run
```

### Watch Mode

Continuously monitor for new files:

```bash
alice --watch
# Press Ctrl+C to stop
```

### Move Instead of Copy

```bash
alice --move
```

### Force Re-analysis

Bypass cache and re-analyze all files:

```bash
alice --force-reindex
```

### Pipeline Processing

Use advanced quality assessment with external APIs:

```bash
# BRISQUE only (free, local)
alice --pipeline brisque

# BRISQUE + SightEngine (~$0.001/image)
alice --pipeline brisque-sightengine

# BRISQUE + Claude (~$0.002/image)
alice --pipeline brisque-claude

# Full pipeline (~$0.003/image)
alice --pipeline brisque-sightengine-claude
```

## Understanding the Output

After organization, you'll see a summary:

```
==================================================
Organization Summary:
  Total files processed: 150
  Successfully organized: 145
  Duplicates skipped: 3
  Errors: 2

By AI Source:
  midjourney: 80
  stable-diffusion: 45
  dalle: 20

Quality Assessment:
  Images assessed: 145
  Distribution:
    5-star: 23 (15.9%)
    4-star: 67 (46.2%)
    3-star: 38 (26.2%)
    2-star: 12 (8.3%)
    1-star: 5 (3.4%)
==================================================
```

## Quick Tips

### 1. Project Folders Matter
Keep your creative projects in separate folders - AliceMultiverse preserves this organization.

### 2. Filename Patterns
Include AI tool names in filenames for better detection:
- ✅ `landscape_midjourney_v5.png`
- ✅ `portrait_sd_xl.jpg`
- ❌ `image001.png` (generic, harder to detect)

### 3. Check Quality Settings
Default BRISQUE thresholds work well, but you can adjust in `settings.yaml`:

```yaml
quality:
  thresholds:
    5_star: {min: 0, max: 20}    # Exceptional
    4_star: {min: 20, max: 40}   # Great
    3_star: {min: 40, max: 60}   # Good
    2_star: {min: 60, max: 80}   # Fair
    1_star: {min: 80, max: 100}  # Poor
```

### 4. Performance Tips
- First run is slower (building cache)
- Subsequent runs are 70-80% faster
- Use `--quality` selectively for large collections

## What's Next?

- 📊 [Pipeline Examples](../user-guide/pipeline-examples.md) - Choose the right pipeline for your needs
- 🔑 [Configure API Keys](../user-guide/api-keys.md) - Set up SightEngine and Claude
- 🤖 [Claude Integration](../user-guide/claude-integration.md) - AI-powered defect detection
- 📚 [Read the User Guide](../user-guide/index.md) - Detailed features and workflows
- 🎓 [Try the Tutorials](../tutorials/index.md) - Step-by-step guides

## Troubleshooting

### Common Issues

**"No media files found"**
- Check that your files have supported extensions
- Ensure files are in project subdirectories, not inbox root

**"BRISQUE not available"**
```bash
pip install image-quality
# or
pip install pybrisque
```

**"Permission denied"**
- Check file permissions
- Run with appropriate user privileges

**Quality scores seem wrong**
- BRISQUE works best on natural images
- Stylized/artistic content may score lower
- Consider adjusting thresholds

### Getting Help

- Check the [FAQ](../user-guide/faq.md)
- Read [detailed documentation](../user-guide/index.md)
- Open an issue on [GitHub](https://github.com/yourusername/AliceMultiverse)

## Command Reference

```bash
# Basic usage
alice [options]
# Or specify input directly as positional argument
alice <input> [options]

# Key options
-i, --input DIR       # Input directory (default: inbox/)
-o, --output DIR      # Output directory (default: organized/)
--quality            # Enable quality assessment
--pipeline TYPE      # Use pipeline (brisque, brisque-sightengine, brisque-claude, brisque-sightengine-claude)
--watch, -w          # Watch mode
--move               # Move files instead of copy
--dry-run            # Preview without changes
--force-reindex      # Bypass cache
--config FILE        # Use custom config file
--verbose, -v        # Detailed output
--quiet, -q          # Minimal output

# API Key options
--sightengine-key USER,SECRET  # SightEngine API credentials
--anthropic-key KEY            # Anthropic API key for Claude

# Examples
alice                                    # Use defaults from settings.yaml
alice --quality                          # Basic quality assessment
alice --pipeline brisque-claude          # BRISQUE + Claude analysis
alice -i ~/Pictures/AI -o ~/Organized   # Custom directories
alice --watch --move                     # Watch mode with file moving
```