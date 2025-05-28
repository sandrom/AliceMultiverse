# ADR-006: AI-Native Service Architecture

**Status**: Implemented  
**Date**: 2025-01-28  
**Updated**: 2025-01-28 - Migration completed  
**Context**: Fundamental Architecture Direction

## Context

AliceMultiverse started as a CLI tool for organizing AI-generated media. However, the vision has evolved to position Alice as an AI-native service that operates exclusively through AI assistants like Claude and ChatGPT via protocols like MCP (Model Context Protocol).

This represents a fundamental shift from direct user interaction to AI-mediated interaction.

## Decision

Adopt an AI-native service architecture where:
1. All user interaction happens through AI assistants
2. The CLI becomes a developer/debugging tool only
3. Service boundaries are designed for AI orchestration
4. Documentation focuses on AI conversations, not commands

## Rationale

### Why AI-Native?

1. **Zero Learning Curve**: Users already know how to talk to AI assistants
2. **Context Awareness**: AI understands project context and user intent
3. **Natural Workflows**: Complex operations become simple conversations
4. **Progressive Disclosure**: AI can guide users from simple to advanced features

### Why Not Traditional CLI/GUI?

1. **Learning Barrier**: Users must learn commands, flags, configurations
2. **Context Loss**: Each command is isolated, no workflow memory
3. **Error Handling**: Cryptic errors vs. AI-explained issues
4. **Discoverability**: Hidden features vs. AI suggestions

### Architecture Implications

The current "complex" architecture makes sense for AI-native operation:

1. **Event System**: AI can monitor long-running operations
2. **Service Boundaries**: Clean separation for AI orchestration
3. **Structured Interfaces**: AI translates natural language to API calls
4. **Persistence**: Maintains state between AI conversations

## Consequences

### Positive

1. **Accessibility**: No technical knowledge required
2. **Intelligence**: AI can suggest optimal workflows
3. **Integration**: Works within existing AI workflows
4. **Evolution**: Improves as AI capabilities grow

### Negative

1. **AI Dependency**: Requires AI assistant to operate
2. **Latency**: Additional layer between user and functionality
3. **Cost**: AI API calls add operational cost
4. **Complexity**: More moving parts than simple CLI

### Migration Path (Completed)

1. **Phase 1**: ✅ Parallel operation (CLI + AI)
2. **Phase 2**: ✅ AI-first documentation
3. **Phase 3**: ✅ Deprecate direct CLI usage
4. **Phase 4**: ✅ CLI for developers only

**Migration completed**: The CLI now requires --debug flag for all non-essential commands. Deprecation warnings guide users to AI-native usage.

## Implementation Guidelines

### Service Interface Design

```python
class AliceService:
    """AI-friendly service interface."""
    
    async def execute(self, request: StructuredRequest) -> StructuredResponse:
        """Single entry point for all AI operations."""
        # AI assistants call this with structured requests
        # Alice returns structured responses AI can interpret
```

### Error Design

```python
class AIFriendlyError(Exception):
    """Errors designed for AI explanation."""
    user_message: str  # What AI tells user
    technical_details: str  # For AI debugging
    suggestions: List[str]  # What user could try
```

### Documentation Strategy

Replace:
```bash
alice --quality --pipeline premium
```

With:
```
User: "Assess the quality of my new images"
Claude: "I'll check your new images using premium quality assessment..."
```

## References

- MCP Specification: https://modelcontextprotocol.io/
- Claude Desktop Integration: docs/integrations/claude-desktop.md
- Original CLI Design: ADR-004-alice-sole-orchestrator.md