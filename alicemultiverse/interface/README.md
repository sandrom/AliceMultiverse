# Interface Module Guide

This module provides different ways to interact with AliceMultiverse:

## For Users

### `main_cli.py`
The command-line interface (`alice` command). This is what most users need.

## For Developers

### Core Interfaces (Choose based on your needs)
- **`alice_orchestrator.py`** - Natural language interface for AI assistants
- **`alice_interface.py`** - Traditional programmatic API with methods
- **`alice_api.py`** - Simplified wrapper with one method

### Supporting Files
- **`cli_handler.py`** - CLI implementation details
- **`models.py`** - Data structures for API requests/responses
- **`creative_models.py`** - Domain models for creative workflows
- **`mcp_server.py`** - Model Context Protocol server for Claude Desktop
- **`asset_processor_client.py`** - Client for microservice architecture (future)

## Which Should You Use?

1. **Command line user?** → You're already using `main_cli.py` via the `alice` command
2. **Building an app?** → Start with `alice_api.py` (simplest)
3. **Need full control?** → Use `alice_interface.py`
4. **AI integration?** → Use `alice_orchestrator.py`

See [Interface Selection Guide](../../docs/INTERFACE_GUIDE.md) for detailed comparison.