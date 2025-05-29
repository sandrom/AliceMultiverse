"""Health check endpoints for provider monitoring."""

import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .health_monitor import health_monitor
from .registry import get_registry
from .types import ProviderStatus

logger = logging.getLogger(__name__)

# Create FastAPI app for health endpoints
health_app = FastAPI(title="Provider Health API", version="1.0.0")


@health_app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Overall system health check."""
    registry = get_registry()
    providers = registry.list_providers()
    
    all_statuses = health_monitor.get_all_statuses()
    
    # Determine overall health
    if not all_statuses:
        overall_status = "unknown"
        status_code = 503
    elif any(status == ProviderStatus.UNAVAILABLE for status in all_statuses.values()):
        overall_status = "degraded"
        status_code = 200
    elif all(status == ProviderStatus.AVAILABLE for status in all_statuses.values()):
        overall_status = "healthy"
        status_code = 200
    else:
        overall_status = "degraded"
        status_code = 200
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "providers": all_statuses,
            "timestamp": datetime.now().isoformat()
        }
    )


@health_app.get("/health/providers")
async def provider_health() -> Dict[str, Any]:
    """Detailed health status for all providers."""
    registry = get_registry()
    providers = registry.list_providers()
    
    provider_details = {}
    
    for provider_name in providers:
        try:
            provider = registry.get_provider(provider_name)
            metrics = provider.get_health_metrics()
            
            provider_details[provider_name] = {
                "status": health_monitor.get_status(provider_name).value,
                "circuit_state": health_monitor.get_or_create_breaker(provider_name).state.value,
                "metrics": metrics,
                "capabilities": {
                    "generation_types": [gt.value for gt in provider.capabilities.generation_types],
                    "models": provider.capabilities.models[:5],  # First 5 models
                    "model_count": len(provider.capabilities.models)
                }
            }
        except Exception as e:
            logger.error(f"Error getting health for {provider_name}: {e}")
            provider_details[provider_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return {
        "providers": provider_details,
        "timestamp": datetime.now().isoformat()
    }


@health_app.get("/health/providers/{provider_name}")
async def provider_health_detail(provider_name: str) -> Dict[str, Any]:
    """Detailed health status for a specific provider."""
    registry = get_registry()
    
    if provider_name not in registry.list_providers():
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    try:
        provider = registry.get_provider(provider_name)
        metrics = provider.get_health_metrics()
        breaker = health_monitor.get_or_create_breaker(provider_name)
        
        return {
            "provider": provider_name,
            "status": health_monitor.get_status(provider_name).value,
            "circuit_breaker": {
                "state": breaker.state.value,
                "last_state_change": breaker.last_state_change.isoformat(),
                "failure_threshold": breaker.failure_threshold,
                "recovery_timeout_seconds": breaker.recovery_timeout.total_seconds(),
                "success_threshold": breaker.success_threshold
            },
            "metrics": metrics,
            "capabilities": {
                "generation_types": [gt.value for gt in provider.capabilities.generation_types],
                "models": provider.capabilities.models,
                "features": provider.capabilities.features or [],
                "rate_limits": provider.capabilities.rate_limits,
                "pricing": provider.capabilities.pricing
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting health for {provider_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@health_app.post("/health/providers/{provider_name}/check")
async def trigger_health_check(provider_name: str) -> Dict[str, Any]:
    """Manually trigger a health check for a provider."""
    registry = get_registry()
    
    if provider_name not in registry.list_providers():
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    try:
        provider = registry.get_provider(provider_name)
        
        # Perform health check
        start_time = time.time()
        status = await provider.check_status()
        response_time = time.time() - start_time
        
        # Update health monitor
        if status == ProviderStatus.AVAILABLE:
            health_monitor.record_success(provider_name, response_time)
        else:
            health_monitor.record_failure(provider_name)
        
        return {
            "provider": provider_name,
            "check_result": status.value,
            "response_time": response_time,
            "new_status": health_monitor.get_status(provider_name).value,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking health for {provider_name}: {e}")
        health_monitor.record_failure(provider_name)
        raise HTTPException(status_code=500, detail=str(e))


@health_app.post("/health/providers/{provider_name}/reset")
async def reset_circuit_breaker(provider_name: str) -> Dict[str, Any]:
    """Manually reset a provider's circuit breaker."""
    if provider_name not in health_monitor.circuit_breakers:
        raise HTTPException(status_code=404, detail=f"No circuit breaker for '{provider_name}'")
    
    breaker = health_monitor.get_or_create_breaker(provider_name)
    old_state = breaker.state.value
    
    # Reset to closed state
    breaker.state = CircuitState.CLOSED
    breaker.metrics.consecutive_failures = 0
    breaker.last_state_change = datetime.now()
    
    return {
        "provider": provider_name,
        "old_state": old_state,
        "new_state": breaker.state.value,
        "timestamp": datetime.now().isoformat()
    }


# Import required modules at the end to avoid circular imports
import time
from datetime import datetime
from .health_monitor import CircuitState