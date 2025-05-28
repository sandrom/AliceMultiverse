# Debug CLI Reference

> **⚠️ DEPRECATED**: Direct CLI usage is deprecated. Alice is now an AI-native service designed to be used through AI assistants like Claude. This CLI reference is maintained for debugging and development purposes only.

## For Normal Users

**Please use Alice through an AI assistant:**

1. [Set up Claude Desktop integration](../integrations/claude-desktop.md)
2. Chat naturally: "Claude, organize my AI images"
3. Let the AI handle the complexity

## For Developers/Debugging

The CLI is maintained for debugging and development workflows only.

### Enabling Debug Mode

All CLI commands (except `mcp-server`, `keys`, and `interface`) now require the `--debug` flag:

```bash
# This will show deprecation warning and exit
alice --dry-run

# This will work (debug mode)
alice --debug --dry-run
```

### Debug Commands

#### System Check
```bash
# Check dependencies
alice --check-deps

# Verbose system info
alice --debug --verbose --dry-run
```

#### Dry Run Testing
```bash
# Test organization logic
alice --debug --dry-run

# Test with specific paths
alice --debug --dry-run --inbox ~/test-input --organized ~/test-output

# Test pipeline logic
alice --debug --dry-run --pipeline premium --verbose
```

#### Force CLI Usage
```bash
# Skip deprecation warning entirely (not recommended)
alice --force-cli

# Better: use debug mode
alice --debug
```

### Still-Supported Commands

These commands work without --debug flag:

#### MCP Server
```bash
# Start MCP server for AI integration
alice mcp-server
```

#### API Key Management
```bash
# Interactive setup wizard
alice keys setup

# Set specific key
alice keys set anthropic_api_key

# List configured keys
alice keys list

# Delete a key
alice keys delete sightengine_user
```

#### Interface Testing
```bash
# Test AI interface locally
alice interface

# Test structured interface
alice interface --structured
```

### Debug Options

| Flag | Purpose |
|------|---------|
| `--debug` | Enable debug mode (required for most commands) |
| `--verbose` / `-v` | Show detailed output |
| `--dry-run` / `-n` | Preview without changes |
| `--force-cli` | Skip deprecation warning |
| `--log-file` | Write logs to file |
| `--check-deps` | Verify system dependencies |

### Configuration Debugging

#### Check Configuration
```bash
# See what configuration would be used
alice --debug --dry-run --verbose
```

#### Override Configuration
```bash
# Test with different settings
alice --debug --paths.inbox=/tmp/test --dry-run
```

### Troubleshooting Workflows

#### Debug Organization Issues
```bash
# 1. Check file detection
alice --debug --dry-run --verbose --inbox ~/problem-folder

# 2. Force reindexing
alice --debug --force-reindex --dry-run

# 3. Check specific pipeline stage
alice --debug --pipeline custom --stages brisque --verbose
```

#### Debug Quality Assessment
```bash
# Test BRISQUE only
alice --debug --pipeline basic --quality --dry-run

# Check scoring weights
alice --debug --pipeline.scoring_weights.standard.brisque=1.0 --dry-run
```

### Development Workflows

#### Testing Changes
```bash
# After code changes
alice --debug --force-reindex --dry-run --verbose

# Test error handling
alice --debug --inbox /nonexistent/path
```

#### Performance Profiling
```bash
# Time operations
time alice --debug --dry-run

# Check cache performance
alice --debug --verbose 2>&1 | grep -i cache
```

## Migration Notice

**Why the change?**
- Zero learning curve for users
- Natural language is more intuitive
- AI can handle complex workflows better
- Reduces user errors and confusion

**What if I need the CLI?**
- Use `--debug` flag for development
- Consider if your use case could work better through AI
- Open an issue if you have a legitimate need for CLI access

**For automation/scripts:**
Consider using the Python API directly instead of the CLI:

```python
from alicemultiverse.interface import AliceInterface

alice = AliceInterface()
response = alice.organize_media(request)
```

---

**Remember**: Alice is designed for AI-first interaction. The debug CLI is a development tool, not the intended user interface.