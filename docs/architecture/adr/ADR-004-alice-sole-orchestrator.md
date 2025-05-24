# ADR-004: Alice as Sole Orchestrator

**Status**: Accepted  
**Date**: 2024-01-26  
**Context**: AliceMultiverse Architecture

## Context

As AliceMultiverse evolves into a creative workflow hub, we need clear boundaries around what Alice does and doesn't do. The proliferation of AI tools and creative services creates complexity that must be managed through clear architectural principles.

## Decision

Alice is the sole orchestrator in the AliceMultiverse ecosystem. Alice does NOT:
- Understand natural language
- Perform AI/ML computations
- Generate creative content
- Make aesthetic judgments
- Interpret semantic meaning

Alice ONLY:
- Accepts structured API calls
- Routes requests to appropriate services
- Orchestrates workflows between services
- Manages state and coordination
- Provides a unified interface

## Rationale

### Clear Separation of Concerns
- **AI Services**: Handle natural language, creativity, and intelligence
- **Alice**: Handles orchestration, routing, and coordination
- **Creative Tools**: Handle actual content generation and manipulation

### Why This Matters
1. **Simplicity**: Alice remains a simple, reliable orchestrator
2. **Flexibility**: New AI services can be added without changing Alice
3. **Performance**: No computational overhead from AI/ML in the orchestration layer
4. **Reliability**: Orchestration logic is deterministic and testable

### Example Flow
```
User → ChatGPT/Claude → Structured API → Alice → Services → Results
       (NLP happens here)    (No NLP here)
```

The AI assistant translates user intent into structured API calls that Alice can execute.

## Consequences

### Positive
- Alice remains lightweight and fast
- Clear API contracts between components
- Easy to test and debug orchestration logic
- Can swap AI providers without changing Alice

### Negative
- Requires AI assistants to understand Alice's API
- No "fuzzy" matching or interpretation in Alice
- All intelligence must be pushed to external services

### Implementation Guidelines

1. **API Design**: All Alice APIs must be structured, typed, and deterministic
2. **No Interpretation**: If something requires interpretation, it belongs in an AI service
3. **Event-Driven**: Use events for loose coupling between Alice and services
4. **Stateless**: Alice should remain as stateless as possible

## References

- Event-Driven Architecture documentation
- Alice Orchestration documentation
- Original vision document (todo/02)