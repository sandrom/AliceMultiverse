# Interface Selection Guide

## Which Interface Should I Use?

AliceMultiverse provides multiple interfaces to suit different use cases. This guide helps you choose the right one.

## Quick Decision Tree

```
Are you...
│
├─ Using the command line?
│  └─► Use `alice` command
│
├─ Writing a Python script?
│  ├─ Need natural language interaction?
│  │  └─► Use `AliceOrchestrator`
│  └─ Need structured API calls?
│     └─► Use `AliceInterface`
│
├─ Building an application?
│  ├─ Want simplest integration?
│  │  └─► Use `AliceAPI`
│  └─ Need full control?
│     └─► Use `AliceInterface`
│
└─ Creating an AI assistant integration?
   └─► Use `AliceOrchestrator` or MCP Server
```

## Detailed Interface Comparison

### 1. Command Line Interface (`alice`)

**Best for:**
- Manual organization tasks
- Scheduled jobs (cron)
- Shell scripts
- Quick one-off operations

**Example:**
```bash
alice --inbox ~/Downloads --quality --watch
```

**Features:**
- ✅ No programming required
- ✅ Progress indicators
- ✅ Watch mode
- ❌ Limited to predefined operations

### 2. AliceAPI (Simplest Python Interface)

**Best for:**
- Chat interfaces
- Quick prototypes
- Simple integrations
- When you want Alice to figure out the details

**Example:**
```python
from alicemultiverse.interface import AliceAPI

alice = AliceAPI()
response = alice.request("organize my downloads folder with quality assessment")
print(response.message)
```

**Features:**
- ✅ Single method interface
- ✅ Natural language input
- ✅ Minimal code required
- ❌ Less control over specifics

### 3. AliceOrchestrator (Natural Language Interface)

**Best for:**
- AI assistant integrations
- Creative workflows
- Complex queries
- When context matters

**Example:**
```python
from alicemultiverse.interface import AliceOrchestrator

alice = AliceOrchestrator()
response = alice.process_request({
    "intent": "search",
    "query": "find cyberpunk images from last week rated 4 stars or higher",
    "context": {"project": "neon-dreams"}
})
```

**Features:**
- ✅ Natural language understanding
- ✅ Context awareness
- ✅ Creative workflow support
- ✅ Memory of past interactions
- ❌ More complex than AliceAPI

### 4. AliceInterface (Structured API)

**Best for:**
- Traditional applications
- When you need precise control
- Type-safe integrations
- Building services

**Example:**
```python
from alicemultiverse.interface import AliceInterface

alice = AliceInterface()
results = alice.search_assets({
    "style_tags": ["cyberpunk"],
    "min_quality_stars": 4,
    "time_reference": "last week"
})
```

**Features:**
- ✅ Explicit methods for each operation
- ✅ Type-safe with TypedDict
- ✅ Full control over parameters
- ✅ Predictable behavior
- ❌ More verbose code

### 5. Direct MediaOrganizer

**Best for:**
- Custom workflows
- Extending functionality
- Understanding internals
- Maximum control

**Example:**
```python
from alicemultiverse.organizer import MediaOrganizer
from alicemultiverse.core.config import load_config

config = load_config()
organizer = MediaOrganizer(config)
organizer.organize()
```

**Features:**
- ✅ Complete control
- ✅ Access to internals
- ✅ Can extend/override behavior
- ❌ Requires understanding of internals
- ❌ More code required

## Integration Examples

### Web API Backend
```python
# Use AliceInterface for structured endpoints
from fastapi import FastAPI
from alicemultiverse.interface import AliceInterface

app = FastAPI()
alice = AliceInterface()

@app.post("/search")
def search(request: SearchRequest):
    return alice.search_assets(request)
```

### Chatbot Integration
```python
# Use AliceAPI for simple chat commands
from alicemultiverse.interface import AliceAPI

alice = AliceAPI()

def handle_message(user_message):
    response = alice.request(user_message)
    return response.message
```

### Claude Desktop Integration
```python
# Use MCP Server for Model Context Protocol
# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "alice": {
      "command": "python",
      "args": ["-m", "alicemultiverse.interface.mcp_server"]
    }
  }
}
```

### Scheduled Jobs
```bash
# Use CLI for cron jobs
# Add to crontab:
0 */6 * * * /usr/local/bin/alice --watch --quality --pipeline standard
```

## Performance Considerations

| Interface | Startup Time | Memory Usage | Best For |
|-----------|--------------|--------------|----------|
| CLI | Medium | Low | One-off tasks |
| AliceAPI | Fast | Medium | Long-running services |
| AliceOrchestrator | Fast | High | Complex workflows |
| AliceInterface | Fast | Medium | Traditional APIs |
| MediaOrganizer | Fastest | Low | Embedded use |

## Migration Guide

### From CLI to Python
```bash
# CLI command:
alice --inbox ~/Downloads --quality --pipeline premium

# Equivalent Python:
from alicemultiverse.interface import AliceAPI
alice = AliceAPI()
alice.request("organize ~/Downloads with premium quality assessment")
```

### From AliceInterface to AliceOrchestrator
```python
# AliceInterface (structured):
alice.search_assets({
    "style_tags": ["cyberpunk", "neon"],
    "min_quality_stars": 4
})

# AliceOrchestrator (natural):
alice.process_request({
    "query": "find cyberpunk neon images with 4+ stars"
})
```

## Troubleshooting

### "Which interface has feature X?"

| Feature | CLI | API | Orchestrator | Interface | Direct |
|---------|-----|-----|--------------|-----------|--------|
| Watch Mode | ✅ | ✅ | ✅ | ✅ | ✅ |
| Quality Assessment | ✅ | ✅ | ✅ | ✅ | ✅ |
| Natural Language | ❌ | ✅ | ✅ | ❌ | ❌ |
| Batch Operations | ❌ | ✅ | ✅ | ✅ | ✅ |
| Custom Pipelines | Limited | ✅ | ✅ | ✅ | ✅ |
| Event Handlers | ❌ | ❌ | ✅ | ❌ | ✅ |

### Common Mistakes

1. **Using MediaOrganizer directly for simple tasks**
   - Use AliceAPI or CLI instead

2. **Using AliceAPI when you need precise control**
   - Use AliceInterface for structured operations

3. **Not using the CLI for one-off tasks**
   - It's the simplest option for manual work

## Summary

- **Just want to organize files?** → Use the CLI
- **Building a simple integration?** → Use AliceAPI  
- **Need natural language features?** → Use AliceOrchestrator
- **Building a traditional API?** → Use AliceInterface
- **Extending the system?** → Use MediaOrganizer directly

Remember: You can always start simple and migrate to more complex interfaces as your needs grow.