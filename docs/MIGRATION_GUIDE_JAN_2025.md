# Migration Guide - January 2025 Release

## Overview

This guide helps you upgrade to the January 2025 release of AliceMultiverse, which adds prompt management, video transitions, and Veo 3 support.

## Before You Update

### 1. Backup Your Data
```bash
# Backup your metadata and settings
cp -r ~/.alice ~/.alice.backup.2025
cp settings.yaml settings.yaml.backup
```

### 2. Check Your Environment
```bash
# Ensure Python 3.12+
python --version

# Ensure ffmpeg is installed
ffmpeg -version

# Check available disk space (need ~500MB)
df -h ~/
```

## Update Process

### 1. Update the Code
```bash
# If using git
git pull origin main

# Reinstall with new dependencies
pip install -e .
```

### 2. Update API Keys
```bash
# Add new keys if using Veo 3
export FAL_KEY="your-fal-api-key"

# Or use the setup wizard
alice keys setup
```

### 3. Update Claude Desktop Config

Add the new tools to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "alice": {
      "command": "alice",
      "args": ["mcp-server"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Then restart Claude Desktop.

## New Features Setup

### 1. Prompt Management

The prompt system will automatically initialize on first use:

```bash
# Test prompt search
alice prompts search "test"

# This creates:
# ~/.alice/prompts.duckdb - Search index
# ~/.alice/prompts/ - YAML storage
```

### 2. Video Transitions

Transition tools are ready to use immediately:

```bash
# Test transition analysis
alice transitions --help

# Available commands:
# - alice transitions morph
# - alice transitions colorflow
# - alice transitions matchcuts
# - alice transitions portal
# - alice transitions rhythm
```

### 3. Google Veo 3

To use Veo 3, ensure you have a fal.ai API key:

```bash
# Set API key
export FAL_KEY="your-key"

# Test Veo 3
python examples/advanced/veo3_example.py
```

## Configuration Changes

### New Settings

Add these to your `settings.yaml` if you want to customize:

```yaml
# Prompt management settings
prompts:
  track_effectiveness: true
  min_success_for_suggestion: 0.8
  
# Transition settings  
transitions:
  default_threshold: 0.7
  export_format: after_effects
  
# Video generation
video:
  default_duration: 5
  default_aspect_ratio: "16:9"
  veo3_enable_audio: false
```

### Deprecated Settings

None. All existing settings remain valid.

## Data Migration

### Existing Projects

Your existing projects are unaffected. To add prompts to existing projects:

```bash
# Create prompts for a project
mkdir -p projects/my_project/.prompts

# Prompts will be automatically indexed
```

### Search Index

If you have existing metadata, rebuild the search index to include new fields:

```bash
# Rebuild search index with new capabilities
alice index rebuild

# This updates the index with:
# - Prompt search support
# - Enhanced tag hierarchies
# - Transition metadata
```

## Breaking Changes

**None!** This release is fully backward compatible.

## Common Issues

### 1. "Module not found" Errors

```bash
# Reinstall in development mode
pip install -e .
```

### 2. Claude Desktop Not Showing New Tools

1. Restart Claude Desktop completely
2. Check the configuration file is valid JSON
3. Verify `alice mcp-server` runs without errors

### 3. Veo 3 Not Working

```bash
# Check fal.ai key is set
echo $FAL_KEY

# Test fal.ai connection
python -c "from alicemultiverse.providers.fal_provider import FalProvider; print('OK')"
```

## Performance Notes

### Storage Impact
- Prompt database: ~10-50MB depending on usage
- Transition cache: ~1MB per 100 images analyzed
- No impact on existing image storage

### Memory Usage
- Transition analysis: +200-500MB during processing
- Prompt search: Negligible (<50MB)
- Veo 3 generation: Standard for video operations

## Rollback Procedure

If you need to rollback:

```bash
# 1. Restore backup
mv ~/.alice ~/.alice.new
mv ~/.alice.backup.2025 ~/.alice

# 2. Checkout previous version
git checkout <previous-commit>

# 3. Reinstall
pip install -e .
```

## Getting Help

### Quick Checks
1. Run `alice --version` to verify installation
2. Check `~/.alice/alice.log` for errors
3. Run `alice prompts search test` to verify prompt system
4. Try `alice transitions --help` for transition tools

### Support Resources
- GitHub Issues for bugs
- `/docs/TROUBLESHOOTING.md` for common problems
- Examples in `/examples/advanced/`

## What's Next

After updating:

1. **Explore Prompt Management**
   ```bash
   alice prompts --help
   ```

2. **Try Video Transitions**
   ```bash
   alice transitions matchcuts examples/images/*.jpg
   ```

3. **Generate with Veo 3**
   ```
   In Claude: "Generate a 5-second video of sunset with sound using Veo 3"
   ```

4. **Read the Guides**
   - `/docs/user-guide/prompt-management-guide.md`
   - `/docs/user-guide/veo3-video-generation-guide.md`
   - `/docs/QUICK_REFERENCE_2025.md`

---

**Migration Status Checklist**

- [ ] Code updated
- [ ] Dependencies installed
- [ ] API keys configured
- [ ] Claude Desktop restarted
- [ ] Test command successful
- [ ] Ready to use new features!

Welcome to the most powerful version of AliceMultiverse yet! 🎉