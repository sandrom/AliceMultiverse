"""Rate limiting for Alice interface to prevent DoS attacks."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock

from ..core.exceptions import ValidationError


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Request limits per time window
    requests_per_minute: int = 60
    requests_per_hour: int = 600
    requests_per_day: int = 10000

    # Specific operation limits
    search_per_minute: int = 30
    organize_per_hour: int = 10
    generation_per_hour: int = 100

    # Burst allowance
    burst_multiplier: float = 1.5

    # Cleanup interval (remove old entries)
    cleanup_interval_minutes: int = 60


@dataclass
class RequestTracker:
    """Track requests for a specific time window."""

    requests: int = 0
    window_start: datetime = field(default_factory=datetime.now)

    def is_expired(self, window_duration: timedelta) -> bool:
        """Check if this tracking window has expired."""
        return datetime.now() - self.window_start > window_duration

    def increment(self) -> None:
        """Increment the request count."""
        self.requests += 1

    def reset(self) -> None:
        """Reset the tracking window."""
        self.requests = 0
        self.window_start = datetime.now()


class RateLimiter:
    """Rate limiter for API endpoints."""

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        """Initialize rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self._lock = Lock()

        # Track requests by client ID and time window
        self._minute_trackers: dict[str, RequestTracker] = defaultdict(RequestTracker)
        self._hour_trackers: dict[str, RequestTracker] = defaultdict(RequestTracker)
        self._day_trackers: dict[str, RequestTracker] = defaultdict(RequestTracker)

        # Track operation-specific limits
        self._search_trackers: dict[str, RequestTracker] = defaultdict(RequestTracker)
        self._organize_trackers: dict[str, RequestTracker] = defaultdict(RequestTracker)
        self._generation_trackers: dict[str, RequestTracker] = defaultdict(RequestTracker)

        # Last cleanup time
        self._last_cleanup = datetime.now()

    def _cleanup_old_entries(self) -> None:
        """Remove expired tracking entries to prevent memory growth."""
        now = datetime.now()

        # Only cleanup periodically
        if now - self._last_cleanup < timedelta(minutes=self.config.cleanup_interval_minutes):
            return

        with self._lock:
            # Clean up minute trackers (older than 2 minutes)
            expired_keys = [
                key for key, tracker in self._minute_trackers.items()
                if tracker.is_expired(timedelta(minutes=2))
            ]
            for key in expired_keys:
                del self._minute_trackers[key]

            # Clean up hour trackers (older than 2 hours)
            expired_keys = [
                key for key, tracker in self._hour_trackers.items()
                if tracker.is_expired(timedelta(hours=2))
            ]
            for key in expired_keys:
                del self._hour_trackers[key]

            # Clean up day trackers (older than 2 days)
            expired_keys = [
                key for key, tracker in self._day_trackers.items()
                if tracker.is_expired(timedelta(days=2))
            ]
            for key in expired_keys:
                del self._day_trackers[key]

            # Clean up operation-specific trackers
            for trackers in [self._search_trackers, self._organize_trackers, self._generation_trackers]:
                expired_keys = [
                    key for key, tracker in trackers.items()
                    if tracker.is_expired(timedelta(hours=2))
                ]
                for key in expired_keys:
                    del trackers[key]

            self._last_cleanup = now

    def _check_limit(
        self,
        client_id: str,
        tracker: RequestTracker,
        limit: int,
        window: timedelta,
        operation: str = "request"
    ) -> bool:
        """Check if a request is within rate limit.
        
        Args:
            client_id: Client identifier
            tracker: Request tracker for this window
            limit: Maximum requests allowed
            window: Time window duration
            operation: Operation name for error messages
            
        Returns:
            True if within limit
            
        Raises:
            ValidationError: If rate limit exceeded
        """
        # Check if window has expired
        if tracker.is_expired(window):
            tracker.reset()

        # Check limit with burst allowance
        burst_limit = int(limit * self.config.burst_multiplier)
        if tracker.requests >= burst_limit:
            retry_after = window - (datetime.now() - tracker.window_start)
            raise ValidationError(
                f"Rate limit exceeded for {operation}. "
                f"Limit: {limit} per {window}. "
                f"Retry after: {retry_after.total_seconds():.0f} seconds"
            )

        return True

    def check_request(self, client_id: str, operation: str | None = None) -> None:
        """Check if a request is allowed under rate limits.
        
        Args:
            client_id: Client identifier (e.g., IP address, API key)
            operation: Specific operation being performed
            
        Raises:
            ValidationError: If rate limit exceeded
        """
        # Periodic cleanup
        self._cleanup_old_entries()

        with self._lock:
            # Check general rate limits
            self._check_limit(
                client_id,
                self._minute_trackers[client_id],
                self.config.requests_per_minute,
                timedelta(minutes=1),
                "requests per minute"
            )
            self._minute_trackers[client_id].increment()

            self._check_limit(
                client_id,
                self._hour_trackers[client_id],
                self.config.requests_per_hour,
                timedelta(hours=1),
                "requests per hour"
            )
            self._hour_trackers[client_id].increment()

            self._check_limit(
                client_id,
                self._day_trackers[client_id],
                self.config.requests_per_day,
                timedelta(days=1),
                "requests per day"
            )
            self._day_trackers[client_id].increment()

            # Check operation-specific limits
            if operation == "search":
                self._check_limit(
                    client_id,
                    self._search_trackers[client_id],
                    self.config.search_per_minute,
                    timedelta(minutes=1),
                    "searches per minute"
                )
                self._search_trackers[client_id].increment()

            elif operation == "organize":
                self._check_limit(
                    client_id,
                    self._organize_trackers[client_id],
                    self.config.organize_per_hour,
                    timedelta(hours=1),
                    "organize operations per hour"
                )
                self._organize_trackers[client_id].increment()

            elif operation == "generate":
                self._check_limit(
                    client_id,
                    self._generation_trackers[client_id],
                    self.config.generation_per_hour,
                    timedelta(hours=1),
                    "generations per hour"
                )
                self._generation_trackers[client_id].increment()

    def get_remaining_quota(self, client_id: str) -> dict[str, int]:
        """Get remaining quota for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary of remaining quotas by time window
        """
        with self._lock:
            minute_tracker = self._minute_trackers[client_id]
            hour_tracker = self._hour_trackers[client_id]
            day_tracker = self._day_trackers[client_id]

            # Reset expired windows
            if minute_tracker.is_expired(timedelta(minutes=1)):
                minute_tracker.reset()
            if hour_tracker.is_expired(timedelta(hours=1)):
                hour_tracker.reset()
            if day_tracker.is_expired(timedelta(days=1)):
                day_tracker.reset()

            return {
                "requests_per_minute": max(0, self.config.requests_per_minute - minute_tracker.requests),
                "requests_per_hour": max(0, self.config.requests_per_hour - hour_tracker.requests),
                "requests_per_day": max(0, self.config.requests_per_day - day_tracker.requests),
            }

    def reset_client(self, client_id: str) -> None:
        """Reset all rate limit tracking for a client.
        
        Args:
            client_id: Client identifier
        """
        with self._lock:
            # Remove all tracking entries for this client
            for trackers in [
                self._minute_trackers,
                self._hour_trackers,
                self._day_trackers,
                self._search_trackers,
                self._organize_trackers,
                self._generation_trackers,
            ]:
                if client_id in trackers:
                    del trackers[client_id]
