# Practical AI Integration Options for AliceMultiverse

You're right - we need a concrete way for AI assistants to actually call Alice functions. Here are the main options:

## Option 1: MCP Server (Model Context Protocol)

Despite the spec saying "Alice is the sole orchestrator", an MCP server makes sense here because it would expose **Alice's interface**, not the underlying tools.

### Implementation:

```python
# alice_mcp_server.py
from mcp import Server, Tool
from alicemultiverse.interface import AliceInterface

server = Server("alice-multiverse")
alice = AliceInterface()

@server.tool()
async def search_assets(
    description: str = None,
    style_tags: list[str] = None,
    mood_tags: list[str] = None,
    subject_tags: list[str] = None,
    min_quality_stars: int = None,
    limit: int = 20
) -> dict:
    """Search for assets using creative concepts."""
    request = {
        "description": description,
        "style_tags": style_tags,
        "mood_tags": mood_tags,
        "subject_tags": subject_tags,
        "min_quality_stars": min_quality_stars,
        "limit": limit
    }
    return alice.search_assets(request)

@server.tool()
async def organize_media(
    source_path: str = None,
    quality_assessment: bool = True,
    enhanced_metadata: bool = True,
    pipeline: str = "standard"
) -> dict:
    """Organize and assess media files."""
    request = {
        "source_path": source_path,
        "quality_assessment": quality_assessment,
        "enhanced_metadata": enhanced_metadata,
        "pipeline": pipeline
    }
    return alice.organize_media(request)

# More tools...

if __name__ == "__main__":
    server.run()
```

### Usage with Claude Desktop:
```json
{
  "mcpServers": {
    "alice": {
      "command": "python",
      "args": ["/path/to/alice_mcp_server.py"]
    }
  }
}
```

## Option 2: REST API Server

A simple HTTP API that any AI system can call through web requests.

```python
# alice_api_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from alicemultiverse.interface import AliceInterface

app = FastAPI(title="AliceMultiverse API")
alice = AliceInterface()

class SearchRequest(BaseModel):
    description: str = None
    style_tags: list[str] = None
    mood_tags: list[str] = None
    subject_tags: list[str] = None
    min_quality_stars: int = None
    limit: int = 20

@app.post("/search")
async def search_assets(request: SearchRequest):
    """Search for assets."""
    try:
        response = alice.search_assets(request.dict())
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/organize")
async def organize_media(request: OrganizeRequest):
    """Organize media files."""
    try:
        response = alice.organize_media(request.dict())
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn alice_api_server:app --host 0.0.0.0 --port 8000
```

### AI Integration:
```python
# For AI assistants that can make HTTP requests
response = requests.post(
    "http://localhost:8000/search",
    json={
        "description": "cyberpunk portraits",
        "min_quality_stars": 4
    }
)
```

## Option 3: Custom Tool Integration

For AI platforms that support custom tools (like OpenAI Assistants API).

```python
# alice_openai_tools.py
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_assets",
            "description": "Search for creative assets using Alice",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Natural language search query"
                    },
                    "style_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Style tags like 'cyberpunk', 'minimalist'"
                    },
                    "mood_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Mood tags like 'energetic', 'calm'"
                    },
                    "min_quality_stars": {
                        "type": "integer",
                        "description": "Minimum quality rating (1-5)"
                    }
                }
            }
        }
    }
    # More tool definitions...
]

# Handler for when the AI calls the tool
def handle_tool_call(tool_name, arguments):
    if tool_name == "search_assets":
        return alice.search_assets(arguments)
    elif tool_name == "organize_media":
        return alice.organize_media(arguments)
    # etc...
```

## Option 4: CLI Integration via Subprocess

For simpler integrations where AI can run commands.

```python
# alice_cli_wrapper.py
import subprocess
import json

def call_alice(command, **kwargs):
    """Call Alice via CLI and return parsed result."""
    cmd = ["alice", "api", command]
    
    # Add arguments
    for key, value in kwargs.items():
        if value is not None:
            cmd.extend([f"--{key}", json.dumps(value)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# AI can then use:
results = call_alice("search", 
    description="cyberpunk portraits",
    min_quality_stars=4
)
```

## Option 5: Python Package Integration

For AI systems that can import Python packages directly.

```python
# Direct import (if AI has access to Python environment)
from alicemultiverse.interface import AliceInterface

alice = AliceInterface()

# AI can directly call:
response = alice.search_assets({
    "description": "cyberpunk portraits",
    "min_quality_stars": 4
})
```

## Recommended Approach: Hybrid Solution

Given your spec and practical needs, I recommend:

### 1. **Primary: MCP Server for Alice**
```python
# alice_mcp_server.py
"""
This MCP server exposes ALICE's interface, not the underlying tools.
This aligns with your spec - AI talks to Alice, Alice talks to tools.
"""
from mcp import Server, Tool
from alicemultiverse.interface import AliceInterface

server = Server("alice")
alice = AliceInterface()

# Expose only high-level Alice functions
# No direct file access, no API keys, just creative operations
```

### 2. **Secondary: REST API for Web Integration**
- For web-based AI assistants
- For testing and debugging
- For future web UI integration

### 3. **CLI API Command for Quick Testing**
```bash
# Add to your CLI
alice api search --description "cyberpunk portraits"
alice api organize --source ~/Downloads --quality
alice api tag --assets id1,id2,id3 --role hero
```

## Implementation Priority

1. **Start with MCP Server** - It's the most direct integration for Claude Desktop
2. **Add REST API** - For broader compatibility
3. **CLI API mode** - For testing and scripting
4. **Document webhook patterns** - For event-driven workflows

## Example MCP Server Config

```json
{
  "mcpServers": {
    "alice": {
      "command": "python",
      "args": ["-m", "alicemultiverse.mcp_server"],
      "env": {
        "ALICE_CONFIG": "~/.alicemultiverse/config.json"
      }
    }
  }
}
```

The key insight: The MCP server would BE Alice's interface layer, not a bypass of it. It's just the transport mechanism for AI to call Alice functions.