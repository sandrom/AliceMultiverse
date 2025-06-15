"""Provider optimization for cost-aware and performance-optimized image analysis."""

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .analyzer import ImageAnalyzer
from .base import ImageAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class ProviderMetrics:
    """Performance and cost metrics for a provider."""

    provider_name: str

    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: datetime | None = None

    # Cost metrics
    total_cost: float = 0.0
    average_cost_per_request: float = 0.0

    # Quality metrics (subjective scoring)
    quality_scores: list[float] = field(default_factory=list)
    average_quality: float = 0.0

    # Reliability tracking
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=10))
    uptime_percentage: float = 100.0

    # Rate limiting info
    rate_limit_remaining: int | None = None
    rate_limit_reset: datetime | None = None
    requests_per_minute: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def cost_efficiency(self) -> float:
        """Calculate cost efficiency (quality per dollar)."""
        if self.average_cost_per_request == 0:
            return 0.0
        return self.average_quality / self.average_cost_per_request

    def update_response_time(self, response_time: float):
        """Update average response time with new measurement."""
        if self.total_requests == 0:
            self.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.average_response_time = (alpha * response_time +
                                        (1 - alpha) * self.average_response_time)

    def record_success(self, cost: float, quality_score: float, response_time: float):
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_cost += cost
        self.quality_scores.append(quality_score)

        # Update averages
        self.average_cost_per_request = self.total_cost / self.total_requests
        self.average_quality = sum(self.quality_scores) / len(self.quality_scores)
        self.update_response_time(response_time)

        self.last_request_time = datetime.now()

    def record_failure(self, error: str, response_time: float = 0.0):
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.recent_failures.append({
            "timestamp": datetime.now(),
            "error": error
        })

        if response_time > 0:
            self.update_response_time(response_time)

        # Update uptime percentage
        self.uptime_percentage = self.success_rate
        self.last_request_time = datetime.now()


@dataclass
class BudgetManager:
    """Manages budget constraints and spending tracking."""

    total_budget: float
    spent: float = 0.0
    reserved: float = 0.0  # Amount reserved for pending requests
    currency: str = "USD"

    # Budget periods
    daily_budget: float | None = None
    daily_spent: float = 0.0
    daily_reset_time: datetime | None = None

    # Warnings and limits
    warning_threshold: float = 0.8  # Warn at 80% of budget
    hard_limit: bool = True  # Stop processing when budget exceeded

    @property
    def available(self) -> float:
        """Get available budget (total - spent - reserved)."""
        return max(0, self.total_budget - self.spent - self.reserved)

    @property
    def utilization(self) -> float:
        """Get budget utilization percentage."""
        return (self.spent / self.total_budget) * 100 if self.total_budget > 0 else 0

    def can_afford(self, cost: float) -> bool:
        """Check if we can afford a request."""
        return self.available >= cost

    def reserve(self, amount: float) -> bool:
        """Reserve budget for a pending request."""
        if self.can_afford(amount):
            self.reserved += amount
            return True
        return False

    def commit(self, reserved_amount: float, actual_amount: float):
        """Commit a reserved amount (convert to spent)."""
        self.reserved -= reserved_amount
        self.spent += actual_amount

        # Track daily spending
        if self.daily_budget:
            now = datetime.now()
            if (self.daily_reset_time is None or
                now.date() > self.daily_reset_time.date()):
                self.daily_spent = 0.0
                self.daily_reset_time = now

            self.daily_spent += actual_amount

    def release_reservation(self, amount: float):
        """Release a reservation without spending."""
        self.reserved = max(0, self.reserved - amount)

    def check_warnings(self) -> list[str]:
        """Check for budget warnings."""
        warnings = []

        if self.utilization >= self.warning_threshold * 100:
            warnings.append(f"Budget {self.utilization:.1f}% utilized")

        if self.daily_budget and self.daily_spent >= self.daily_budget * self.warning_threshold:
            daily_util = (self.daily_spent / self.daily_budget) * 100
            warnings.append(f"Daily budget {daily_util:.1f}% utilized")

        if self.available <= 0:
            warnings.append("Budget exhausted")

        return warnings


