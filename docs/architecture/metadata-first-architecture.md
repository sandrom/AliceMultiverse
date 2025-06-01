# Metadata-First Architecture

## Core Principle: Files Are The Source of Truth

AliceMultiverse treats files as self-contained units with all metadata embedded directly in them. The database (DuckDB) is purely a search cache that can be rebuilt at any time by scanning files.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FILES (Source of Truth)               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  image.jpg  │  │  video.mp4  │  │  sound.mp3  │  ...   │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │        │
│  │ │Metadata │ │  │ │Metadata │ │  │ │Metadata │ │        │
│  │ │Embedded │ │  │ │Embedded │ │  │ │Embedded │ │        │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Scan & Extract
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DuckDB (Search Cache)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ content_hash │ locations │ tags │ understanding │... │  │
│  └──────────────────────────────────────────────────────┘  │
│                    Can be rebuilt anytime                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Optional Export
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Parquet Files (Analytics)                   │
│            For archival and big data analysis                │
└─────────────────────────────────────────────────────────────┘
```

## Metadata Storage Strategy

### 1. Everything in File Metadata

All information is embedded directly in files using standard metadata fields:

```python
# Image files (EXIF/XMP/IPTC)
metadata = {
    # Standard fields
    "ImageDescription": "A cyberpunk portrait of a woman...",
    "Keywords": ["cyberpunk", "portrait", "neon", "woman"],
    "Creator": "Midjourney",
    
    # Custom XMP namespace for Alice
    "Xmp.alice.content_hash": "sha256:abc123...",
    "Xmp.alice.understanding": json.dumps({
        "tags": {
            "style": ["cyberpunk", "neon"],
            "mood": ["dramatic", "mysterious"],
            "subject": ["woman", "portrait"],
            "colors": ["blue", "purple", "pink"]
        },
        "description": "A cyberpunk portrait...",
        "generated_prompt": "cyberpunk woman portrait, neon lights...",
        "provider_outputs": [...]  # Individual model outputs
    }),
    "Xmp.alice.generation": json.dumps({
        "provider": "midjourney",
        "model": "v6",
        "prompt": "original prompt used",
        "parameters": {...},
        "cost": 0.05,
        "generated_at": "2024-01-15T10:30:00Z"
    })
}

# Video files (similar approach with MP4 metadata)
# Audio files (ID3 tags for MP3, similar structure)
```

### 2. DuckDB as Search Cache

DuckDB is populated by scanning files and extracting their metadata:

```python
class DuckDBCache:
    def rebuild_from_files(self, paths: List[Path]):
        """Scan all files and rebuild the search cache."""
        for path in paths:
            for file_path in path.rglob("*"):
                if self.is_media_file(file_path):
                    metadata = self.extract_embedded_metadata(file_path)
                    self.insert_or_update(metadata)
    
    def extract_embedded_metadata(self, file_path: Path) -> dict:
        """Extract all Alice metadata from file."""
        # Use appropriate library based on file type
        if file_path.suffix.lower() in ['.jpg', '.png', '.webp']:
            return self.extract_image_metadata(file_path)
        elif file_path.suffix.lower() in ['.mp4', '.mov']:
            return self.extract_video_metadata(file_path)
        elif file_path.suffix.lower() in ['.mp3', '.wav']:
            return self.extract_audio_metadata(file_path)
