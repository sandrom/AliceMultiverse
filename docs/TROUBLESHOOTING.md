# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### ImportError: No module named 'alicemultiverse'
**Problem**: Python can't find the AliceMultiverse module.

**Solution**:
```bash
# Reinstall in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### ffmpeg not found
**Problem**: Video features require ffmpeg.

**Solution**:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

### API Key Issues

#### "No API key provided" errors
**Problem**: API keys not configured properly.

**Solution**:
```bash
# Run interactive setup
alice keys setup

# Or set environment variables
export FAL_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# Verify keys are set
alice keys list
```

#### "Invalid API key" errors
**Problem**: API key is incorrect or expired.

**Solution**:
1. Check key validity on provider's dashboard
2. Regenerate key if needed
3. Update using `alice keys setup`
4. Restart Claude Desktop if using MCP

### MCP (Claude Desktop) Issues

#### "MCP server not responding"
**Problem**: Claude can't connect to AliceMultiverse.

**Solution**:
1. Check Claude Desktop config:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Verify alice is in PATH:
   ```bash
   which alice
   ```

3. Test MCP server directly:
   ```bash
   alice mcp-server
   ```

4. Restart Claude Desktop

#### "Tool execution failed"
**Problem**: MCP tool errors in Claude.

**Solution**:
1. Check alice.log for detailed errors:
   ```bash
   tail -f ~/.alice/alice.log
   ```

2. Verify permissions for file access
3. Check if paths exist
4. Ensure API keys are configured

### Search Issues

#### "No results found"
**Problem**: Search returns empty results.

**Solution**:
```bash
# Rebuild search index
alice index rebuild

# Check if files are indexed
alice search "*" --limit 10

# Verify database exists
ls -la ~/.alice/search.duckdb
```

#### "Search is slow"
**Problem**: Searches taking too long.

**Solution**:
1. Check index size:
   ```bash
   alice storage stats
   ```

2. Optimize for large collections:
   ```bash
   # Limit search scope
   alice search "query" --path specific/folder
   
   # Use more specific queries
   alice search "cyberpunk AND portrait" --limit 20
   ```

### Prompt Management Issues

#### "Prompts not saving"
**Problem**: Prompts aren't being stored.

**Solution**:
```bash
# Check prompt directory
ls -la ~/.alice/prompts/

# Rebuild prompt index
alice prompts reindex

# Verify database
ls -la ~/.alice/prompts.duckdb
```

#### "Can't find effective prompts"
**Problem**: Effectiveness tracking not working.

**Solution**:
1. Ensure usage is being tracked:
   ```python
   # Track manually
   alice prompts track <prompt_id> --success --cost 0.05
   ```

2. Check if provider integration is enabled in settings.yaml

### Video Generation Issues

#### "Video generation failed"
**Problem**: Video generation errors.

**Solution**:
1. Check API limits:
   ```bash
   alice cost report
   ```

2. Verify model name:
   ```bash
   # Use correct model
   alice generate video --model veo-3  # not "veo3" or "veo-3.0"
   ```

3. Check file size limits (Veo 3: max 20MB for image-to-video)

4. Monitor provider status:
   ```bash
   alice providers health
   ```

#### "No audio in video"
**Problem**: Veo 3 video has no sound.

**Solution**:
```python
# Enable audio explicitly
alice generate video --model veo-3 --audio

# Or in code
parameters={"enable_audio": True}
```

### Transition Analysis Issues

#### "No transitions detected"
**Problem**: Transition tools find no matches.

**Solution**:
```bash
# Lower threshold
alice transitions matchcuts *.jpg -t 0.5  # default is 0.7

# Check image quality
# - Ensure images are high resolution
# - Verify clear shapes/motion
# - Use sequential frames
```

#### "Transition export not working"
**Problem**: Can't export to editing software.

**Solution**:
1. Check output format:
   ```bash
   # After Effects
   alice transitions portal shot1.jpg shot2.jpg -f after_effects
   
   # EDL
   alice transitions matchcuts *.jpg -f edl
   ```

2. Verify file permissions for output directory

### Performance Issues

#### "High memory usage"
**Problem**: AliceMultiverse using too much RAM.

**Solution**:
1. Process images in batches:
   ```bash
   # Limit batch size
   alice organize --batch-size 50
   ```

2. Reduce image resolution for analysis:
   ```bash
   # Resize for processing
   alice understand --max-size 1024
   ```

3. Clear caches:
   ```bash
   rm -rf ~/.alice/cache/*
   ```

#### "Slow processing"
**Problem**: Operations taking too long.

**Solution**:
1. Enable progress bars to see what's slow:
   ```bash
   alice organize --progress
   ```

2. Use local providers when possible:
   ```bash
   # Use Ollama for free local analysis
   alice understand --providers ollama
   ```

3. Disable unnecessary features:
   ```yaml
   # settings.yaml
   understanding:
     enabled: false  # If not needed
   ```

### Cost Issues

#### "Exceeded budget"
**Problem**: API costs too high.

**Solution**:
```bash
# Set strict budgets
alice cost set-budget --daily 5 --monthly 100

# Use cost-effective providers
alice understand --providers google  # Free tier

# Preview costs
alice generate video --model veo-3 --dry-run
```

#### "Cost tracking not working"
**Problem**: Costs not being recorded.

**Solution**:
1. Check cost tracking is enabled:
   ```yaml
   # settings.yaml
   cost_tracking:
     enabled: true
   ```

2. Manually log costs:
   ```bash
   alice cost log --provider fal --amount 2.50
   ```

### Database Issues

#### "Database locked"
**Problem**: DuckDB lock errors.

**Solution**:
```bash
# Remove lock files
rm ~/.alice/*.duckdb.wal
rm ~/.alice/*.duckdb.lock

# Rebuild if corrupted
alice index rebuild --force
```

#### "Database corrupted"
**Problem**: Can't read database files.

**Solution**:
```bash
# Backup and recreate
mv ~/.alice/search.duckdb ~/.alice/search.duckdb.backup
alice index rebuild

mv ~/.alice/prompts.duckdb ~/.alice/prompts.duckdb.backup
alice prompts reindex
```

## Getting Help

### Logs
Always check logs first:
```bash
# Main log
tail -f ~/.alice/alice.log

# Event logs
tail -f ~/.alice/events/$(date +%Y-%m-%d).json
```

### Debug Mode
Run commands with debug flag:
```bash
alice --debug organize
alice --debug transitions matchcuts *.jpg
```

### Version Info
Include version when reporting issues:
```bash
alice --version
python --version
ffmpeg -version
```

### Community Support
- GitHub Issues: Bug reports
- Discussions: Questions
- Wiki: Community solutions

## Emergency Recovery

If everything is broken:

```bash
# 1. Backup current state
cp -r ~/.alice ~/.alice.backup

# 2. Reset to clean state
rm -rf ~/.alice

# 3. Reinstall
pip uninstall alicemultiverse
pip install -e .

# 4. Reconfigure
alice setup
alice keys setup

# 5. Rebuild indices
alice index rebuild
alice prompts reindex
```

---

Remember: Most issues are related to:
1. Missing API keys
2. Incorrect paths
3. Rate limits
4. Missing dependencies

Check these first before diving deeper!