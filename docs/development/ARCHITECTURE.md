# AliceMultiverse Architecture

## Overview

AliceMultiverse is an AI media organization system built with a modular, event-driven architecture. This document explains the key architectural decisions and component relationships.

## Core Components

### 1. Media Organization Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│   Inbox     │────▶│   Detector   │────▶│  Organizer   │────▶│ Organized  │
│  (Source)   │     │ (AI Source)  │     │ (Structure)  │     │  (Output)  │
└─────────────┘     └──────────────┘     └──────────────┘     └────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐      ┌──────────────┐
                    │   Metadata   │      │   Quality    │
                    │  Extraction  │      │ Assessment   │
                    └──────────────┘      └──────────────┘
```

### 2. Cache System Architecture

The cache system uses an **adapter pattern** to maintain backward compatibility while migrating to a unified implementation:

```
Application Code
       │
       ▼
┌─────────────────────────────────────────┐
│          Cache Adapters Layer           │
├──────────────┬────────────┬─────────────┤
│ MetadataCache│ Enhanced   │ Persistent  │
│   Adapter    │   Cache    │  Manager    │
│              │  Adapter   │  Adapter    │
└──────────────┴────────────┴─────────────┘
                     │
                     ▼
              ┌─────────────┐
              │UnifiedCache │
              │  (Core)     │
              └─────────────┘
```

**Why Adapters?**
- Allows gradual migration without breaking changes
- Maintains API compatibility
- Centralizes implementation in UnifiedCache

### 3. Organizer Hierarchy

```
MediaOrganizer (Base)
    │
    ├─► EnhancedMediaOrganizer
    │   (adds metadata search & enhanced caching)
    │
    └─► EventAwareOrganizer
        (adds event publishing)
```

**Feature Comparison:**
| Feature | MediaOrganizer | EnhancedMediaOrganizer | EventAwareOrganizer |
|---------|----------------|------------------------|-------------------|
| Basic Organization | ✓ | ✓ | ✓ |
| Quality Assessment | ✓ | ✓ | ✓ |
| Metadata Search | ✗ | ✓ | ✗ |
| Event Publishing | ✗ | ✗ | ✓ |
| Enhanced Caching | ✗ | ✓ | ✗ |

### 4. Interface Evolution

The interface module provides multiple abstraction levels for different use cases:

```
┌─────────────────┐
│   AliceAPI      │  ← Simplest (1 method)
└────────┬────────┘
         │ uses
┌────────▼────────┐
│AliceOrchestrator│  ← Natural language
└────────┬────────┘
         │ uses
┌────────▼────────┐
│ AliceInterface  │  ← Structured methods
└────────┬────────┘
         │ uses
┌────────▼────────┐
│  MediaOrganizer │  ← Core functionality
└─────────────────┘
```

**When to Use Each:**
- **AliceAPI**: Building chat interfaces, simple integrations
- **AliceOrchestrator**: AI assistants, natural language workflows
- **AliceInterface**: Traditional APIs, programmatic access
- **MediaOrganizer**: Direct access to core functionality

### 5. Event System

The event system enables loose coupling and extensibility:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Publisher  │────▶│  Event Bus   │────▶│  Subscriber  │
│ (Organizer)  │     │  (In-Memory) │     │  (Handler)   │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Event Types:**
- **Asset Events**: Discovery, processing, organization
- **Workflow Events**: Start, progress, completion
- **Creative Events**: Project creation, context updates
- **Quality Events**: Assessment results, score updates

### 6. Quality Assessment Pipeline

Multi-stage quality assessment with increasing cost/accuracy:

```
        ┌─────────────┐
Image ──▶│  BRISQUE   │──▶ Score (Free, Local)
        └──────┬──────┘
               │ Optional
        ┌──────▼──────┐
        │ SightEngine │──▶ Technical Quality (~$0.001/image)
        └──────┬──────┘
               │ Optional
        ┌──────▼──────┐
        │   Claude    │──▶ Artistic Quality (~$0.002/image)
        └─────────────┘
```

## Design Principles

### 1. Content-Addressed Storage
- Files tracked by content hash, not path
- Enables reorganization without losing metadata
- Supports deduplication

### 2. Progressive Enhancement
- Start with basic organization
- Add quality assessment as needed
- Enable advanced features on demand

### 3. Event-Driven Architecture
- Loose coupling between components
- Easy to extend with new handlers
- Enables future microservices split

### 4. Backward Compatibility
- Adapter pattern for smooth migrations
- Deprecation warnings before removal
- Clear upgrade paths

## Future Architecture

The system is designed to evolve into a distributed architecture:

```
Current (Monolith)          →          Future (Microservices)
┌─────────────────┐                   ┌─────────────────┐
│                 │                   │  Alice Gateway  │
│  AliceMultiverse│                   └────────┬────────┘
│   (All-in-One)  │                            │
│                 │         ┌──────────────────┼──────────────────┐
└─────────────────┘         │                  │                  │
                      ┌─────▼─────┐     ┌──────▼──────┐    ┌─────▼─────┐
                      │   Media    │     │   Quality   │    │  Project  │
                      │  Service   │     │   Service   │    │  Service  │
                      └───────────┘     └─────────────┘    └───────────┘
```

## Configuration Architecture

Hierarchical configuration with multiple override levels:

```
1. Default Config (in package)
       ↓
2. User Config (settings.yaml)
       ↓
3. Environment Variables
       ↓
4. Command Line Arguments
```

## Security Considerations

- API keys stored in OS keychain (never in files)
- Content hashes prevent tampering
- Event system doesn't expose file paths
- MCP server limits access to Alice functions only

## Performance Optimizations

1. **Lazy Loading**: Modules loaded only when needed
2. **Caching**: Multiple levels (memory, disk, embedded)
3. **Batch Processing**: Group operations for efficiency
4. **Quick Hashing**: Fast change detection before full hash

## Testing Strategy

```
tests/
├── unit/          # Component isolation
├── integration/   # Component interaction
└── e2e/          # Full workflow tests
```

This architecture provides a solid foundation for current needs while enabling future evolution into a comprehensive creative workflow system.