# Storage Architecture

AliceMultiverse uses a file-first storage approach designed for simplicity, portability, and reliability.

## Key Documents

- **[File-Based Storage](file-based-storage.md)** - Complete guide to the file-first architecture
- **[Multi-Path Storage](../multi-path-storage-design.md)** - Managing assets across multiple locations
- **[DuckDB Migration](../duckdb-migration-plan.md)** - Search index implementation

## Core Principles

1. **Files as Truth**: All data lives with your media files
2. **Content Addressing**: SHA-256 hashes identify files regardless of location
3. **Embedded Search**: DuckDB provides fast search without a server
4. **Optional Events**: File-based by default, Redis when scaling

## Storage Hierarchy

```
~/Pictures/AI/
├── .metadata/              # Content-addressed metadata
│   ├── ab/abcdef...json   # Metadata by content hash
│   └── cd/cdef...json
├── organized/              # Date/project/source structure
│   └── 2025-01-06/
│       └── my-project/
│           └── midjourney/
└── projects/               # Self-contained projects
    └── video-2025/
        ├── project.yaml
        ├── created/
        └── selected/
```

## Why File-First?

- **Portable**: Move folders anywhere, metadata follows
- **Simple**: No database servers to manage
- **Reliable**: Standard filesystem backups work
- **Offline**: Everything works without internet
- **Yours**: Your data isn't locked in a database