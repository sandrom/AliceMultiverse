# alice-config

Configuration management utilities for AliceMultiverse.

## Installation

```bash
pip install -e packages/alice-config
```

## Usage

```python
from alice_config import Config, get_config, load_config

# Load configuration
config = load_config("config.yaml")

# Access configuration values
inbox_path = config.paths.inbox
quality_enabled = config.quality.enabled

# Override with environment variables
# ALICE_PATHS__INBOX=/custom/path
# ALICE_QUALITY__ENABLED=false

# Get global config instance
config = get_config()
```

## Features

- YAML configuration files
- Environment variable overrides
- Command-line argument support
- Type-safe configuration with Pydantic
- Service-specific configurations

## Configuration Schema

```yaml
# Base configuration
paths:
  inbox: ./inbox
  organized: ./organized

# Service configurations  
services:
  alice_interface:
    host: 0.0.0.0
    port: 8000
  
  asset_processor:
    batch_size: 100
    workers: 4

# Feature flags
features:
  quality_assessment: true
  event_persistence: true
```