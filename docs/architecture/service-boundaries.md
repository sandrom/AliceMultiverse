# Service Boundaries

## Overview

This document defines clear boundaries between services in the AliceMultiverse ecosystem. Each service has a specific responsibility and communicates through well-defined interfaces.

## Core Services

### Alice Interface Service
**Responsibility**: API gateway and orchestration

**Does**:
- Expose unified REST/GraphQL API
- Route requests to appropriate services
- Orchestrate multi-service workflows
- Manage authentication and authorization
- Aggregate responses from multiple services

**Does NOT**:
- Process media files directly
- Make quality judgments
- Store metadata
- Understand natural language

**Interfaces**:
- Ingress: REST API, GraphQL endpoint
- Egress: Event bus, service HTTP clients

---

### Asset Processor Service
**Responsibility**: Media file analysis and organization

**Does**:
- Detect AI generation source
- Extract technical metadata
- Plan file organization
- Process media formats (images, video)
- Generate thumbnails

**Does NOT**:
- Make quality assessments
- Store files permanently
- Search across assets
- Manage user preferences

**Interfaces**:
- Ingress: HTTP API, event subscriptions
- Egress: Event publications, storage API calls

---

### Quality Analyzer Service
**Responsibility**: Media quality assessment

**Does**:
- Calculate BRISQUE scores
- Integrate with SightEngine API
- Integrate with Claude for defect detection
- Combine scores into star ratings
- Cache quality assessments

**Does NOT**:
- Organize files
- Extract non-quality metadata
- Make creative judgments
- Generate content

**Interfaces**:
- Ingress: HTTP API, event subscriptions  
- Egress: Event publications, external API calls

---

### Metadata Extractor Service
**Responsibility**: Deep metadata extraction and enrichment

**Does**:
- Extract EXIF/XMP/technical metadata
- Parse AI tool parameters
- Generate embeddings for similarity
- Extract text from images (OCR)
- Identify objects and scenes

**Does NOT**:
- Judge quality
- Organize files
- Make creative decisions
- Store files

**Interfaces**:
- Ingress: HTTP API, event subscriptions
- Egress: Event publications, AI service calls

---

### Search Service
**Responsibility**: Asset discovery and retrieval

**Does**:
- Index metadata from all services
- Execute structured queries
- Rank results by relevance
- Provide faceted search
- Handle pagination

**Does NOT**:
- Understand natural language
- Modify assets
- Make quality judgments
- Generate metadata

**Interfaces**:
- Ingress: HTTP API (structured queries only)
- Egress: Read from metadata stores

---

### Storage Service
**Responsibility**: Content-addressed file storage

**Does**:
- Store files by content hash
- Provide retrieval by hash
- Handle different storage backends
- Manage storage quotas
- Ensure data integrity

**Does NOT**:
- Understand file contents
- Make organizational decisions
- Process or transform files
- Search within files

**Interfaces**:
- Ingress: HTTP API for store/retrieve
- Egress: Various storage backends (S3, local, etc.)

---

### Workflow Engine Service
**Responsibility**: Complex workflow orchestration

**Does**:
- Execute multi-step workflows
- Handle conditional logic
- Manage workflow state
- Retry failed steps
- Provide workflow templates

**Does NOT**:
- Perform actual processing
- Make creative decisions
- Store results
- Understand content

**Interfaces**:
- Ingress: HTTP API, event subscriptions
- Egress: Service API calls, event publications

## Communication Patterns

### Synchronous (HTTP)
Used for:
- Direct API calls requiring immediate response
- Simple request-response patterns
- Health checks and status endpoints

### Asynchronous (Events)
Used for:
- Long-running operations
- Multi-service workflows
- State changes and notifications
- Loose coupling between services

### Event Examples
```yaml
# Asset discovered by processor
asset.discovered:
  asset_id: "sha256:abc..."
  path: "/inbox/project/image.png"
  type: "image/png"

# Quality assessed by analyzer  
quality.assessed:
  asset_id: "sha256:abc..."
  scores:
    brisque: 35.2
    sightengine: 0.89
  star_rating: 4

# Metadata extracted
metadata.extracted:
  asset_id: "sha256:abc..."
  ai_source: "midjourney"
  prompt: "cyberpunk city at night"
  parameters: {...}
```

## Service Interactions

### Example: Process New Asset
```
1. Asset Processor discovers file
   → Publishes: asset.discovered
   
2. Quality Analyzer receives event
   → Assesses quality
   → Publishes: quality.assessed
   
3. Metadata Extractor receives event
   → Extracts metadata
   → Publishes: metadata.extracted
   
4. Search Service receives all events
   → Updates search index
   
5. Alice Interface aggregates results
   → Returns unified response to client
```

## Boundary Violations (Anti-patterns)

### ❌ Service Doing Too Much
```python
# BAD: Asset Processor making quality judgments
class AssetProcessor:
    def process(self, file):
        metadata = self.extract_metadata(file)
        quality = self.assess_quality(file)  # WRONG!
        return metadata, quality
```

### ❌ Direct Service Dependencies
```python
# BAD: Quality Analyzer calling Asset Processor directly
class QualityAnalyzer:
    def __init__(self):
        self.processor = AssetProcessor()  # WRONG!
    
    def analyze(self, file):
        metadata = self.processor.get_metadata(file)
```

### ❌ Natural Language in Alice
```python
# BAD: Alice interpreting user intent
@app.post("/search")
def search(query: str):
    if "high quality" in query:  # WRONG!
        filters = {"min_quality": 4}
```

## Best Practices

### 1. Single Responsibility
Each service should do one thing well. If you're using "and" to describe what a service does, it might be doing too much.

### 2. Event-Driven by Default
Use events for anything that:
- Other services might care about
- Could be async
- Represents a state change

### 3. Structured Interfaces
All API contracts should be:
- Strongly typed
- Versioned
- Well-documented
- Backward compatible

### 4. Stateless Operations
Services should be stateless where possible. State belongs in:
- Dedicated storage services
- Event streams
- External databases

### 5. Clear Dependencies
- Services depend on interfaces, not implementations
- Use service discovery, not hardcoded URLs
- Version your APIs explicitly

## Evolution Guidelines

When to create a new service:
1. **Cohesive functionality** that's currently split
2. **Reusable capability** needed by multiple services
3. **Different scaling needs** than existing services
4. **External integration** that needs isolation
5. **Complex processing** that would bloat existing services

When to merge services:
1. **Chatty communication** between two services
2. **Shared data model** with high coupling
3. **Single deployment** always needed
4. **Artificial boundaries** that complicate things

## Future Services (Planned)

### Creative Engine Service
- Generate content via AI tools
- Manage generation parameters
- Handle tool-specific APIs

### Project Manager Service  
- Organize assets into projects
- Track project metadata
- Manage project templates

### User Preference Service
- Store user settings
- Manage quality thresholds
- Track usage patterns

### Export Service
- Package assets for delivery
- Generate contact sheets
- Create portfolios

Each new service should:
1. Have a clear, single responsibility
2. Communicate via events and APIs
3. Respect existing service boundaries
4. Add value without adding coupling