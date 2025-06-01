# ADR-009: File-First Metadata Architecture

**Status**: Accepted  
**Date**: 2025-01-31  
**Context**: Database lock-in prevents file portability

## Context

Traditional media management systems store metadata in databases, creating several problems:
1. **Lock-in**: Files lose their context when moved
2. **Sync Issues**: Database and filesystem can diverge
3. **Fragility**: Database corruption affects all files
4. **Complexity**: Backup requires both files and database

Users frequently requested:
- "I want to move files to another drive and keep tags"
- "Can I share a folder with someone and include metadata?"
- "What happens if the database crashes?"

## Decision

Implement a file-first architecture where:
- All metadata is embedded directly in files (EXIF, XMP, etc.)
- Database serves only as a search cache
- Files are self-contained with their metadata
- Search index can be rebuilt from files at any time
- Content-addressed storage tracks files by hash

## Rationale

### Why File-First

1. **True Portability**: Files carry their complete context
2. **Resilience**: No single point of failure
3. **Simplicity**: Standard tools can read metadata
4. **Flexibility**: Works with any storage backend
5. **User Control**: Metadata stays with user's files

### Technical Approach

- Use standard metadata formats (EXIF for images, XMP for extended data)
- Embed tags, descriptions, and generation parameters
- Store JSON metadata in XMP fields for complex data
- Track files by content hash for relocatability

### Alternatives Considered

1. **Sidecar Files**: .json files alongside media
   - Rejected: Easy to lose, harder to manage
   
2. **Blockchain Storage**: Decentralized metadata
   - Rejected: Overcomplicated for the use case
   
3. **Cloud Sync**: Sync database to cloud
   - Rejected: Still requires database dependency

## Consequences

### Positive
- Files are truly portable
- Works with existing tools (Lightroom, etc.)
- No vendor lock-in
- Simplified backup (just copy files)
- Enables P2P sharing with metadata
- Database can be regenerated anytime

### Negative
- Initial embedding takes time
- Some file formats have limited metadata support
- Slightly larger file sizes
- Need to handle metadata conflicts
- Requires careful write coordination

## Implementation Details

Key components:
- `alicemultiverse/metadata/embedder.py` - Metadata embedding
- `alicemultiverse/assets/hashing.py` - Content addressing
- `alicemultiverse/storage/location_registry.py` - Multi-location tracking

Metadata structure:
```python
{
    "alice:version": "1.7.0",
    "alice:tags": ["portrait", "cyberpunk", "neon"],
    "alice:source": "midjourney",
    "alice:generation": {
        "prompt": "cyberpunk portrait --v 6",
        "model": "v6",
        "timestamp": "2024-03-15T10:30:00Z"
    }
}
```

## Migration Path

1. Scan existing database
2. Embed metadata into files
3. Verify embedding success
4. Rebuild search index from files
5. Mark database as cache-only

## References

- [Metadata Structure Documentation](../metadata-structure.md)
- [File-First Architecture](../file-first-architecture.md)
- EXIF Specification: https://exif.org/
- XMP Specification: https://www.adobe.com/devnet/xmp.html
- Issue #178: "Lost all tags when moved to NAS"