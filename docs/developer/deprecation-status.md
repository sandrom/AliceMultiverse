# Deprecation Status Guide

*Last Updated: January 2025*

## Overview

This document tracks deprecated features in AliceMultiverse and their migration paths.

## Recently Removed (v2.1.0)

### Cache Modules ✅
The following cache modules have been removed after a migration period:

#### 1. `alicemultiverse.core.metadata_cache.MetadataCache`
- **Removed in**: v2.1.0 (January 2025)
- **Replacement**: `alicemultiverse.core.unified_cache.UnifiedCache`
- **Migration**: Use `MetadataCacheAdapter` from `core.cache_migration` for compatibility

#### 2. `alicemultiverse.metadata.enhanced_cache.EnhancedMetadataCache`
- **Removed in**: v2.1.0 (January 2025)
- **Replacement**: `alicemultiverse.core.unified_cache.UnifiedCache`
- **Migration**: Use `EnhancedMetadataCacheAdapter` from `core.cache_migration`

#### 3. `alicemultiverse.metadata.persistent_metadata.PersistentMetadataManager`
- **Removed in**: v2.1.0 (January 2025)
- **Replacement**: `alicemultiverse.core.unified_cache.UnifiedCache`
- **Migration**: Use `PersistentMetadataManagerAdapter` from `core.cache_migration`

### Migration Example
```python
# Old way (no longer works)
from alicemultiverse.core.metadata_cache import MetadataCache

# New way (using adapter)
from alicemultiverse.core.cache_migration import MetadataCacheAdapter as MetadataCache

# Or migrate to unified cache directly
from alicemultiverse.core.unified_cache import UnifiedCache
```

## Currently Deprecated

### 1. CLI Interface (Deprecated in v2.0.0)
- **Status**: Maintained for debugging only
- **Replacement**: AI assistant interface via MCP
- **Timeline**: No removal planned (needed for debugging)
- **Usage**: Must use `--debug` flag

```bash
# Deprecated
alice organize

# Current (debugging only)
alice --debug organize

# Recommended
# Use through Claude Desktop or other AI assistants
```

### 2. Quality Assessment System
- **Status**: Replaced by Understanding System
- **Replacement**: Use `--understand` flag with alice CLI
- **Features removed**:
  - BRISQUE scoring
  - Star ratings based on technical quality
  - `assess_quality` in API

```python
# Deprecated
quality_score = assess_quality(image_path)

# Current
analysis = await analyzer.analyze(image_path)
tags = analysis.tags  # Semantic understanding instead of quality score
```

### 3. PostgreSQL Integration
- **Status**: Completely removed
- **Replacement**: File-based storage with DuckDB search
- **Migration**: All data now stored in `.metadata/` directories

### 4. Redis Requirement
- **Status**: Optional
- **Default**: File-based events and cache
- **Enable Redis**: Set environment variables
  - `USE_REDIS_EVENTS=true`
  - `USE_REDIS_CACHE=true`

## Deprecation Timeline

### Phase 1: Completed ✅
- Remove PostgreSQL dependencies
- Implement file-based alternatives
- Add migration adapters for cache modules

### Phase 2: Completed ✅
- Remove deprecated cache modules
- Update all imports
- Maintain backward compatibility via adapters

### Phase 3: In Progress 🔄
- Refactor large modules (MCP server)
- Extract common patterns
- Update documentation

### Phase 4: Planned 📋
- Remove quality assessment remnants
- Consolidate event system backends
- Simplify configuration

## Features Marked for Future Deprecation

### 1. Multiple Event Backends
- **Current**: File-based (default) and Redis (optional)
- **Future**: Single unified event system
- **Timeline**: v3.0.0 (late 2025)

### 2. Legacy Pipeline Modes
- **Current**: Multiple pipeline modes in configuration
- **Future**: Single, optimized pipeline
- **Timeline**: After pipeline architecture review

## Migration Resources

### Documentation
- [Cache Migration Guide](../architecture/caching-strategy.md)
- [File-based Storage Guide](../architecture/storage/file-based-storage.md)
- [Event System Guide](../architecture/event-driven-architecture.md)

### Code Examples
- Cache migration: `alicemultiverse/core/cache_migration.py`
- Configuration migration: `CONFIGURATION_GUIDE.md`
- MCP migration: `alicemultiverse/mcp/MIGRATION_GUIDE.md`

## Best Practices

### For Developers
1. **Check deprecation warnings** in logs
2. **Use migration adapters** for smooth transition
3. **Update imports** as soon as possible
4. **Test thoroughly** after migrations

### For Users
1. **Use AI assistants** instead of CLI
2. **Update configuration** to remove deprecated options
3. **Check release notes** for deprecation notices

## Deprecation Policy

1. **Warning Period**: 3-6 months with deprecation warnings
2. **Migration Path**: Always provide adapters or alternatives
3. **Documentation**: Update guides before removal
4. **Breaking Changes**: Only in major versions (x.0.0)

## Getting Help

If you encounter issues with deprecated features:

1. Check this guide for migration paths
2. Review release notes for your version
3. Open an issue on GitHub
4. Ask in community discussions

---

*This document is updated with each release that deprecates or removes features.*