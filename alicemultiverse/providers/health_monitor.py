"""Provider health monitoring with circuit breaker pattern."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List, Callable

from .types import ProviderStatus

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class HealthMetrics:
    """Health metrics for a provider."""
    total_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_check_time: Optional[datetime] = None
    average_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)
    
    def record_success(self, response_time: float):
        """Record a successful request."""
        self.total_requests += 1
        self.consecutive_failures = 0
        self.consecutive_successes += 1
        self.last_success_time = datetime.now()
        
        # Update response times (keep last 100)
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)
        self.average_response_time = sum(self.response_times) / len(self.response_times)
    
    def record_failure(self):
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.now()
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def is_healthy(self) -> bool:
        """Check if provider is healthy based on metrics."""
        # No requests yet - assume healthy
        if self.total_requests == 0:
            return True
            
        # Too many consecutive failures
        if self.consecutive_failures >= 5:
            return False
            
        # High failure rate (over 50% in last 100 requests)
        if self.total_requests >= 10 and self.failure_rate > 0.5:
            return False
            
        # Slow response times (over 30 seconds average)
        if self.average_response_time > 30.0:
            return False
            
        return True


@dataclass
class CircuitBreaker:
    """Circuit breaker for a provider."""
    provider_name: str
    failure_threshold: int = 5  # Consecutive failures to open circuit
    recovery_timeout: timedelta = timedelta(minutes=1)  # Time before trying again
    success_threshold: int = 3  # Consecutive successes to close circuit
    
    state: CircuitState = CircuitState.CLOSED
    metrics: HealthMetrics = field(default_factory=HealthMetrics)
    last_state_change: datetime = field(default_factory=datetime.now)
    
    def record_success(self, response_time: float = 0.0):
        """Record successful request."""
        self.metrics.record_success(response_time)
        
        if self.state == CircuitState.HALF_OPEN:
            if self.metrics.consecutive_successes >= self.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.OPEN:
            # Shouldn't happen, but handle gracefully
            logger.warning(f"{self.provider_name}: Success recorded while circuit open")
    
    def record_failure(self):
        """Record failed request."""
        self.metrics.record_failure()
        
        if self.state == CircuitState.CLOSED:
            if self.metrics.consecutive_failures >= self.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Single failure in half-open state reopens circuit
            self._transition_to_open()
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if datetime.now() - self.last_state_change >= self.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def _transition_to_open(self):
        """Transition to open state."""
        logger.warning(
            f"{self.provider_name}: Circuit breaker OPEN "
            f"(failures: {self.metrics.consecutive_failures})"
        )
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
    
    def _transition_to_closed(self):
        """Transition to closed state."""
        logger.info(f"{self.provider_name}: Circuit breaker CLOSED (recovered)")
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.metrics.consecutive_failures = 0
    
    def _transition_to_half_open(self):
        """Transition to half-open state."""
        logger.info(f"{self.provider_name}: Circuit breaker HALF-OPEN (testing)")
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
    
    def get_status(self) -> ProviderStatus:
        """Get provider status based on circuit state."""
        if self.state == CircuitState.CLOSED:
            if self.metrics.is_healthy:
                return ProviderStatus.AVAILABLE
            else:
                return ProviderStatus.DEGRADED
        elif self.state == CircuitState.OPEN:
            return ProviderStatus.UNAVAILABLE
        else:  # HALF_OPEN
            return ProviderStatus.DEGRADED


class ProviderHealthMonitor:
    """Monitors health of all providers."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._check_interval = 60  # seconds
        self._callbacks: List[Callable] = []
    
    def get_or_create_breaker(self, provider_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for provider."""
        if provider_name not in self.circuit_breakers:
            self.circuit_breakers[provider_name] = CircuitBreaker(provider_name)
        return self.circuit_breakers[provider_name]
    
    def record_success(self, provider_name: str, response_time: float = 0.0):
        """Record successful request."""
        breaker = self.get_or_create_breaker(provider_name)
        breaker.record_success(response_time)
    
    def record_failure(self, provider_name: str):
        """Record failed request."""
        breaker = self.get_or_create_breaker(provider_name)
        breaker.record_failure()
        
        # Notify callbacks if circuit opened
        if breaker.state == CircuitState.OPEN:
            self._notify_callbacks(provider_name, ProviderStatus.UNAVAILABLE)
    
    def can_execute(self, provider_name: str) -> bool:
        """Check if provider can handle requests."""
        breaker = self.get_or_create_breaker(provider_name)
        return breaker.can_execute()
    
    def get_status(self, provider_name: str) -> ProviderStatus:
        """Get provider status."""
        if provider_name not in self.circuit_breakers:
            return ProviderStatus.UNKNOWN
        return self.circuit_breakers[provider_name].get_status()
    
    def get_all_statuses(self) -> Dict[str, ProviderStatus]:
        """Get status of all monitored providers."""
        return {
            name: breaker.get_status()
            for name, breaker in self.circuit_breakers.items()
        }
    
    def get_metrics(self, provider_name: str) -> Optional[HealthMetrics]:
        """Get health metrics for provider."""
        if provider_name in self.circuit_breakers:
            return self.circuit_breakers[provider_name].metrics
        return None
    
    def add_status_callback(self, callback: Callable[[str, ProviderStatus], None]):
        """Add callback for status changes."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self, provider_name: str, status: ProviderStatus):
        """Notify callbacks of status change."""
        for callback in self._callbacks:
            try:
                callback(provider_name, status)
            except Exception as e:
                logger.error(f"Error in health monitor callback: {e}")
    
    async def start_monitoring(self, providers: List):
        """Start monitoring providers."""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Health monitoring already running")
            return
            
        self._monitoring_task = asyncio.create_task(self._monitor_loop(providers))
        logger.info("Started provider health monitoring")
    
    async def stop_monitoring(self):
        """Stop monitoring providers."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped provider health monitoring")
    
    async def _monitor_loop(self, providers: List):
        """Monitoring loop that periodically checks provider health."""
        while True:
            try:
                # Check each provider
                for provider in providers:
                    try:
                        start_time = time.time()
                        status = await provider.check_status()
                        response_time = time.time() - start_time
                        
                        breaker = self.get_or_create_breaker(provider.name)
                        breaker.metrics.last_check_time = datetime.now()
                        
                        if status == ProviderStatus.AVAILABLE:
                            breaker.record_success(response_time)
                        else:
                            breaker.record_failure()
                            
                    except Exception as e:
                        logger.error(f"Error checking {provider.name} health: {e}")
                        self.record_failure(provider.name)
                
                # Wait before next check
                await asyncio.sleep(self._check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self._check_interval)


# Global health monitor instance
health_monitor = ProviderHealthMonitor()


def with_circuit_breaker(provider_name: str):
    """Decorator to add circuit breaker to provider methods."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Check if circuit allows execution
            if not health_monitor.can_execute(provider_name):
                raise Exception(f"{provider_name} circuit breaker is OPEN - service unavailable")
            
            try:
                start_time = time.time()
                result = await func(*args, **kwargs)
                response_time = time.time() - start_time
                
                # Record success
                health_monitor.record_success(provider_name, response_time)
                return result
                
            except Exception as e:
                # Record failure
                health_monitor.record_failure(provider_name)
                raise
        
        return wrapper
    return decorator