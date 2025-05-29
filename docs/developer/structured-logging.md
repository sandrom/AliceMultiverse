# Structured Logging Guide

AliceMultiverse uses structured logging with correlation IDs for distributed tracing and better observability.

## Overview

Features:
- **Structured logs** in JSON or console format
- **Correlation IDs** for tracing requests across services
- **Automatic context** (service, timestamp, caller info)
- **Sensitive data redaction**
- **Performance tracking** for operations
- **Slow query detection**

## Usage

### Basic Logging

```python
from alicemultiverse.core.structured_logging import get_logger

logger = get_logger(__name__)

# Log with structured data
logger.info(
    "Processing asset",
    asset_id="abc123",
    media_type="image",
    size_mb=5.2
)

# Log errors with context
try:
    result = process_asset(asset)
except Exception as e:
    logger.error(
        "Asset processing failed",
        asset_id=asset.id,
        error_type=type(e).__name__,
        exc_info=True  # Include stack trace
    )
```

### Correlation IDs

Every request gets a unique correlation ID for tracing:

```python
from alicemultiverse.core.structured_logging import CorrelationContext

# Set correlation ID for a block of code
with CorrelationContext("user-provided-id"):
    # All logs in this block will have this correlation ID
    logger.info("Starting operation")
    await process_data()
    logger.info("Operation complete")
```

### Operation Tracing

Use decorators to automatically trace operations:

```python
from alicemultiverse.core.structured_logging import trace_operation

@trace_operation("asset_analysis")
async def analyze_asset(asset_id: str):
    # Automatically logs:
    # - Operation start with parameters
    # - Duration on completion
    # - Errors with stack trace
    return await perform_analysis(asset_id)
```

### API Call Logging

Special decorator for external API calls:

```python
from alicemultiverse.core.structured_logging import log_api_call

@log_api_call(provider="openai", model="gpt-4", operation="completion")
async def call_gpt4(prompt: str):
    # Logs provider, model, duration, cost, success/failure
    return await openai_client.complete(prompt)
```

## Configuration

### CLI Options

```bash
# JSON logs for production
alice --log-format json --log-level INFO

# Console logs with debug info
alice --log-format console --log-level DEBUG

# Minimal logging
alice --log-level ERROR
```

### Programmatic Setup

```python
from alicemultiverse.core.structured_logging import setup_structured_logging

# Production configuration
setup_structured_logging(
    log_level="INFO",
    json_logs=True,
    include_caller_info=False
)

# Development configuration
setup_structured_logging(
    log_level="DEBUG",
    json_logs=False,
    include_caller_info=True
)
```

## Log Format

### JSON Format (Production)

```json
{
  "timestamp": "2025-01-29T10:30:45.123Z",
  "level": "INFO",
  "logger": "alicemultiverse.providers.fal_provider",
  "message": "API call completed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "service": "alicemultiverse",
  "provider": "fal.ai",
  "model": "flux-schnell",
  "duration_seconds": 2.34,
  "cost": 0.003,
  "success": true
}
```

### Console Format (Development)

```
2025-01-29 10:30:45 [INFO] alicemultiverse.providers.fal_provider: API call completed
    correlation_id: 550e8400-e29b-41d4-a716-446655440000
    provider: fal.ai
    model: flux-schnell
    duration_seconds: 2.34
    cost: 0.003
    success: true
```

## Middleware Integration

### FastAPI Middleware

For API services, add correlation ID middleware:

```python
from fastapi import FastAPI
from alicemultiverse.core.logging_middleware import StructuredLoggingMiddleware

app = FastAPI()
app.add_middleware(StructuredLoggingMiddleware)

# Now all requests get:
# - Unique correlation IDs
# - Request/response logging
# - Duration tracking
```

### Database Query Logging

Enable slow query detection:

```python
from alicemultiverse.core.logging_middleware import setup_sqlalchemy_logging
from alicemultiverse.database.config import engine

# Log queries taking > 1 second
setup_sqlalchemy_logging(engine)
```

## Best Practices

### 1. Use Structured Data

```python
# Good - structured data
logger.info(
    "Asset processed",
    asset_id=asset.id,
    duration=2.5,
    quality_score=0.85
)

# Bad - unstructured string
logger.info(f"Processed asset {asset.id} in 2.5s with score 0.85")
```

### 2. Include Context

```python
# Bind context to logger for multiple operations
asset_logger = logger.bind(
    asset_id=asset.id,
    project_id=project.id
)

asset_logger.info("Starting processing")
# ... operations ...
asset_logger.info("Processing complete")
```

### 3. Use Appropriate Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General operational messages
- **WARNING**: Warning conditions that should be reviewed
- **ERROR**: Error conditions that need attention
- **CRITICAL**: Critical failures requiring immediate action

### 4. Avoid Logging Sensitive Data

The system automatically redacts fields containing:
- password
- api_key
- secret
- token
- authorization
- credit_card
- ssn
- private_key

```python
# This will be redacted automatically
logger.info(
    "API configured",
    api_key="sk-1234567890",  # Logged as "***REDACTED***"
    endpoint="https://api.example.com"
)
```

## Monitoring Integration

### Prometheus Metrics

Structured logs can be parsed for metrics:

```python
from prometheus_client import Counter, Histogram

# Track API calls from logs
api_calls = Counter(
    'alice_api_calls_total',
    'Total API calls',
    ['provider', 'model', 'status']
)

api_duration = Histogram(
    'alice_api_duration_seconds',
    'API call duration',
    ['provider', 'model']
)
```

### Log Aggregation

For production, send logs to aggregation services:

```bash
# Send to Elasticsearch
alice --log-format json | logstash -f alice.conf

# Send to CloudWatch
alice --log-format json | aws logs put-log-events

# Send to Datadog
alice --log-format json | datadog-agent
```

## Troubleshooting

### Missing Correlation IDs

If correlation IDs are missing:
1. Ensure middleware is installed for web services
2. Check that context is properly propagated in async code
3. Use `CorrelationContext` for background tasks

### Performance Impact

Structured logging has minimal overhead:
- ~0.1ms per log statement
- Caller info adds ~0.5ms (disable in production)
- JSON formatting is optimized

### Large Log Files

For high-volume logging:
1. Use appropriate log levels
2. Implement log rotation
3. Consider sampling for debug logs
4. Use centralized logging

## Examples

### Complete Request Flow

```python
from alicemultiverse.core.structured_logging import (
    get_logger, 
    CorrelationContext,
    trace_operation
)

logger = get_logger(__name__)

@trace_operation("process_user_request")
async def handle_request(user_id: str, request_data: dict):
    # Create correlation context
    with CorrelationContext() as correlation_id:
        logger.info(
            "Request received",
            user_id=user_id,
            request_type=request_data.get("type")
        )
        
        try:
            # Process request
            result = await process_data(request_data)
            
            logger.info(
                "Request completed",
                user_id=user_id,
                result_count=len(result)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Request failed",
                user_id=user_id,
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
```

### Background Task Logging

```python
import asyncio
from alicemultiverse.core.structured_logging import get_logger, CorrelationContext

logger = get_logger(__name__)

async def background_task(task_id: str):
    # Create new correlation context for background task
    with CorrelationContext(f"task-{task_id}"):
        logger.info("Background task started", task_id=task_id)
        
        try:
            await perform_work()
            logger.info("Background task completed", task_id=task_id)
        except Exception as e:
            logger.error(
                "Background task failed",
                task_id=task_id,
                exc_info=True
            )
```