```

### 3. No JSON Sidecar Files

We explicitly **DO NOT** use JSON sidecar files because:

1. **Separation breaks atomicity** - File and metadata can get separated
2. **Duplication of truth** - Same data in two places
3. **Sync issues** - Sidecar can get out of sync with file
4. **Portability problems** - Need to move two files instead of one
5. **Not necessary** - Modern file formats support rich metadata

## Multi-Location Tracking

Files can exist in multiple locations, all tracked by content hash:

```sql
-- DuckDB schema for tracking locations
CREATE TABLE file_tracking (
    content_hash VARCHAR PRIMARY KEY,
    file_size BIGINT,
    media_type VARCHAR,
    
    -- All locations where this file exists
    locations STRUCT(
        path VARCHAR,
        storage_type VARCHAR,  -- local, s3, gcs, network
        last_verified TIMESTAMP,
        metadata_version VARCHAR  -- Track if metadata needs update
    )[],
    
    -- Latest metadata extracted from file
    metadata JSON,
    last_metadata_extraction TIMESTAMP
);
```

## Parquet Files for Analytics

Parquet files are used for:

1. **Archival exports** - Periodic snapshots of metadata
2. **Analytics workloads** - Complex queries across millions of files
3. **Data sharing** - Export subsets for analysis
4. **NOT primary storage** - Always secondary to file metadata

```python
def export_to_parquet(self, output_path: Path, query: str = None):
    """Export metadata to Parquet for analytics."""
    if query:
        df = self.conn.execute(query).df()
    else:
        df = self.conn.execute("SELECT * FROM assets").df()
    
    df.to_parquet(
        output_path,
        engine='duckdb',
        compression='zstd'
    )
```

## Workflow Example

### 1. New File Added

```python
# User adds new AI-generated image
file_path = Path("inbox/cyberpunk_woman.jpg")

# Alice processes it
async def process_new_file(file_path: Path):
    # 1. Calculate content hash
    content_hash = calculate_hash(file_path)
    
    # 2. Extract any existing metadata
    existing_metadata = extract_metadata(file_path)
    
    # 3. Run AI understanding
    understanding = await analyze_image(file_path)
    
    # 4. Embed all metadata back into file
    embed_metadata(file_path, {
        "content_hash": content_hash,
        "understanding": understanding,
        "existing": existing_metadata,
        "processed_at": datetime.now()
    })
    
    # 5. Update DuckDB cache
    duckdb.upsert_asset(content_hash, file_path, understanding)
    
    # 6. File can now be moved anywhere - it's self-contained
```

### 2. File Moved to Different Location

```python
# User moves file to external drive
shutil.move(
    "inbox/cyberpunk_woman.jpg",
    "/Volumes/External/AI/cyberpunk_woman.jpg"
)

# Later, Alice scans the external drive
async def scan_location(path: Path):
    for file_path in path.rglob("*"):
        metadata = extract_metadata(file_path)
        content_hash = metadata.get("alice:content_hash")
        
        # Update location in DuckDB
        duckdb.add_file_location(
            content_hash,
            file_path,
            storage_type="external"
        )
```

### 3. Rebuild Cache from Scratch

```python
# DuckDB database corrupted or lost? No problem!
async def rebuild_entire_cache():
    # Clear existing cache
    duckdb.execute("DELETE FROM assets")
    
    # Scan all configured locations
    for location in config.storage_locations:
        await scan_location(location.path)
    
    # Cache is now rebuilt from files
    print(f"Rebuilt cache with {duckdb.count()} assets")
```

## Benefits of This Approach

1. **True Portability** - Files contain everything needed
2. **No Lock-in** - Standard metadata formats
3. **Resilient** - Database can always be rebuilt
4. **Flexible Storage** - Files can live anywhere
5. **Version Control Friendly** - Metadata travels with files
6. **Backup Simple** - Just backup files, not database
7. **Tool Agnostic** - Other tools can read metadata

## Implementation Priorities

1. **Metadata Embedding** - Ensure all data goes into files
2. **Content Hash Tracking** - Identify files regardless of name/location
3. **DuckDB Cache** - Fast search without being critical
4. **Location Registry** - Track where files are
5. **Parquet Export** - For advanced analytics only

## What We DON'T Do

1. **No JSON sidecar files** - Everything in file metadata
2. **No database as source of truth** - Cache only
3. **No proprietary formats** - Standard metadata fields
4. **No required online connection** - Works offline
5. **No centralized storage requirement** - Fully distributed