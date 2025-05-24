# Architecture Documentation Cleanup - May 2024

## Summary

This document records the architectural clarifications and documentation updates made to ensure AliceMultiverse documentation reflects the current direction.

## Key Architectural Decisions

### 1. Alice is NOT an AI System
- Alice is a pure orchestration layer
- All natural language processing happens at the AI assistant layer
- Alice only accepts structured API requests
- No semantic understanding or creative interpretation in Alice

### 2. Structured Search Only
- Deprecated: Natural language search within Alice
- Current: Structured queries with explicit parameters
- AI assistants translate user intent into structured API calls
- Clear separation between technical metadata and semantic tags

### 3. Tag System Evolution
- Moving from simple tags to tag:value pairs
- Example: Instead of `["portrait", "cyberpunk"]`, use `{"subject": "portrait", "style": "cyberpunk"}`
- Enables more precise queries and better organization

## Documentation Updates

### Updated Files

1. **docs/architecture/alice-orchestration.md**
   - Removed all references to NLP within Alice
   - Clarified Alice as pure API gateway
   - Added explicit "Alice does NOT" section
   - Provided structured API examples

2. **docs/architecture/alice-interface-design.md** 
   - Already correctly stated principles (no changes needed)
   - Serves as the definitive guide for API design

3. **docs/architecture/metadata-extraction-strategy.md**
   - Clarified that AI analysis happens via external services
   - Alice orchestrates but doesn't perform AI tasks

4. **docs/developer/search-api-specification.md**
   - Added tag:value pair documentation
   - Clarified media_type vs semantic tags
   - Provided future-looking examples

5. **CLAUDE.md**
   - Added notes about structured APIs
   - Clarified tag usage principles

### Removed Concepts

- Natural language understanding in Alice
- Creative memory/pattern recognition in Alice  
- Semantic search within Alice (can be in metadata-extractor service)
- Any suggestion that Alice "understands" or "interprets"

### Architecture Principles Going Forward

1. **Clean Separation of Concerns**
   - AI Layer: Handles all NLP, creative understanding
   - Alice Layer: Pure orchestration, structured APIs
   - Service Layer: Specific technical capabilities

2. **Event-Driven Communication**
   - Services communicate via events
   - Alice coordinates but doesn't transform meaning
   - Clear contracts between services

3. **Structured Data Throughout**
   - No string parsing for meaning extraction
   - Explicit parameters for all operations
   - Type-safe interfaces

## Implementation Notes

### For Existing Code
- Mark any NLP methods as deprecated
- Provide structured alternatives
- Move NLP logic to AI assistant implementations

### For New Development
- Always require structured input
- Use tag:value pairs for rich metadata
- Keep Alice "dumb" - it's a router, not a thinker

## Benefits of This Approach

1. **Testability**: Predictable behavior, easy to test
2. **Maintainability**: Clear boundaries, less complexity
3. **Scalability**: Services can evolve independently
4. **Flexibility**: Different AI assistants can have different capabilities
5. **Performance**: Structured queries enable efficient indexing

## Future Considerations

- Implement tag:value storage and querying
- Build metadata extraction pipeline for rich tagging
- Create service templates that follow these principles
- Develop API client libraries for AI assistants