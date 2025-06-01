# Deprecation Guide

This guide helps you migrate from deprecated modules to their replacements.

## MetadataCache → UnifiedCache

The `MetadataCache` class is deprecated and will be removed in v3.0. Use `UnifiedCache` instead.

### Before (deprecated):
```python
from alicemultiverse.core.metadata_cache import MetadataCache

cache = MetadataCache(source_root, force_reindex)
metadata = cache.load(media_path)
cache.save(media_path, analysis, time)
```

### After (recommended):
```python
from alicemultiverse.core.unified_cache import UnifiedCache

cache = UnifiedCache(source_root, project_id="default", force_reindex=force_reindex)
metadata = cache.load(media_path)
cache.save(media_path, analysis, time)
```

### What's Different?
- `UnifiedCache` includes all functionality from `MetadataCache` plus:
  - Enhanced metadata extraction and embedding
  - Search capabilities with DuckDB backend
  - Automatic metadata embedding in image files
  - Better performance with in-memory indexing

### Backward Compatibility
- The `MetadataCacheAdapter` provides a compatibility layer
- Existing code using `MetadataCache` will continue to work until v3.0
- A deprecation warning will be shown when importing `MetadataCache`

## SQLAlchemy Declarative Base

### Before (deprecated):
```python
from sqlalchemy.ext.declarative import declarative_base
```

### After (recommended):
```python
from sqlalchemy.orm import declarative_base
```

## AsyncIO Event Loop

### Before (deprecated):
```python
loop = asyncio.get_event_loop()
```

### After (recommended):
```python
# In async context:
loop = asyncio.get_running_loop()

# In sync context where you need to create a loop:
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
```

## Quality Assessment → Understanding System

The quality assessment pipeline has been replaced with the understanding system.

### Before (deprecated):
```bash
alice --quality
alice --pipeline brisque
```

### After (recommended):
```bash
alice --understand
alice --understand --providers openai,anthropic
```

### What's Different?
- Quality scoring (BRISQUE) has been replaced with semantic understanding
- Focus shifted from technical quality to content understanding
- AI providers analyze images for content, style, and semantic tags
- Metadata now includes rich semantic information instead of quality scores

## Pipeline System → Understanding System

### Before (deprecated):
```python
from alicemultiverse.pipeline import create_pipeline_stages

stages = create_pipeline_stages(["brisque", "sightengine"])
```

### After (recommended):
```python
from alicemultiverse.understanding import UnderstandingPipeline

pipeline = UnderstandingPipeline(providers=["openai", "anthropic"])
```

## Migration Timeline

- **v1.7.x** (current): Deprecation warnings added, backward compatibility maintained
- **v2.0**: Understanding system becomes default, quality system moved to legacy module
- **v3.0**: Deprecated modules removed entirely

## Getting Help

If you encounter issues during migration:
1. Check the [CHANGELOG](../../CHANGELOG.md) for breaking changes
2. Review example code in the [examples/](../../examples/) directory
3. Submit issues at https://github.com/yourusername/AliceMultiverse/issues