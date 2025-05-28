"""Database and system monitoring utilities."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

logger = logging.getLogger(__name__)


class DatabasePoolMonitor:
    """Monitor database connection pool statistics."""
    
    def __init__(self, engine: Engine, log_interval: int = 60):
        """Initialize pool monitor.
        
        Args:
            engine: SQLAlchemy engine to monitor
            log_interval: Seconds between logging pool stats (0 to disable)
        """
        self.engine = engine
        self.log_interval = log_interval
        self._start_time = time.time()
        self._stats = {
            "connections_created": 0,
            "connections_closed": 0,
            "connection_errors": 0,
            "checkouts": 0,
            "checkins": 0,
            "checkout_time_total": 0.0,
            "checkout_time_max": 0.0,
            "overflow_created": 0,
        }
        self._checkout_times: Dict[Any, float] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Register event listeners
        self._register_listeners()
        
        # Start monitoring task if interval > 0
        if self.log_interval > 0:
            self._start_monitoring()
    
    def _register_listeners(self):
        """Register SQLAlchemy pool event listeners."""
        pool_impl = self.engine.pool
        
        @event.listens_for(pool_impl, "connect")
        def on_connect(dbapi_conn, connection_record):
            self._stats["connections_created"] += 1
            logger.debug("New database connection created")
        
        @event.listens_for(pool_impl, "close")
        def on_close(dbapi_conn, connection_record):
            self._stats["connections_closed"] += 1
            logger.debug("Database connection closed")
        
        @event.listens_for(pool_impl, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            self._stats["checkouts"] += 1
            self._checkout_times[id(connection_proxy)] = time.time()
        
        @event.listens_for(pool_impl, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            self._stats["checkins"] += 1
            
            # Calculate checkout duration
            conn_id = id(connection_record)
            if conn_id in self._checkout_times:
                duration = time.time() - self._checkout_times[conn_id]
                self._stats["checkout_time_total"] += duration
                self._stats["checkout_time_max"] = max(
                    self._stats["checkout_time_max"], duration
                )
                del self._checkout_times[conn_id]
    
    def _start_monitoring(self):
        """Start the monitoring loop."""
        async def _monitor_loop():
            while True:
                await asyncio.sleep(self.log_interval)
                self.log_stats()
        
        loop = asyncio.get_event_loop()
        self._monitoring_task = loop.create_task(_monitor_loop())
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status."""
        pool_impl = self.engine.pool
        
        status = {
            "size": pool_impl.size() if hasattr(pool_impl, 'size') else 0,
            "checked_out": pool_impl.checkedout() if hasattr(pool_impl, 'checkedout') else 0,
            "overflow": pool_impl.overflow() if hasattr(pool_impl, 'overflow') else 0,
            "total": pool_impl.total() if hasattr(pool_impl, 'total') else 0,
        }
        
        # Add configuration
        if hasattr(pool_impl, '_pool'):
            status["max_size"] = pool_impl._pool.maxsize if hasattr(pool_impl._pool, 'maxsize') else None
        
        return status
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        uptime = time.time() - self._start_time
        avg_checkout_time = (
            self._stats["checkout_time_total"] / self._stats["checkouts"]
            if self._stats["checkouts"] > 0 else 0
        )
        
        return {
            "uptime_seconds": uptime,
            "pool_status": self.get_pool_status(),
            "lifetime_stats": {
                **self._stats,
                "checkout_time_avg": avg_checkout_time,
            },
            "health": self._assess_health(),
        }
    
    def _assess_health(self) -> Dict[str, Any]:
        """Assess pool health based on metrics."""
        pool_status = self.get_pool_status()
        
        # Health indicators
        warnings = []
        
        # Check if pool is exhausted
        if pool_status["checked_out"] >= pool_status["size"]:
            if pool_status["overflow"] > 0:
                warnings.append("Pool exhausted, using overflow connections")
            else:
                warnings.append("Pool exhausted, connections may be blocked")
        
        # Check average checkout time
        avg_time = (
            self._stats["checkout_time_total"] / self._stats["checkouts"]
            if self._stats["checkouts"] > 0 else 0
        )
        if avg_time > 5.0:  # 5 seconds
            warnings.append(f"High average connection hold time: {avg_time:.2f}s")
        
        # Check max checkout time
        if self._stats["checkout_time_max"] > 30.0:  # 30 seconds
            warnings.append(f"Very long connection hold detected: {self._stats['checkout_time_max']:.2f}s")
        
        # Check connection errors
        error_rate = (
            self._stats["connection_errors"] / self._stats["connections_created"]
            if self._stats["connections_created"] > 0 else 0
        )
        if error_rate > 0.05:  # 5% error rate
            warnings.append(f"High connection error rate: {error_rate*100:.1f}%")
        
        return {
            "status": "unhealthy" if warnings else "healthy",
            "warnings": warnings,
        }
    
    def log_stats(self):
        """Log current statistics."""
        stats = self.get_stats()
        pool_status = stats["pool_status"]
        health = stats["health"]
        
        logger.info(
            f"DB Pool Status - "
            f"Active: {pool_status['checked_out']}/{pool_status['size']} "
            f"(+{pool_status['overflow']} overflow), "
            f"Total connections: {pool_status['total']}, "
            f"Health: {health['status']}"
        )
        
        if health["warnings"]:
            for warning in health["warnings"]:
                logger.warning(f"DB Pool Warning: {warning}")
        
        # Log detailed stats periodically (every 10th interval)
        if self._stats["checkouts"] % 10 == 0:
            logger.info(f"DB Pool Lifetime Stats: {stats['lifetime_stats']}")
    
    def stop_monitoring(self):
        """Stop the monitoring task."""
        if self._monitoring_task:
            self._monitoring_task.cancel()


def setup_pool_monitoring(engine: Engine, log_interval: int = 60) -> DatabasePoolMonitor:
    """Setup database pool monitoring for an engine.
    
    Args:
        engine: SQLAlchemy engine
        log_interval: Seconds between logging (0 to disable periodic logging)
        
    Returns:
        DatabasePoolMonitor instance
    """
    monitor = DatabasePoolMonitor(engine, log_interval)
    logger.info(f"Database pool monitoring enabled (interval: {log_interval}s)")
    return monitor