class ProviderOptimizer:
    """Optimizes provider selection based on cost, performance, and quality."""

    def __init__(self, analyzer: ImageAnalyzer, metrics_file: Path | None = None):
        """Initialize the optimizer.
        
        Args:
            analyzer: Image analyzer instance
            metrics_file: Optional file to persist metrics
        """
        self.analyzer = analyzer
        self.metrics_file = metrics_file or Path("provider_metrics.json")

        # Provider metrics
        self.metrics: dict[str, ProviderMetrics] = {}
        self._load_metrics()

        # Initialize metrics for available providers
        for provider in self.analyzer.get_available_providers():
            if provider not in self.metrics:
                self.metrics[provider] = ProviderMetrics(provider_name=provider)

        # Budget management
        self.budget_manager: BudgetManager | None = None

        # Failover configuration
        self.failover_enabled = True
        self.max_failover_attempts = 3
        self.failover_blacklist_duration = timedelta(minutes=15)
        self.temp_blacklist: dict[str, datetime] = {}

    def set_budget(self, total_budget: float, daily_budget: float | None = None,
                   currency: str = "USD", **kwargs):
        """Set budget constraints.
        
        Args:
            total_budget: Total budget limit
            daily_budget: Optional daily budget limit
            currency: Currency code
            **kwargs: Additional budget manager options
        """
        self.budget_manager = BudgetManager(
            total_budget=total_budget,
            daily_budget=daily_budget,
            currency=currency,
            **kwargs
        )
        logger.info(f"Set budget: {currency} {total_budget:.2f}")

    def _load_metrics(self):
        """Load metrics from file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file) as f:
                    data = json.load(f)

                for provider_name, metrics_data in data.items():
                    metrics = ProviderMetrics(provider_name=provider_name)

                    # Load basic metrics
                    for field in ['total_requests', 'successful_requests', 'failed_requests',
                                'average_response_time', 'total_cost', 'average_cost_per_request',
                                'average_quality', 'uptime_percentage', 'requests_per_minute']:
                        if field in metrics_data:
                            setattr(metrics, field, metrics_data[field])

                    # Load timestamps
                    if 'last_request_time' in metrics_data:
                        metrics.last_request_time = datetime.fromisoformat(metrics_data['last_request_time'])

                    # Load quality scores
                    metrics.quality_scores = metrics_data.get('quality_scores', [])

                    # Load recent failures
                    recent_failures = deque(maxlen=10)
                    for failure in metrics_data.get('recent_failures', []):
                        recent_failures.append({
                            'timestamp': datetime.fromisoformat(failure['timestamp']),
                            'error': failure['error']
                        })
                    metrics.recent_failures = recent_failures

                    self.metrics[provider_name] = metrics

                logger.info(f"Loaded metrics for {len(self.metrics)} providers")

            except Exception as e:
                logger.warning(f"Failed to load metrics: {e}")

    def _save_metrics(self):
        """Save metrics to file."""
        try:
            data = {}
            for provider_name, metrics in self.metrics.items():
                data[provider_name] = {
                    'total_requests': metrics.total_requests,
                    'successful_requests': metrics.successful_requests,
                    'failed_requests': metrics.failed_requests,
                    'average_response_time': metrics.average_response_time,
                    'total_cost': metrics.total_cost,
                    'average_cost_per_request': metrics.average_cost_per_request,
                    'average_quality': metrics.average_quality,
                    'uptime_percentage': metrics.uptime_percentage,
                    'requests_per_minute': metrics.requests_per_minute,
                    'quality_scores': metrics.quality_scores,
                    'last_request_time': metrics.last_request_time.isoformat() if metrics.last_request_time else None,
                    'recent_failures': [
                        {
                            'timestamp': f['timestamp'].isoformat(),
                            'error': f['error']
                        }
                        for f in metrics.recent_failures
                    ]
                }

            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def get_available_providers(self, exclude_blacklisted: bool = True) -> list[str]:
        """Get available providers, optionally excluding temporarily blacklisted ones."""
        providers = self.analyzer.get_available_providers()

        if exclude_blacklisted:
            now = datetime.now()
            providers = [
                p for p in providers
                if p not in self.temp_blacklist or
                   now > self.temp_blacklist[p]
            ]

        return providers

    def select_optimal_provider(self, optimization_criteria: str = "cost_efficiency",
                              budget_limit: float | None = None,
                              detailed: bool = False) -> str | None:
        """Select the optimal provider based on criteria.
        
        Args:
            optimization_criteria: 'cost', 'quality', 'speed', 'cost_efficiency', 'reliability'
            budget_limit: Maximum cost per request
            detailed: Whether this is for detailed analysis
            
        Returns:
            Selected provider name or None if none available
        """
        available_providers = self.get_available_providers()
        if not available_providers:
            return None

        # Filter by budget if specified
        if budget_limit:
            affordable_providers = []
            for provider in available_providers:
                if provider in self.analyzer.analyzers:
                    cost = self.analyzer.analyzers[provider].estimate_cost(detailed)
                    if cost <= budget_limit:
                        affordable_providers.append(provider)
            available_providers = affordable_providers

        if not available_providers:
            return None

        # Score providers based on criteria
        scored_providers = []
        for provider in available_providers:
            metrics = self.metrics.get(provider, ProviderMetrics(provider_name=provider))

            if optimization_criteria == "cost":
                # Lower cost is better
                cost = self.analyzer.analyzers[provider].estimate_cost(detailed)
                score = 1.0 / (cost + 0.001)  # Avoid division by zero

            elif optimization_criteria == "quality":
                score = metrics.average_quality

            elif optimization_criteria == "speed":
                # Lower response time is better
                score = 1.0 / (metrics.average_response_time + 0.1)

            elif optimization_criteria == "cost_efficiency":
                score = metrics.cost_efficiency

            elif optimization_criteria == "reliability":
                score = metrics.success_rate / 100.0

            else:
                # Default: balanced score
                cost = self.analyzer.analyzers[provider].estimate_cost(detailed)
                cost_score = 1.0 / (cost + 0.001)
                quality_score = metrics.average_quality
                reliability_score = metrics.success_rate / 100.0

                score = (cost_score * 0.3 + quality_score * 0.4 + reliability_score * 0.3)

            scored_providers.append((provider, score))

        # Return highest scoring provider
        if scored_providers:
            return max(scored_providers, key=lambda x: x[1])[0]

        return None

    async def analyze_with_optimization(self, image_path: Path, **kwargs) -> ImageAnalysisResult | None:
        """Analyze image with automatic provider optimization and failover.
        
        Args:
            image_path: Path to image
            **kwargs: Arguments passed to analyzer
            
        Returns:
            Analysis result or None if all providers failed
        """
        # Select optimal provider
        detailed = kwargs.get('detailed', False)
        budget_per_request = None

        if self.budget_manager:
            # Check budget constraints
            warnings = self.budget_manager.check_warnings()
            for warning in warnings:
                logger.warning(warning)

            if self.budget_manager.available <= 0:
                logger.error("Budget exhausted")
                return None

            budget_per_request = self.budget_manager.available

        provider = kwargs.get('provider') or self.select_optimal_provider(
            budget_limit=budget_per_request,
            detailed=detailed
        )

        if not provider:
            logger.error("No suitable provider available")
            return None

        # Attempt analysis with failover
        attempts = 0
        while attempts < self.max_failover_attempts:
            try:
                start_time = time.time()

                # Reserve budget if needed
                estimated_cost = 0.0
                if self.budget_manager and provider in self.analyzer.analyzers:
                    estimated_cost = self.analyzer.analyzers[provider].estimate_cost(detailed)
                    if not self.budget_manager.reserve(estimated_cost):
                        logger.warning(f"Cannot afford {provider} (${estimated_cost:.4f})")
                        # Try cheaper provider
                        provider = self.select_optimal_provider(
                            optimization_criteria="cost",
                            budget_limit=self.budget_manager.available,
                            detailed=detailed
                        )
                        if not provider:
                            return None
                        continue

                # Perform analysis
                result = await self.analyzer.analyze(image_path, provider=provider, **kwargs)
                response_time = time.time() - start_time

                # Calculate quality score (simplified)
                quality_score = self._calculate_quality_score(result)

                # Update metrics
                self.metrics[provider].record_success(result.cost, quality_score, response_time)

                # Update budget
                if self.budget_manager:
                    self.budget_manager.commit(estimated_cost, result.cost)

                # Save metrics periodically
                if self.metrics[provider].total_requests % 10 == 0:
                    self._save_metrics()

                return result

            except Exception as e:
                response_time = time.time() - start_time
                error_msg = str(e)

                # Update metrics
                self.metrics[provider].record_failure(error_msg, response_time)

                # Release budget reservation
                if self.budget_manager:
                    self.budget_manager.release_reservation(estimated_cost)

                logger.warning(f"Provider {provider} failed (attempt {attempts + 1}): {e}")

                # Temporarily blacklist provider if too many recent failures
                if len(self.metrics[provider].recent_failures) >= 3:
                    recent_failures = [
                        f for f in self.metrics[provider].recent_failures
                        if datetime.now() - f['timestamp'] < timedelta(minutes=5)
                    ]
                    if len(recent_failures) >= 3:
                        self.temp_blacklist[provider] = datetime.now() + self.failover_blacklist_duration
                        logger.warning(f"Temporarily blacklisted {provider} due to repeated failures")

                # Try different provider
                if self.failover_enabled:
                    provider = self.select_optimal_provider(
                        budget_limit=budget_per_request,
                        detailed=detailed
                    )
                    if not provider:
                        break

                attempts += 1

        logger.error(f"All providers failed after {attempts} attempts")
        return None

    def _calculate_quality_score(self, result: ImageAnalysisResult) -> float:
        """Calculate quality score for a result (simplified scoring)."""
        score = 0.5  # Base score

        # Add points for comprehensive description
        if result.description and len(result.description) > 100:
            score += 0.2

        # Add points for rich tags
        if result.tags:
            tag_count = sum(len(tags) for tags in result.tags.values())
            score += min(0.2, tag_count * 0.01)

        # Add points for successful prompt generation
        if result.generated_prompt:
            score += 0.1

        return min(1.0, score)

    def get_provider_statistics(self) -> dict[str, dict[str, Any]]:
        """Get comprehensive statistics for all providers."""
        stats = {}

        for provider_name, metrics in self.metrics.items():
            stats[provider_name] = {
                "requests": {
                    "total": metrics.total_requests,
                    "successful": metrics.successful_requests,
                    "failed": metrics.failed_requests,
                    "success_rate": f"{metrics.success_rate:.1f}%"
                },
                "performance": {
                    "average_response_time": f"{metrics.average_response_time:.2f}s",
                    "uptime_percentage": f"{metrics.uptime_percentage:.1f}%",
                    "requests_per_minute": f"{metrics.requests_per_minute:.1f}"
                },
                "cost": {
                    "total_cost": f"${metrics.total_cost:.2f}",
                    "average_per_request": f"${metrics.average_cost_per_request:.4f}",
                    "cost_efficiency": f"{metrics.cost_efficiency:.2f}"
                },
                "quality": {
                    "average_score": f"{metrics.average_quality:.2f}",
                    "total_scores": len(metrics.quality_scores)
                },
                "last_request": metrics.last_request_time.isoformat() if metrics.last_request_time else None,
                "recent_failures": len(metrics.recent_failures)
            }

        return stats

    def reset_provider_metrics(self, provider: str):
        """Reset metrics for a specific provider."""
        if provider in self.metrics:
            self.metrics[provider] = ProviderMetrics(provider_name=provider)
            logger.info(f"Reset metrics for {provider}")

    def cleanup_blacklist(self):
        """Remove expired entries from temporary blacklist."""
        now = datetime.now()
        expired = [p for p, expiry in self.temp_blacklist.items() if now > expiry]
        for provider in expired:
            del self.temp_blacklist[provider]
            logger.info(f"Removed {provider} from temporary blacklist")

    def close(self):
        """Clean up and save final metrics."""
        self._save_metrics()
        logger.info("Provider optimizer closed, metrics saved")
