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

            try:
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

            except Exception:
                status = 'error'
                raise

            finally:
                # Track request count and duration
                duration = time.time() - start_time

                api_requests_total.labels(
                    provider=provider,
                    model=model,
                    operation=operation,
                    status=status
                ).inc()

                api_request_duration_seconds.labels(
                    provider=provider,
                    model=model,
                    operation=operation
                ).observe(duration)

                logger.debug(
                    "API metrics tracked",
                    provider=provider,
                    model=model,
                    operation=operation,
                    status=status,
                    duration=duration
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar implementation for sync functions
            start_time = time.time()
            status = 'success'

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                api_requests_total.labels(
                    provider=provider,
                    model=model,
                    operation=operation,
                    status=status
                ).inc()
                api_request_duration_seconds.labels(
                    provider=provider,
                    model=model,
                    operation=operation
                ).observe(duration)

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_db_metrics(query_type: str) -> Callable:
    """Decorator to track database query metrics.
    
    Args:
        query_type: Type of query (select, insert, update, delete)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(
                    query_type=query_type
                ).observe(duration)

        return wrapper

    return decorator


def update_provider_health_metrics(provider_name: str, health_data: dict[str, Any]):
    """Update provider health metrics.
    
    Args:
        provider_name: Provider name
        health_data: Health data including status, error rate, circuit breaker state
    """
    # Update health status
    is_healthy = health_data.get('is_healthy', False)
    provider_health_status.labels(provider=provider_name).set(
        1 if is_healthy else 0
    )

    # Update circuit breaker state
    circuit_state = health_data.get('circuit_state', 'closed')
    state_value = {
        'closed': 0,
        'open': 1,
        'half_open': 2
    }.get(circuit_state, 0)
    provider_circuit_breaker_state.labels(provider=provider_name).set(state_value)

    # Update error rate
    error_rate = health_data.get('error_rate', 0.0)
    provider_error_rate.labels(provider=provider_name).set(error_rate)


def update_db_pool_metrics(pool_stats: dict[str, Any]):
    """Update database connection pool metrics.
    
    Args:
        pool_stats: Pool statistics from monitoring
    """
    if 'pool_status' in pool_stats:
        status = pool_stats['pool_status']
        db_connections_active.set(status.get('checked_out', 0))
        db_connections_total.set(status.get('total', 0))


def track_asset_processing(
    media_type: str,
    source: str,
    operation: str
) -> Callable:
    """Decorator to track asset processing metrics.
    
    Args:
        media_type: Type of media (image, video)
        source: Source of asset (e.g., provider name)
        operation: Operation type (e.g., 'analysis', 'organization')
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = await func(*args, **kwargs)

                # Track quality scores if available
                if hasattr(result, 'quality_scores'):
                    for quality_type, score in result.quality_scores.items():
                        asset_quality_score.labels(
                            media_type=media_type,
                            quality_type=quality_type
                        ).observe(score)

                return result

            except Exception:
                status = 'error'
                raise

            finally:
                duration = time.time() - start_time

                assets_processed_total.labels(
                    media_type=media_type,
                    source=source,
                    status=status
                ).inc()

                asset_processing_duration_seconds.labels(
                    media_type=media_type,
                    operation=operation
                ).observe(duration)

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            # Similar sync implementation
            return func

    return decorator


def track_event_metrics(event_type: str):
    """Track event system metrics.
    
    Args:
        event_type: Type of event being published/processed
    """
    events_published_total.labels(event_type=event_type).inc()


def get_metrics() -> bytes:
    """Generate current metrics in Prometheus format.
    
    Returns:
        Metrics data in Prometheus text format
    """
    return generate_latest(REGISTRY)


def get_metrics_content_type() -> str:
    """Get content type for Prometheus metrics.
    
    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST


# Create a metrics endpoint for FastAPI
def create_metrics_endpoint():
    """Create a FastAPI endpoint for Prometheus metrics."""
    from fastapi import Response

    async def metrics_endpoint():
        metrics_data = get_metrics()
        return Response(
            content=metrics_data,
            media_type=get_metrics_content_type()
        )

    return metrics_endpoint
