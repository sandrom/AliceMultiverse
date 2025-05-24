# Claude Desktop Integration Setup

This guide explains how to integrate AliceMultiverse with Claude Desktop using MCP (Model Context Protocol).

## Prerequisites

1. Claude Desktop app installed
2. AliceMultiverse installed and configured
3. Python environment with AliceMultiverse dependencies

## Setup Steps

### 1. Locate Claude Desktop Config

The config file location depends on your OS:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Add Alice MCP Server Configuration

Edit the config file and add the Alice server:

```json
{
  "mcpServers": {
    "alice": {
      "command": "python",
      "args": ["-m", "alicemultiverse.cli", "mcp-server"],
      "cwd": "/path/to/AliceMultiverse",
      "env": {
        "PYTHONPATH": "/path/to/AliceMultiverse"
      }
    }
  }
}
```

**Important:** Adjust the `cwd` path to your AliceMultiverse directory.

### 3. Alternative: Use Direct Script

If the module approach doesn't work, create a wrapper script:

```bash
#!/usr/bin/env python3
# save as: alice-mcp-server.py
import sys
sys.path.insert(0, '/path/to/AliceMultiverse')
from alicemultiverse.mcp_server import main
main()
```

Then use this config:

```json
{
  "mcpServers": {
    "alice": {
      "command": "python",
      "args": ["/path/to/alice-mcp-server.py"]
    }
  }
}
```

### 4. Restart Claude Desktop

After saving the config, completely quit and restart Claude Desktop.

## Verifying the Integration

1. Open Claude Desktop
2. Look for the 🔌 icon in the input area
3. Click it to see available tools
4. You should see Alice tools like:
   - `search_assets`
   - `organize_media`
   - `tag_assets`
   - `find_similar_assets`

## Usage Examples

Once integrated, you can ask Claude:

- "Search for cyberpunk portraits in my media collection"
- "Organize my downloads folder and assess quality"
- "Find all 5-star hero shots from last week"
- "Show me images similar to asset abc123"

Claude will automatically use the Alice tools to fulfill these requests.

## Troubleshooting

### Server Not Appearing

1. Check Claude Desktop logs:
   - **macOS**: `~/Library/Logs/Claude/mcp.log`
   - **Windows**: `%LOCALAPPDATA%\Claude\logs\mcp.log`

2. Test the server manually:
   ```bash
   python -m alicemultiverse.cli mcp-server
   ```
   You should see startup messages.

### Import Errors

Make sure AliceMultiverse is installed:
```bash
cd /path/to/AliceMultiverse
pip install -e .
```

### Permission Errors

Ensure the Claude Desktop app has permission to access:
- Your Python installation
- The AliceMultiverse directory
- The media directories (inbox/organized)

## Advanced Configuration

### Environment Variables

You can pass configuration through environment variables:

```json
{
  "mcpServers": {
    "alice": {
      "command": "python",
      "args": ["-m", "alicemultiverse.cli", "mcp-server"],
      "env": {
        "ALICE_CONFIG": "~/.alicemultiverse/config.json",
        "ALICE_INBOX": "~/Pictures/AI-Generated",
        "ALICE_ORGANIZED": "~/Pictures/AI-Organized"
      }
    }
  }
}
```

### Multiple Instances

You can run multiple Alice instances for different projects:

```json
{
  "mcpServers": {
    "alice-personal": {
      "command": "python",
      "args": ["-m", "alicemultiverse.cli", "mcp-server"],
      "env": {
        "ALICE_CONFIG": "~/.alicemultiverse/personal.json"
      }
    },
    "alice-work": {
      "command": "python",
      "args": ["-m", "alicemultiverse.cli", "mcp-server"],
      "env": {
        "ALICE_CONFIG": "~/.alicemultiverse/work.json"
      }
    }
  }
}
```

## Security Notes

1. The MCP server only exposes Alice's high-level interface
2. No direct file system access is provided to Claude
3. API keys remain secure in your local configuration
4. File paths are never exposed in responses

## Next Steps

After setup, you can:
1. Ask Claude to organize your media
2. Search for specific styles or moods
3. Build collections for projects
4. Assess quality of your generated content

The integration allows natural conversation with Claude about your creative assets without dealing with technical details.