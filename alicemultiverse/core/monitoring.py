"""System monitoring utilities."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor system health and performance."""
    
    def __init__(self, log_interval: int = 60):
        """Initialize system monitor.
        
        Args:
            log_interval: Seconds between logging stats (0 to disable)
        """
        self.log_interval = log_interval
        self._start_time = time.time()
        self._stats = {
            "requests_processed": 0,
            "errors_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self._monitoring_task: Optional[asyncio.Task] = None
    
    def record_request(self) -> None:
        """Record a processed request."""
        self._stats["requests_processed"] += 1
    
    def record_error(self) -> None:
        """Record an error."""
        self._stats["errors_count"] += 1
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self._stats["cache_hits"] += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self._stats["cache_misses"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics.
        
        Returns:
            Dictionary of current stats
        """
        uptime = time.time() - self._start_time
        cache_total = self._stats["cache_hits"] + self._stats["cache_misses"]
        hit_rate = (
            self._stats["cache_hits"] / cache_total if cache_total > 0 else 0
        )
        
        return {
            **self._stats,
            "uptime_seconds": uptime,
            "cache_hit_rate": hit_rate,
        }
    
    async def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.log_interval)
                stats = self.get_stats()
                logger.info(
                    "System stats",
                    **stats
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
    
    def start_monitoring(self) -> None:
        """Start background monitoring."""
        if self.log_interval > 0 and not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitor_loop())
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None


# Global monitor instance
system_monitor = SystemMonitor()