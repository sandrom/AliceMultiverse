# Multi-Path Storage System Design

## Overview

AliceMultiverse is evolving from a single-folder organizer to a distributed media management system that can track and organize files across multiple storage locations including local drives, cloud storage (S3/GCS), and network drives.

## Core Principles

1. **Content-Addressed Storage**: Files are tracked by their content hash, not location
2. **Metadata Lives with Files**: All metadata is embedded in files for portability
3. **Database as Cache**: The database is just a search cache that can be rebuilt
4. **Location Transparency**: Find files regardless of where they're stored
5. **Zero Lock-in**: Files remain self-contained and portable

## Architecture

### 1. Storage Location Registry

```python
@dataclass
class StorageLocation:
    """Represents a storage location."""
    name: str
    type: Literal["local", "s3", "gcs", "network"]
    config: Dict[str, Any]
    purpose: List[str]  # ["inbox", "organized", "archive", "backup"]
    scan: bool = False  # Whether to scan for new files
    read_only: bool = False
    
    # Local storage
    path: Optional[Path] = None
    
    # S3 storage
    bucket: Optional[str] = None
    prefix: Optional[str] = None
    region: Optional[str] = None
    
    # GCS storage
    project: Optional[str] = None
    
    # Network storage
    mount_path: Optional[Path] = None
    credentials: Optional[Dict] = None
```

### 2. File Tracking System

```python
@dataclass
class FileLocation:
    """Track where a file is stored."""
    content_hash: str  # SHA-256 hash
    locations: List[LocationInfo]
    primary_location: str  # Preferred location name
    last_seen: datetime
    file_size: int
    media_type: MediaType
    
@dataclass
class LocationInfo:
    """Information about a file in a specific location."""
    location_name: str
    path: str  # Full path or S3 key
    exists: bool
    last_verified: datetime
    metadata_embedded: bool
    cloud_metadata: Optional[Dict] = None  # For S3/GCS metadata
```

### 3. Storage Rules Engine

```yaml
# Example rules configuration
storage:
  rules:
    # Rule 1: Videos go to cloud
    - match:
        media_type: video
        age: ">30d"
      action: move
      destination: s3_archive
      
    # Rule 2: Client work to external
    - match:
        project: "client-*"
        tags.contains: "deliverable"
      action: copy
      destination: external_backup
      
    # Rule 3: Large files to archive
    - match:
        size: ">1GB"
      action: move
      destination: cold_storage
      keep_local_preview: true
      
    # Rule 4: Default
    - default: primary
```

### 4. Multi-Location Operations

```python
class MultiLocationManager:
    """Manage files across multiple storage locations."""
    
    async def discover_file(self, content_hash: str) -> List[LocationInfo]:
        """Find all locations where a file exists."""
        
    async def ensure_available(self, content_hash: str, location: str) -> Path:
        """Ensure file is available at specified location, copying if needed."""
        
    async def sync_metadata(self, content_hash: str):
        """Sync metadata across all copies of a file."""
        
    async def apply_rules(self, content_hash: str):
        """Apply storage rules to determine where file should be."""
        
    async def optimize_storage(self):
        """Optimize storage based on access patterns and rules."""
```

### 5. Search Index Architecture

```python
class UnifiedSearchIndex:
    """Search index that spans all storage locations."""
    
    def __init__(self, backend: str = "sqlite"):
        self.backend = self._init_backend(backend)
        
    async def index_file(self, file_info: FileLocation, metadata: Dict):
        """Index a file regardless of its location."""
        
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search across all locations."""
        
    async def rebuild_from_locations(self, locations: List[StorageLocation]):
        """Rebuild index by scanning all storage locations."""
```

## Implementation Phases

### Phase 1: Location Registry (Week 1)
- [ ] Create StorageLocation configuration
- [ ] Implement location registry
- [ ] Add configuration UI/CLI
- [ ] Basic location scanning

### Phase 2: Content-Addressed Tracking (Week 2)
- [ ] Implement FileLocation tracking
- [ ] Create content hash index
- [ ] Add file discovery across locations
- [ ] Implement location verification

### Phase 3: Multi-Location Operations (Week 3)
- [ ] File copy/move between locations
- [ ] Metadata synchronization
- [ ] Conflict resolution
- [ ] Access optimization

### Phase 4: Storage Rules (Week 4)
- [ ] Rules engine implementation
- [ ] Rule matching logic
- [ ] Automated file movement
- [ ] Storage optimization

### Phase 5: Cloud Integration (Week 5-6)
- [ ] S3 adapter implementation
- [ ] GCS adapter implementation
- [ ] Cloud metadata handling
- [ ] Bandwidth optimization

## API Examples

### Configuration
```python
# Configure multiple locations
alice.add_location(
    name="primary",
    type="local",
    path="~/Pictures/AI",
    purpose=["organized"],
)

alice.add_location(
    name="s3_archive",
    type="s3",
    bucket="my-ai-archive",
    prefix="images/",
    purpose=["archive", "backup"],
)

alice.add_location(
    name="external",
    type="local",
    path="/Volumes/External/AI",
    purpose=["overflow"],
    scan=True,
)
```

### Usage
```python
# Find a file across all locations
locations = await alice.find_file("sha256:abc123...")
print(f"File found in {len(locations)} locations")

# Ensure file is available locally
local_path = await alice.ensure_available(
    "sha256:abc123...",
    location="primary"
)

# Apply storage rules
await alice.apply_storage_rules()  # Moves files based on rules

# Search across all locations
results = await alice.search(
    tags=["portrait", "dramatic"],
    locations=["primary", "s3_archive"],  # Optional filter
)
```

## Benefits

1. **Flexibility**: Store files where it makes sense (cost, speed, capacity)
2. **Reliability**: Multiple copies across locations
3. **Performance**: Local cache of frequently used files
4. **Cost Optimization**: Use cheap storage for archives
5. **Scalability**: Add new storage locations as needed

## Migration Strategy

1. Start with current single-location setup
2. Add location registry without changing behavior
3. Gradually add new locations
4. Implement rules engine
5. Enable automatic optimization

## Security Considerations

1. **Encryption**: Files encrypted in cloud storage
2. **Access Control**: Per-location permissions
3. **Audit Trail**: Track all file movements
4. **Secure Credentials**: Use key management service

## Future Enhancements

1. **P2P Sync**: Sync between multiple Alice instances
2. **CDN Integration**: Serve files from edge locations
3. **Smart Caching**: ML-based prediction of file access
4. **Compression**: Automatic compression for archives
5. **Deduplication**: Content-aware deduplication