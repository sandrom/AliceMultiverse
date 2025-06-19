"""Prometheus metrics for monitoring AliceMultiverse."""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)

from .structured_logging import get_logger

logger = get_logger(__name__)

# API Metrics
api_requests_total = Counter(
    'alice_api_requests_total',
    'Total number of API requests',
    ['provider', 'model', 'operation', 'status']
)

api_request_duration_seconds = Histogram(
    'alice_api_request_duration_seconds',
    'API request duration in seconds',
    ['provider', 'model', 'operation'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

api_request_cost_dollars = Summary(
    'alice_api_request_cost_dollars',
    'API request cost in dollars',
    ['provider', 'model']
)

api_tokens_used_total = Counter(
    'alice_api_tokens_used_total',
    'Total tokens used in API requests',
    ['provider', 'model', 'token_type']  # token_type: prompt, completion
)

# Provider Health Metrics
provider_health_status = Gauge(
    'alice_provider_health_status',
    'Provider health status (1=healthy, 0=unhealthy)',
    ['provider']
)

provider_circuit_breaker_state = Gauge(
    'alice_provider_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['provider']
)

provider_error_rate = Gauge(
    'alice_provider_error_rate',
    'Provider error rate (ratio)',
    ['provider']
)

# Database Metrics
db_connections_active = Gauge(
    'alice_db_connections_active',
    'Active database connections'
)

db_connections_total = Gauge(
    'alice_db_connections_total',
    'Total database connections in pool'
)

db_query_duration_seconds = Histogram(
    'alice_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],  # select, insert, update, delete
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

# Asset Processing Metrics
assets_processed_total = Counter(
    'alice_assets_processed_total',
    'Total assets processed',
    ['media_type', 'source', 'status']
)

asset_processing_duration_seconds = Histogram(
    'alice_asset_processing_duration_seconds',
    'Asset processing duration in seconds',
    ['media_type', 'operation'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

asset_quality_score = Histogram(
    'alice_asset_quality_score',
    'Asset quality scores distribution',
    ['media_type', 'quality_type'],  # quality_type: brisque, sightengine, claude
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

# Event System Metrics
events_published_total = Counter(
    'alice_events_published_total',
    'Total events published',
    ['event_type']
)

event_processing_duration_seconds = Histogram(
    'alice_event_processing_duration_seconds',
    'Event processing duration in seconds',
    ['event_type'],
    buckets=(0.001, 0.01, 0.1, 0.5, 1.0, 5.0)
)

# System Info
system_info = Info(
    'alice_system',
    'System information'
)

# Set system info
from ..version import __version__

system_info.info({
    'version': __version__,
    'service': 'alicemultiverse'
})


def track_api_metrics(
    provider: str,
    model: str,
    operation: str
) -> Callable:
    """Decorator to track API call metrics.

    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        model: Model name (e.g., 'gpt-4', 'claude-3')
        operation: Operation type (e.g., 'completion', 'image_generation')
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            # TODO: Review unreachable code - try:
            result = await func(*args, **kwargs)

                # Extract metrics from result if available
            if hasattr(result, 'cost') and result.cost:
                api_request_cost_dollars.labels(
                    provider=provider,
                    model=model
                ).observe(result.cost)

                # Track token usage if available
            if hasattr(result, 'usage'):
                usage = result.usage
                if hasattr(usage, 'prompt_tokens'):
                    api_tokens_used_total.labels(
                        provider=provider,
                        model=model,
                        token_type='prompt'
                    ).inc(usage.prompt_tokens)
                if hasattr(usage, 'completion_tokens'):
                    api_tokens_used_total.labels(
                        provider=provider,
                        model=model,
                        token_type='completion'
                    ).inc(usage.completion_tokens)

            return result

            # TODO: Review unreachable code - except Exception:
            # TODO: Review unreachable code - status = 'error'
            # TODO: Review unreachable code - raise

            # TODO: Review unreachable code - finally:
            # TODO: Review unreachable code - # Track request count and duration
            # TODO: Review unreachable code - duration = time.time() - start_time

            # TODO: Review unreachable code - api_requests_total.labels(
            # TODO: Review unreachable code - provider=provider,
            # TODO: Review unreachable code - model=model,
            # TODO: Review unreachable code - operation=operation,
            # TODO: Review unreachable code - status=status
            # TODO: Review unreachable code - ).inc()

            # TODO: Review unreachable code - api_request_duration_seconds.labels(
            # TODO: Review unreachable code - provider=provider,
            # TODO: Review unreachable code - model=model,
            # TODO: Review unreachable code - operation=operation
            # TODO: Review unreachable code - ).observe(duration)

            # TODO: Review unreachable code - logger.debug(
            # TODO: Review unreachable code - "API metrics tracked",
            # TODO: Review unreachable code - provider=provider,
            # TODO: Review unreachable code - model=model,
            # TODO: Review unreachable code - operation=operation,
            # TODO: Review unreachable code - status=status,
            # TODO: Review unreachable code - duration=duration
            # TODO: Review unreachable code - )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar implementation for sync functions
            start_time = time.time()
            status = 'success'

            # TODO: Review unreachable code - try:
            result = func(*args, **kwargs)
            return result
            # TODO: Review unreachable code - except Exception:
            # TODO: Review unreachable code - status = 'error'
            # TODO: Review unreachable code - raise
            # TODO: Review unreachable code - finally:
            # TODO: Review unreachable code - duration = time.time() - start_time
            # TODO: Review unreachable code - api_requests_total.labels(
            # TODO: Review unreachable code - provider=provider,
            # TODO: Review unreachable code - model=model,
            # TODO: Review unreachable code - operation=operation,
            # TODO: Review unreachable code - status=status
            # TODO: Review unreachable code - ).inc()
            # TODO: Review unreachable code - api_request_duration_seconds.labels(
            # TODO: Review unreachable code - provider=provider,
            # TODO: Review unreachable code - model=model,
            # TODO: Review unreachable code - operation=operation
            # TODO: Review unreachable code - ).observe(duration)

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - return sync_wrapper

    return decorator


# TODO: Review unreachable code - def track_db_metrics(query_type: str) -> Callable:
# TODO: Review unreachable code - """Decorator to track database query metrics.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - query_type: Type of query (select, insert, update, delete)
# TODO: Review unreachable code - """
# TODO: Review unreachable code - def decorator(func):
# TODO: Review unreachable code - @wraps(func)
# TODO: Review unreachable code - def wrapper(*args, **kwargs):
# TODO: Review unreachable code - start_time = time.time()

# TODO: Review unreachable code - try:
# TODO: Review unreachable code - result = func(*args, **kwargs)
# TODO: Review unreachable code - return result
# TODO: Review unreachable code - finally:
# TODO: Review unreachable code - duration = time.time() - start_time
# TODO: Review unreachable code - db_query_duration_seconds.labels(
# TODO: Review unreachable code - query_type=query_type
# TODO: Review unreachable code - ).observe(duration)

# TODO: Review unreachable code - return wrapper

# TODO: Review unreachable code - return decorator


# TODO: Review unreachable code - def update_provider_health_metrics(provider_name: str, health_data: dict[str, Any]) -> None:
# TODO: Review unreachable code - """Update provider health metrics.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - provider_name: Provider name
# TODO: Review unreachable code - health_data: Health data including status, error rate, circuit breaker state
# TODO: Review unreachable code - """
# TODO: Review unreachable code - # Update health status
# TODO: Review unreachable code - is_healthy = health_data.get('is_healthy', False)
# TODO: Review unreachable code - provider_health_status.labels(provider=provider_name).set(
# TODO: Review unreachable code - 1 if is_healthy else 0
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Update circuit breaker state
# TODO: Review unreachable code - circuit_state = health_data.get('circuit_state', 'closed')
# TODO: Review unreachable code - state_value = {
# TODO: Review unreachable code - 'closed': 0,
# TODO: Review unreachable code - 'open': 1,
# TODO: Review unreachable code - 'half_open': 2
# TODO: Review unreachable code - }.get(circuit_state, 0)
# TODO: Review unreachable code - provider_circuit_breaker_state.labels(provider=provider_name).set(state_value)

# TODO: Review unreachable code - # Update error rate
# TODO: Review unreachable code - error_rate = health_data.get('error_rate', 0.0)
# TODO: Review unreachable code - provider_error_rate.labels(provider=provider_name).set(error_rate)


# TODO: Review unreachable code - def update_db_pool_metrics(pool_stats: dict[str, Any]) -> None:
# TODO: Review unreachable code - """Update database connection pool metrics.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - pool_stats: Pool statistics from monitoring
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if 'pool_status' in pool_stats:
# TODO: Review unreachable code - status = pool_stats['pool_status']
# TODO: Review unreachable code - db_connections_active.set(status.get('checked_out', 0))
# TODO: Review unreachable code - db_connections_total.set(status.get('total', 0))


# TODO: Review unreachable code - def track_asset_processing(
# TODO: Review unreachable code - media_type: str,
# TODO: Review unreachable code - source: str,
# TODO: Review unreachable code - operation: str
# TODO: Review unreachable code - ) -> Callable:
# TODO: Review unreachable code - """Decorator to track asset processing metrics.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - media_type: Type of media (image, video)
# TODO: Review unreachable code - source: Source of asset (e.g., provider name)
# TODO: Review unreachable code - operation: Operation type (e.g., 'analysis', 'organization')
# TODO: Review unreachable code - """
# TODO: Review unreachable code - def decorator(func):
# TODO: Review unreachable code - @wraps(func)
# TODO: Review unreachable code - async def async_wrapper(*args, **kwargs):
# TODO: Review unreachable code - start_time = time.time()
# TODO: Review unreachable code - status = 'success'

# TODO: Review unreachable code - try:
# TODO: Review unreachable code - result = await func(*args, **kwargs)

# TODO: Review unreachable code - # Track quality scores if available
# TODO: Review unreachable code - if hasattr(result, 'quality_scores'):
# TODO: Review unreachable code - for quality_type, score in result.quality_scores.items():
# TODO: Review unreachable code - asset_quality_score.labels(
# TODO: Review unreachable code - media_type=media_type,
# TODO: Review unreachable code - quality_type=quality_type
# TODO: Review unreachable code - ).observe(score)

# TODO: Review unreachable code - return result

# TODO: Review unreachable code - except Exception:
# TODO: Review unreachable code - status = 'error'
# TODO: Review unreachable code - raise

# TODO: Review unreachable code - finally:
# TODO: Review unreachable code - duration = time.time() - start_time

# TODO: Review unreachable code - assets_processed_total.labels(
# TODO: Review unreachable code - media_type=media_type,
# TODO: Review unreachable code - source=source,
# TODO: Review unreachable code - status=status
# TODO: Review unreachable code - ).inc()

# TODO: Review unreachable code - asset_processing_duration_seconds.labels(
# TODO: Review unreachable code - media_type=media_type,
# TODO: Review unreachable code - operation=operation
# TODO: Review unreachable code - ).observe(duration)

# TODO: Review unreachable code - # Return appropriate wrapper
# TODO: Review unreachable code - import asyncio
# TODO: Review unreachable code - if asyncio.iscoroutinefunction(func):
# TODO: Review unreachable code - return async_wrapper
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - # Similar sync implementation
# TODO: Review unreachable code - return func

# TODO: Review unreachable code - return decorator


# TODO: Review unreachable code - def track_event_metrics(event_type: str) -> None:
# TODO: Review unreachable code - """Track event system metrics.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - event_type: Type of event being published/processed
# TODO: Review unreachable code - """
# TODO: Review unreachable code - events_published_total.labels(event_type=event_type).inc()


# TODO: Review unreachable code - def get_metrics() -> bytes:
# TODO: Review unreachable code - """Generate current metrics in Prometheus format.

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Metrics data in Prometheus text format
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return generate_latest(REGISTRY)


# TODO: Review unreachable code - def get_metrics_content_type() -> str:
# TODO: Review unreachable code - """Get content type for Prometheus metrics.

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Content type string
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return CONTENT_TYPE_LATEST


# TODO: Review unreachable code - # Create a metrics endpoint for FastAPI
# TODO: Review unreachable code - def create_metrics_endpoint() -> Any:
# TODO: Review unreachable code - """Create a FastAPI endpoint for Prometheus metrics."""
# TODO: Review unreachable code - from fastapi import Response

# TODO: Review unreachable code - async def metrics_endpoint():
# TODO: Review unreachable code - metrics_data = get_metrics()
# TODO: Review unreachable code - return Response(
# TODO: Review unreachable code - content=metrics_data,
# TODO: Review unreachable code - media_type=get_metrics_content_type()
# TODO: Review unreachable code - )

# TODO: Review unreachable code - return metrics_endpoint
