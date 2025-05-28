# Simplification Plan: Event System & Provider Abstractions

## Overview

This document outlines the step-by-step plan to simplify AliceMultiverse's event system and provider abstractions based on the deep review findings. These simplifications will reduce code complexity by ~50% while maintaining all functionality.

## Part 1: Event System Simplification

### Current State
- 5 event store implementations (2,600+ lines)
- Complex abstractions forcing Redis concepts onto SQL databases
- Only SQLite used by default, but PostgreSQL is our target
- Duplicate Redis implementations

### Target State
- 1 PostgreSQL-based event system using NOTIFY/LISTEN
- Simple events table for persistence
- Direct event publishing without complex abstractions
- ~400 lines total (85% reduction)

### Step-by-Step Plan

#### Step 1: Create PostgreSQL-only Event System
**Reason**: We're PostgreSQL-only, so use its native pub/sub capabilities

```bash
# Commit: "Create PostgreSQL-native event system"
```

Tasks:
1. Create `alicemultiverse/events/postgres_events.py`:
   - Simple event publishing using NOTIFY
   - Event persistence in events table
   - Subscription using LISTEN
   - No consumer groups or DLQ (PostgreSQL doesn't need them)

2. Update database migrations:
   - Add events table with proper indexes
   - Add trigger for NOTIFY on insert

#### Step 2: Migrate Event Publishers
**Reason**: Update all code to use the new simple interface

```bash
# Commit: "Migrate event publishers to PostgreSQL events"
```

Tasks:
1. Update all event publishing code to use new interface
2. Remove EventBus abstraction - direct PostgreSQL publishing
3. Update tests to use new event system

#### Step 3: Remove Old Event System
**Reason**: Delete 2,200+ lines of unnecessary code

```bash
# Commit: "Remove legacy event store implementations"
```

Tasks:
1. Delete these files:
   - `alicemultiverse/events/store.py`
   - `alicemultiverse/events/redis_store.py`
   - `alicemultiverse/events/sqlite_store.py`
   - `alicemultiverse/events/memory_store.py`
   - `alicemultiverse/events/enhanced_bus.py`
   - `alicemultiverse/events/base_persistence.py`
   - `alicemultiverse/events/persistence.py` (duplicate Redis)

2. Update imports throughout codebase
3. Remove EVENT_STORE_BACKEND environment variable

## Part 2: Provider Abstraction Simplification

### Current State
- 2 base classes (GenerationProvider deprecated, BaseProvider new)
- 2 registries (ProviderRegistry wraps EnhancedProviderRegistry)
- Separate event mixin and cost tracking wrapper
- 4 layers of indirection

### Target State
- 1 base class with all functionality
- 1 registry managing providers
- Direct provider access without wrappers
- ~60% code reduction

### Step-by-Step Plan

#### Step 4: Create Unified Provider Base Class
**Reason**: Combine all provider functionality in one place

```bash
# Commit: "Create unified provider base class"
```

Tasks:
1. Create `alicemultiverse/providers/provider.py`:
   - Combine BaseProvider + events + cost tracking
   - Single source of truth for provider interface
   - Include all error types in one place

2. Move shared types to `alicemultiverse/providers/types.py`

#### Step 5: Migrate Providers to New Base
**Reason**: Update all providers to use unified interface

```bash
# Commit: "Migrate providers to unified base class"
```

Tasks:
1. Update these providers:
   - `fal_provider.py`
   - `openai_provider.py`
   - `anthropic_provider.py`

2. Remove event mixin usage
3. Remove cost tracking wrapper - it's now in base class

#### Step 6: Create Simple Registry
**Reason**: One registry is sufficient

```bash
# Commit: "Create simplified provider registry"
```

Tasks:
1. Create new `alicemultiverse/providers/registry.py`:
   - Direct provider management
   - Built-in cost tracking
   - No wrapper classes

2. Update all registry usage throughout codebase

#### Step 7: Remove Old Provider System
**Reason**: Delete unnecessary abstraction layers

```bash
# Commit: "Remove legacy provider abstractions"
```

Tasks:
1. Delete these files:
   - `alicemultiverse/providers/base.py` (old GenerationProvider)
   - `alicemultiverse/providers/base_provider.py` (old BaseProvider)
   - `alicemultiverse/providers/enhanced_registry.py`
   - `alicemultiverse/providers/event_mixin.py`

2. Update all imports and tests

## Part 3: Fix Critical Issues

#### Step 8: Fix Exception Handling
**Reason**: instructions.md #4 - no bare except blocks

```bash
# Commit: "Fix exception handling throughout codebase"
```

Tasks:
1. Replace all `except: pass` with proper error handling
2. Add specific exception types
3. Add logging for all caught exceptions

#### Step 9: Implement Video Hashing
**Reason**: Complete TODO in critical functionality

```bash
# Commit: "Implement video content hashing"
```

Tasks:
1. Implement proper video hashing in `assets/hashing.py`
2. Use ffmpeg to extract keyframes
3. Hash keyframe data for content identification

#### Step 10: Move Hardcoded Values to Config
**Reason**: Improve maintainability and flexibility

```bash
# Commit: "Move hardcoded values to configuration"
```

Tasks:
1. Add to settings.yaml:
   - Claude model names
   - Connection pool sizes
   - Retry limits and timeouts

2. Update code to use configuration values

## Impact Summary

### Code Reduction
- Event System: 2,600 lines → 400 lines (85% reduction)
- Provider System: ~1,500 lines → 600 lines (60% reduction)
- Total: ~4,100 lines removed

### Complexity Reduction
- Event stores: 5 → 1
- Provider base classes: 2 → 1
- Provider registries: 2 → 1
- Abstraction layers: 4 → 2

### Benefits
1. **Easier onboarding**: Clear, simple architecture
2. **Better performance**: Fewer layers of indirection
3. **Easier debugging**: Direct code paths
4. **Lower maintenance**: Less code to maintain
5. **Follows instructions.md**: "be pragmatic, direct, no bullshit"

## Migration Guide

For each step:
1. Create new implementation
2. Add compatibility shim if needed
3. Migrate usage incrementally
4. Remove old implementation
5. Run full test suite

## Part 4: Additional Improvements

#### Step 11: Add Input Validation
**Reason**: Security - prevent injection attacks and invalid data

```bash
# Commit: "Add input validation for API endpoints"
```

Tasks:
1. Add validation for Alice interface methods:
   - Path traversal prevention
   - SQL injection prevention
   - Size limits for uploads
2. Use pydantic models for all API inputs
3. Add rate limiting to prevent DoS

#### Step 12: Clean Up Empty/Unused Files
**Reason**: Reduce confusion and maintenance burden

```bash
# Commit: "Remove empty and unused files"
```

Tasks:
1. Delete empty files:
   - `alicemultiverse/organizer/event_aware_organizer.py`
   - Empty `__init__.py` files without exports
2. Remove unused modules identified in analysis
3. Update imports accordingly

#### Step 13: Add Missing Type Hints
**Reason**: Improve code quality and IDE support

```bash
# Commit: "Add comprehensive type hints"
```

Tasks:
1. Add type hints to all public APIs
2. Fix incorrect type hints (e.g., `any` → `Any`)
3. Add `py.typed` marker for type checking
4. Enable mypy in CI pipeline

#### Step 14: Update Documentation
**Reason**: Documentation should match current reality

```bash
# Commit: "Update documentation to reflect AI-native architecture"
```

Tasks:
1. Update all docs to remove CLI-first examples
2. Add AI conversation examples
3. Update architecture diagrams
4. Fix outdated configuration examples

## Timeline

Each step is designed to be a single working commit:
- Part 1 (Event System): Steps 1-3 (3 commits)
- Part 2 (Provider System): Steps 4-7 (4 commits)
- Part 3 (Critical Issues): Steps 8-10 (3 commits)
- Part 4 (Additional Improvements): Steps 11-14 (4 commits)

Total: 14 commits to complete simplification