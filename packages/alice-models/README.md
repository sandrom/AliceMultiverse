# alice-models

Shared data models and types for AliceMultiverse.

## Installation

```bash
pip install -e packages/alice-models
```

## Usage

```python
from alice_models import (
    Asset,
    Project,
    MediaType,
    QualityRating,
    WorkflowState
)

# Create an asset
asset = Asset(
    content_hash="abc123",
    file_path="/path/to/image.jpg",
    media_type=MediaType.IMAGE,
    file_size=1024000,
    project_name="my-project"
)

# Create a project
project = Project(
    id="proj-123",
    name="My Creative Project",
    description="A test project",
    style_preferences={"theme": "dark"}
)
```

## Model Categories

- **Core Models**: Asset, Project, Workflow
- **Enums**: MediaType, QualityRating, WorkflowState
- **Value Objects**: ContentHash, FilePath, Metadata

## Database Models

SQLAlchemy models for persistence:

```python
from alice_models.db import AssetDB, ProjectDB

# Use with SQLAlchemy session
asset_db = AssetDB(content_hash="abc123", ...)
session.add(asset_db)
session.commit()
```