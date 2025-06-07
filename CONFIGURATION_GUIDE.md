# Configuration Guide

This guide explains how to use the centralized configuration system in AliceMultiverse.

## Overview

The configuration system provides:
- Default values in `core/defaults.yaml`
- Environment variable overrides
- Programmatic access via `ConfigLoader`
- Type-safe value parsing

## Configuration Structure

### Default Configuration File

The default configuration is stored in `alicemultiverse/core/defaults.yaml`:

```yaml
providers:
  openai:
    base_url: "https://api.openai.com/v1"
    timeout: 120
    max_retries: 3

services:
  web_server:
    host: "0.0.0.0"
    port: 8000

storage:
  default_inbox: "inbox"
  default_organized: "organized"
```

## Using the Configuration

### Basic Usage

```python
from alicemultiverse.core.config_loader import get_config

config = get_config()

# Get a single value
base_url = config.get("providers.openai.base_url")

# Get with default
timeout = config.get("providers.openai.timeout", 60)

# Get provider configuration
openai_config = config.get_provider_config("openai")
# Returns: {"base_url": "...", "timeout": 120, "max_retries": 3}
```

### In Provider Classes

```python
class MyProvider(Provider):
    # Load configuration at class level
    _config = get_config()
    
    # Use configuration values
    BASE_URL = _config.get("providers.myprovider.base_url", "https://default.url")
    TIMEOUT = _config.get("providers.myprovider.timeout", 120)
    
    def __init__(self, **kwargs):
        # Allow instance overrides
        self.timeout = kwargs.get("timeout", self.TIMEOUT)
```

### Environment Variable Overrides

All configuration values can be overridden using environment variables:

```bash
# Override provider settings
export ALICE_PROVIDERS_OPENAI_BASE_URL="https://custom.openai.com"
export ALICE_PROVIDERS_OPENAI_TIMEOUT=300

# Override service settings
export ALICE_SERVICES_WEB_SERVER_PORT=8080
export ALICE_SERVICES_METRICS_SERVER_HOST="127.0.0.1"

# Override storage settings
export ALICE_STORAGE_DEFAULT_INBOX="/custom/inbox"
export ALICE_STORAGE_MAX_FILE_SIZE=52428800  # 50MB
```

### Environment Variable Naming

Configuration paths are converted to environment variables using these rules:
- Prefix with `ALICE_`
- Convert dots to underscores
- Convert to uppercase

Examples:
- `providers.openai.base_url` → `ALICE_PROVIDERS_OPENAI_BASE_URL`
- `services.web_server.port` → `ALICE_SERVICES_WEB_SERVER_PORT`
- `storage.max_file_size` → `ALICE_STORAGE_MAX_FILE_SIZE`

## Type Conversion

The configuration loader automatically converts string values:

### Booleans
- `"true"`, `"yes"`, `"1"`, `"on"` → `True`
- `"false"`, `"no"`, `"0"`, `"off"` → `False`

### Numbers
- `"123"` → `123` (integer)
- `"123.45"` → `123.45` (float)

### Paths
- `"~/path"` → Expanded to full path

## Migration Examples

### Before (Hardcoded)
```python
class FalProvider(Provider):
    BASE_URL = "https://fal.run"
    TIMEOUT = 300
    POLL_INTERVAL = 5
```

### After (Configuration-based)
```python
class FalProvider(Provider):
    _config = get_config()
    BASE_URL = _config.get("providers.fal.base_url", "https://fal.run")
    TIMEOUT = _config.get("providers.fal.timeout", 300)
    POLL_INTERVAL = _config.get("providers.fal.poll_interval", 5)
```

## Best Practices

### 1. Use Descriptive Paths
```python
# Good
config.get("providers.openai.base_url")
config.get("services.web_server.port")

# Bad
config.get("openai_url")
config.get("port")
```

### 2. Always Provide Defaults
```python
# Good - provides fallback
timeout = config.get("providers.myservice.timeout", 120)

# Bad - might return None
timeout = config.get("providers.myservice.timeout")
```

### 3. Group Related Settings
```yaml
# Good - grouped by service
services:
  web_server:
    host: "0.0.0.0"
    port: 8000
    max_connections: 100

# Bad - flat structure
web_server_host: "0.0.0.0"
web_server_port: 8000
web_server_max_connections: 100
```

### 4. Document Environment Variables
```python
class MyProvider(Provider):
    """Provider for MyService.
    
    Environment variables:
        ALICE_PROVIDERS_MYSERVICE_BASE_URL: API base URL
        ALICE_PROVIDERS_MYSERVICE_TIMEOUT: Request timeout in seconds
    """
```

## Testing with Configuration

### Override for Tests
```python
def test_my_provider():
    # Set test environment
    os.environ["ALICE_PROVIDERS_MYSERVICE_BASE_URL"] = "http://localhost:8000"
    
    # Test will use the override
    provider = MyProvider()
    assert provider.BASE_URL == "http://localhost:8000"
```

### Mock Configuration
```python
from unittest.mock import patch

@patch("alicemultiverse.core.config_loader.get_config")
def test_with_mock_config(mock_config):
    mock_config.return_value.get.return_value = "test_value"
    # ... rest of test
```

## Adding New Configuration

1. **Add to defaults.yaml**:
   ```yaml
   myservice:
     api_url: "https://api.myservice.com"
     rate_limit: 100
   ```

2. **Use in code**:
   ```python
   config = get_config()
   api_url = config.get("myservice.api_url")
   ```

3. **Document environment variables**:
   ```
   ALICE_MYSERVICE_API_URL - Override API URL
   ALICE_MYSERVICE_RATE_LIMIT - Override rate limit
   ```

## Benefits

1. **Centralized Management**: All configuration in one place
2. **Environment Flexibility**: Easy to override for different environments
3. **Type Safety**: Automatic type conversion
4. **Backwards Compatible**: Can be added incrementally
5. **Self-Documenting**: Clear structure shows available options

## Future Enhancements

- Schema validation for configuration values
- Configuration reload without restart
- Configuration profiles (dev, staging, prod)
- Encrypted secrets management
- Configuration UI/CLI tool