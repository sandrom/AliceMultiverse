# Shared Packages

This directory contains shared packages used across all AliceMultiverse services.

## Structure

- **alice-events**: Event definitions and base infrastructure
- **alice-models**: Shared data models and types
- **alice-config**: Configuration management utilities
- **alice-utils**: Common utilities and helpers

## Usage

Services can import these packages directly:

```python
from alice_events import AssetDiscoveredEvent, publish_event
from alice_models import Asset, Project
from alice_config import get_config
from alice_utils import hash_content
```

## Development

Each package has its own:
- `pyproject.toml` for dependencies
- `README.md` for documentation
- Tests in `tests/` directory