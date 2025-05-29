# Provider Health Monitoring Guide

AliceMultiverse includes built-in health monitoring for AI providers with circuit breaker pattern to handle provider failures gracefully.

## Overview

The health monitoring system:
- Tracks success/failure rates for each provider
- Implements circuit breakers to prevent cascading failures
- Provides automatic recovery when providers come back online
- Exposes health check endpoints for monitoring
- Records detailed metrics for performance analysis

## Circuit Breaker Pattern

The circuit breaker has three states:

1. **CLOSED** (Normal): Requests flow through normally
2. **OPEN** (Failing): Requests are rejected immediately to prevent overload
3. **HALF_OPEN** (Testing): Limited requests test if service has recovered

### State Transitions

```
CLOSED → OPEN: After 5 consecutive failures
OPEN → HALF_OPEN: After 1 minute recovery timeout
HALF_OPEN → CLOSED: After 3 consecutive successes
HALF_OPEN → OPEN: After any failure
```

## Health Metrics

Each provider tracks:
- Total requests
- Failed requests
- Consecutive failures/successes
- Average response time
- Last success/failure time
- Overall health status

## Usage Examples

### Checking Provider Health

```python
from alicemultiverse.providers import get_provider

# Get provider instance
provider = get_provider("fal.ai")

# Check health status
status = provider.get_health_status()
print(f"Provider status: {status}")  # AVAILABLE, DEGRADED, or UNAVAILABLE

# Get detailed metrics
metrics = provider.get_health_metrics()
print(f"Failure rate: {metrics['failure_rate']:.2%}")
print(f"Avg response time: {metrics['average_response_time']:.2f}s")
```

### Starting Health Monitoring

```python
from alicemultiverse.providers import get_registry

registry = get_registry()

# Start automatic health monitoring
await registry.start_health_monitoring()

# Check all provider statuses
statuses = registry.get_health_statuses()
for provider, status in statuses.items():
    print(f"{provider}: {status}")
```

### Handling Circuit Breaker Errors

```python
from alicemultiverse.providers import get_provider, GenerationError

provider = get_provider("openai")

try:
    result = await provider.generate(request)
except GenerationError as e:
    if "circuit breaker open" in str(e):
        # Provider is temporarily unavailable
        # Try a different provider or wait
        fallback_provider = get_provider("anthropic")
        result = await fallback_provider.generate(request)
```

## Health Check Endpoints

When running the health API server:

```bash
# Start health monitoring API
python -m alicemultiverse.providers.health_endpoint
```

### Available Endpoints

#### GET /health
Overall system health check
```json
{
  "status": "healthy",
  "providers": {
    "fal.ai": "available",
    "openai": "available",
    "anthropic": "degraded"
  },
  "timestamp": "2025-01-29T10:30:00Z"
}
```

#### GET /health/providers
Detailed status for all providers
```json
{
  "providers": {
    "fal.ai": {
      "status": "available",
      "circuit_state": "closed",
      "metrics": {
        "total_requests": 1000,
        "failure_rate": 0.02,
        "average_response_time": 2.5
      }
    }
  }
}
```

#### GET /health/providers/{name}
Detailed status for specific provider

#### POST /health/providers/{name}/check
Manually trigger health check

#### POST /health/providers/{name}/reset
Reset circuit breaker (admin operation)

## Configuration

### Circuit Breaker Settings

Default configuration:
- **Failure threshold**: 5 consecutive failures
- **Recovery timeout**: 1 minute
- **Success threshold**: 3 consecutive successes

These can be customized per provider:

```python
from alicemultiverse.providers.health_monitor import health_monitor

# Get circuit breaker for a provider
breaker = health_monitor.get_or_create_breaker("openai")

# Customize settings
breaker.failure_threshold = 3  # Open after 3 failures
breaker.recovery_timeout = timedelta(minutes=5)  # Wait 5 minutes
breaker.success_threshold = 5  # Need 5 successes to close
```

### Monitoring Configuration

```python
# Set check interval (default: 60 seconds)
health_monitor._check_interval = 30  # Check every 30 seconds

# Add status change callbacks
def on_status_change(provider_name, new_status):
    print(f"{provider_name} status changed to {new_status}")
    # Send alert, update dashboard, etc.

health_monitor.add_status_callback(on_status_change)
```

## Best Practices

1. **Start monitoring early**: Initialize health monitoring when your application starts
2. **Use fallback providers**: Have backup providers for critical operations
3. **Monitor the monitors**: Set up alerts for circuit breaker state changes
4. **Tune thresholds**: Adjust based on provider reliability and your needs
5. **Log failures**: Track why providers fail to identify patterns

## Integration with Alice Orchestrator

The orchestrator automatically uses health monitoring:

```python
from alicemultiverse.interface import AliceOrchestrator

alice = AliceOrchestrator()

# Orchestrator checks provider health before routing requests
result = await alice.generate_creative_asset(request)
# Automatically tries healthy providers first
```

## Troubleshooting

### Provider Always Unavailable
- Check API keys are correctly configured
- Verify network connectivity
- Look at failure reasons in logs
- Manually reset circuit breaker if needed

### Slow Recovery
- Adjust recovery timeout for faster retry
- Check if provider has actual issues
- Monitor provider's status page

### High Failure Rates
- Review request parameters
- Check rate limits
- Verify API compatibility
- Consider increasing retry attempts

## Metrics Export

Export metrics for monitoring systems:

```python
from prometheus_client import Gauge, Counter

# Create Prometheus metrics
provider_health = Gauge(
    'alice_provider_health',
    'Provider health status (1=healthy, 0=unhealthy)',
    ['provider']
)

provider_requests = Counter(
    'alice_provider_requests_total',
    'Total provider requests',
    ['provider', 'status']
)

# Update metrics
for provider, status in registry.get_health_statuses().items():
    provider_health.labels(provider=provider).set(
        1 if status == "available" else 0
    )
```

## Future Enhancements

Planned improvements:
- Adaptive thresholds based on time of day
- Predictive failure detection
- Cost-aware circuit breaking
- Regional failover support
- WebSocket real-time health updates