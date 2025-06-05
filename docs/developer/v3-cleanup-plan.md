# V3.0 Cleanup Plan

This document tracks deprecated code scheduled for removal in AliceMultiverse v3.0.

## Deprecated Cache Modules

The following cache modules have been replaced by `UnifiedCache` and will be removed:

### 1. `alicemultiverse.core.metadata_cache`
- **Status**: Deprecated, using adapter for compatibility
- **Replacement**: `alicemultiverse.core.unified_cache.UnifiedCache`
- **Used by**: Legacy code through `MetadataCacheAdapter` in `cache_migration.py`
- **Migration**: All production code already uses adapters

### 2. `alicemultiverse.metadata.enhanced_cache`
- **Status**: Deprecated, using adapter for compatibility
- **Replacement**: `alicemultiverse.core.unified_cache.UnifiedCache`
- **Used by**: Legacy code through `EnhancedMetadataCacheAdapter` in `cache_migration.py`
- **Migration**: All production code already uses adapters

### 3. `alicemultiverse.metadata.persistent_metadata`
- **Status**: Likely deprecated (check usage)
- **Replacement**: `alicemultiverse.core.unified_cache.UnifiedCache`
- **Used by**: Legacy code through `PersistentMetadataManagerAdapter` in `cache_migration.py`
- **Migration**: All production code already uses adapters

## Migration Strategy

1. **Current State**: Production code imports from `cache_migration.py` which provides adapters
2. **Adapters**: `MetadataCacheAdapter`, `EnhancedMetadataCacheAdapter`, `PersistentMetadataManagerAdapter`
3. **Target State**: Direct use of `UnifiedCache` without adapters

## Removal Checklist for v3.0

- [ ] Remove `core/metadata_cache.py`
- [ ] Remove `metadata/enhanced_cache.py`
- [ ] Remove `metadata/persistent_metadata.py` (if confirmed deprecated)
- [ ] Update all imports to use `UnifiedCache` directly
- [ ] Remove adapter classes from `cache_migration.py`
- [ ] Update all tests to test `UnifiedCache` directly
- [ ] Remove example files using deprecated modules
- [ ] Update documentation

## Files to Update

### Test Files
- `tests/unit/test_metadata_cache.py` - Remove or rewrite for UnifiedCache
- `tests/test_metadata_cache_integration.py` - Remove or rewrite
- `tests/test_metadata_embedding.py` - Update imports

### Example Files
- `examples/advanced/persistent_metadata_example.py` - Remove or update

### Import Updates Needed
- `organizer/media_organizer.py` - Uses MetadataCacheAdapter
- `organizer/enhanced_organizer.py` - Uses EnhancedMetadataCacheAdapter
- Any other files importing from `cache_migration.py`

## Testing Before Removal

1. Ensure all tests pass with current adapter setup
2. Create feature branch for v3.0 cleanup
3. Remove deprecated modules one by one
4. Update imports to use UnifiedCache directly
5. Run full test suite after each change
6. Ensure no functionality is lost