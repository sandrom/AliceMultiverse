# Architecture Overview

AliceMultiverse is designed as a modular, extensible system for organizing AI-generated media. This document provides a comprehensive overview of the system architecture, design decisions, and technical implementation details.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Input Layer"
        IN[Inbox Directory]
        WATCH[File System Watcher]
    end
    
    subgraph "Core Processing"
        ORG[Media Organizer]
        DETECT[AI Detector]
        CACHE[(Metadata Cache)]
    end
    
    subgraph "Quality Pipeline"
        BRISQUE[BRISQUE Scorer]
        SIGHT[SightEngine API]
        CLAUDE[Claude Vision API]
    end
    
    subgraph "Output Layer"
        OUT[Organized Directory]
        STATS[Statistics]
    end
    
    IN --> ORG
    WATCH --> ORG
    ORG --> DETECT
    ORG <--> CACHE
    ORG --> BRISQUE
    BRISQUE --> SIGHT
    SIGHT --> CLAUDE
    ORG --> OUT
    ORG --> STATS
    
    style ORG fill:#f9f,stroke:#333,stroke-width:4px
    style CACHE fill:#bbf,stroke:#333,stroke-width:2px
```

## Core Components

### 1. Media Organizer (`alicemultiverse.organizer`)

The heart of the system, responsible for:
- File discovery and filtering
- Orchestrating the processing pipeline
- Managing file operations (copy/move)
- Statistics tracking

**Design Decision**: We chose a single orchestrator pattern rather than a distributed system because:
- Media files are processed independently
- Local file operations are the bottleneck, not processing
- Simpler to understand and maintain

### 2. AI Detection System

Identifies the AI tool used to generate content through:
- Filename pattern matching
- Metadata inspection
- Fallback to generic categorization

**Design Decision**: Pattern-based detection over ML classification because:
- AI tools have distinct naming conventions
- Zero runtime cost
- Easy to extend with new patterns
- No training data required

### 3. Quality Assessment Pipeline

Progressive quality filtering through multiple stages:

```mermaid
graph LR
    A[All Images] -->|BRISQUE| B[4-5 Star Images]
    B -->|SightEngine| C[High Quality]
    C -->|Claude Vision| D[No Defects]
    
    A -.->|Failed| E[1-3 Star]
    B -.->|Issues| F[Quality Issues]
    C -.->|Defects| G[AI Defects]
```

**Design Decision**: Progressive filtering reduces costs:
- BRISQUE: Free, filters ~60% of images
- SightEngine: $0.001/image, filters ~20% more
- Claude: ~$0.02/image, only for best candidates

### 4. Metadata Cache

Content-based caching system with:
- SHA256 content hashing
- Sharded storage (first 2 chars of hash)
- Persistent JSON storage
- Cache statistics tracking

**Design Decision**: Content-based over path-based caching because:
- Files can be moved/renamed without cache invalidation
- Duplicate detection across different locations
- More robust for long-term storage

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Organizer
    participant Cache
    participant Quality
    participant FileOps
    
    User->>CLI: alice --quality inbox/
    CLI->>Organizer: organize()
    
    loop For each media file
        Organizer->>Cache: check_cache(file)
        alt Cache Hit
            Cache-->>Organizer: cached_metadata
        else Cache Miss
            Organizer->>Quality: assess_quality(file)
            Quality-->>Organizer: quality_score
            Organizer->>Cache: save_metadata()
        end
        Organizer->>FileOps: copy/move file
    end
    
    Organizer-->>CLI: statistics
    CLI-->>User: summary report
```

## Directory Structure

### Input Structure
```
inbox/
└── project-name/
    ├── image1.png
    ├── image2_midjourney_v5.jpg
    └── video_runway_gen2.mp4
```

### Output Structure
```
organized/
└── 2024-03-15/                    # Date
    └── project-name/              # Project
        ├── midjourney/            # AI Source
        │   ├── 5-star/           # Quality
        │   │   └── project-00001.jpg
        │   └── 4-star/
        │       └── project-00002.jpg
        └── runway/
            └── project-00001.mp4
```

**Design Decisions**:
1. **Date-first hierarchy**: Enables chronological browsing
2. **Project preservation**: Maintains creative context
3. **Source segregation**: Easy to compare AI tools
4. **Quality folders**: Optional, best content surfaces
5. **Sequential naming**: Avoids conflicts, maintains order

## Performance Considerations

### Caching Strategy

```mermaid
graph LR
    A[File Input] --> B{Content Changed?}
    B -->|No| C[Use Cache]
    B -->|Yes| D[Process File]
    D --> E[Update Cache]
    C --> F[Organize]
    E --> F
```

- **O(1) cache lookups** via hash-based storage
- **Sharded directories** prevent filesystem limitations
- **Lazy loading** for large collections

### Scalability

The system scales to handle:
- **100,000+ files** tested in production
- **Parallel processing** possible (not implemented)
- **Incremental updates** via watch mode
- **Bounded memory usage** through streaming

## Security Considerations

### API Key Management

```mermaid
graph TB
    A[API Keys] --> B{Storage Method}
    B -->|Secure| C[macOS Keychain]
    B -->|Convenient| D[Environment Vars]
    B -->|Portable| E[Config File]
    
    C --> F[Best Security]
    D --> G[CI/CD Friendly]
    E --> H[Team Sharing]
```

**Design Decision**: Multiple storage options because:
- Different security requirements
- Platform-specific capabilities
- Team collaboration needs

## Extension Points

### 1. Custom AI Detectors
```python
def detect_custom_ai(filename: str, metadata: dict) -> Optional[str]:
    """Add custom AI detection logic"""
    if "my_custom_ai" in filename:
        return "CustomAI"
    return None
```

### 2. Additional Quality Stages
```python
class CustomQualityStage:
    def assess(self, image_path: Path) -> QualityResult:
        """Implement custom quality check"""
        pass
```

### 3. Output Formatters
```python
class CustomOrganizer:
    def build_path(self, analysis: dict) -> Path:
        """Custom organization structure"""
        pass
```

## Technology Stack

- **Python 3.8+**: Modern Python features
- **Pillow**: Image processing
- **OpenCV**: BRISQUE implementation
- **Click**: CLI framework
- **OmegaConf**: Configuration management
- **tqdm**: Progress bars
- **pytest**: Testing framework

## Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: Easy to add new AI detectors or quality stages
3. **Performance**: Cache everything expensive
4. **Usability**: Sensible defaults, optional complexity
5. **Reliability**: Graceful error handling, never lose data

## Future Considerations

- **Distributed Processing**: For very large collections
- **Web Interface**: For non-technical users
- **Cloud Storage**: S3/GCS integration
- **Real-time Monitoring**: WebSocket updates
- **ML Enhancement**: Automatic pattern learning