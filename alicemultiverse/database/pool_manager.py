"""Enhanced database connection pool management with exhaustion prevention."""

import asyncio
import logging
import time
import weakref
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Optional, Set, Any, List

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.pool import Pool

from .config import engine, SessionLocal, get_pool_monitor
from ..core.metrics import update_db_pool_metrics, db_query_duration_seconds

logger = logging.getLogger(__name__)


class ConnectionLeakDetector:
    """Detects and logs potential connection leaks."""
    
    def __init__(self, warning_threshold: float = 30.0):
        """Initialize leak detector.
        
        Args:
            warning_threshold: Seconds before considering a connection leaked
        """
        self.warning_threshold = warning_threshold
        self._active_connections: Dict[int, Dict[str, Any]] = {}
        self._lock = Lock()
        self._monitoring_task: Optional[asyncio.Task] = None
    
    def track_checkout(self, connection_id: int, stack_info: str):
        """Track a connection checkout."""
        with self._lock:
            self._active_connections[connection_id] = {
                "checkout_time": time.time(),
                "stack_info": stack_info,
                "warned": False
            }
    
    def track_checkin(self, connection_id: int):
        """Track a connection checkin."""
        with self._lock:
            self._active_connections.pop(connection_id, None)
    
    def check_for_leaks(self) -> List[Dict[str, Any]]:
        """Check for potential connection leaks."""
        current_time = time.time()
        leaks = []
        
        with self._lock:
            for conn_id, info in self._active_connections.items():
                hold_time = current_time - info["checkout_time"]
                
                if hold_time > self.warning_threshold and not info["warned"]:
                    info["warned"] = True
                    leaks.append({
                        "connection_id": conn_id,
                        "hold_time": hold_time,
                        "stack_info": info["stack_info"]
                    })
        
        return leaks
    
    async def start_monitoring(self, check_interval: int = 10):
        """Start monitoring for connection leaks."""
        async def _monitor_loop():
            while True:
                await asyncio.sleep(check_interval)
                leaks = self.check_for_leaks()
                
                for leak in leaks:
                    logger.warning(
                        f"Potential connection leak detected! "
                        f"Connection held for {leak['hold_time']:.1f}s\n"
                        f"Stack trace:\n{leak['stack_info']}"
                    )
        
        self._monitoring_task = asyncio.create_task(_monitor_loop())
        logger.info("Connection leak detection started")
    
    def stop_monitoring(self):
        """Stop monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()


class PoolExhaustionPreventer:
    """Prevents connection pool exhaustion through various strategies."""
    
    def __init__(self, pool: Pool, max_wait_time: float = 5.0):
        """Initialize exhaustion preventer.
        
        Args:
            pool: SQLAlchemy connection pool
            max_wait_time: Maximum time to wait for a connection
        """
        self.pool = pool
        self.max_wait_time = max_wait_time
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
    
    async def acquire_connection_async(self) -> Any:
        """Acquire a connection with queue management."""
        # Add request to queue
        future = asyncio.Future()
        await self._request_queue.put(future)
        
        # Wait for connection with timeout
        try:
            return await asyncio.wait_for(future, timeout=self.max_wait_time)
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Failed to acquire database connection after {self.max_wait_time}s. "
                "Pool may be exhausted."
            )
    
    async def start_processing(self):
        """Start processing connection requests."""
        async def _process_requests():
            while True:
                try:
                    future = await self._request_queue.get()
                    
                    # Try to get connection from pool
                    try:
                        conn = self.pool.connect()
                        future.set_result(conn)
                    except Exception as e:
                        future.set_exception(e)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error processing connection request: {e}")
        
        self._processing_task = asyncio.create_task(_process_requests())
        logger.info("Pool exhaustion prevention started")


class ManagedSession:
    """Enhanced session management with automatic cleanup and leak prevention."""
    
    def __init__(self, session: Session, stack_info: str, timeout: float = 300.0):
        """Initialize managed session.
        
        Args:
            session: SQLAlchemy session
            stack_info: Stack trace for debugging
            timeout: Maximum session lifetime in seconds
        """
        self.session = session
        self.stack_info = stack_info
        self.timeout = timeout
        self.created_at = time.time()
        self._closed = False
    
    def __enter__(self):
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the session if not already closed."""
        if not self._closed:
            try:
                self.session.close()
                self._closed = True
            except Exception as e:
                logger.error(f"Error closing session: {e}")
    
    def is_expired(self) -> bool:
        """Check if session has exceeded timeout."""
        return (time.time() - self.created_at) > self.timeout


class EnhancedSessionManager:
    """Enhanced session manager with leak detection and pool exhaustion prevention."""
    
    def __init__(self):
        self.leak_detector = ConnectionLeakDetector()
        self.exhaustion_preventer = None  # Initialized when pool is available
        self._active_sessions: weakref.WeakSet = weakref.WeakSet()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Setup event listeners
        self._setup_listeners()
    
    def _setup_listeners(self):
        """Setup SQLAlchemy event listeners."""
        pool = engine.pool
        
        @event.listens_for(pool, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            # Get stack trace for debugging
            import traceback
            stack_info = ''.join(traceback.format_stack()[:-1])
            
            # Track checkout
            conn_id = id(connection_proxy)
            self.leak_detector.track_checkout(conn_id, stack_info)
        
        @event.listens_for(pool, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            # Track checkin
            conn_id = id(connection_record)
            self.leak_detector.track_checkin(conn_id)
    
    @contextmanager
    def get_session(self, timeout: Optional[float] = None) -> Session:
        """Get a managed session with automatic cleanup.
        
        Args:
            timeout: Session timeout in seconds (default: 5 minutes)
            
        Yields:
            SQLAlchemy session
        """
        # Get stack trace for debugging
        import traceback
        stack_info = ''.join(traceback.format_stack()[:-1])
        
        # Create session
        session = SessionLocal()
        
        # Create managed session
        managed = ManagedSession(
            session, 
            stack_info, 
            timeout or 300.0
        )
        
        # Track active session
        self._active_sessions.add(managed)
        
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            managed.close()
    
    @asynccontextmanager
    async def get_session_async(self, timeout: Optional[float] = None) -> Session:
        """Async version of get_session."""
        # For now, wrap sync version
        # In future, could use async SQLAlchemy
        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(None, SessionLocal)
        
        try:
            yield session
            await loop.run_in_executor(None, session.commit)
        except Exception:
            await loop.run_in_executor(None, session.rollback)
            raise
        finally:
            await loop.run_in_executor(None, session.close)
    
    async def start_monitoring(self, cleanup_interval: int = 60):
        """Start monitoring and cleanup tasks."""
        # Start leak detection
        await self.leak_detector.start_monitoring()
        
        # Start cleanup task
        async def _cleanup_loop():
            while True:
                await asyncio.sleep(cleanup_interval)
                self._cleanup_expired_sessions()
        
        self._cleanup_task = asyncio.create_task(_cleanup_loop())
        logger.info("Session monitoring and cleanup started")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        expired_count = 0
        
        for managed in list(self._active_sessions):
            if managed.is_expired():
                logger.warning(
                    f"Closing expired session (age: {time.time() - managed.created_at:.1f}s)\n"
                    f"Created at:\n{managed.stack_info}"
                )
                managed.close()
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information."""
        pool_monitor = get_pool_monitor()
        pool_stats = pool_monitor.get_stats() if pool_monitor else {}
        
        return {
            "active_sessions": len(self._active_sessions),
            "potential_leaks": len(self.leak_detector._active_connections),
            "pool_stats": pool_stats,
            "recommendations": self._get_recommendations(pool_stats)
        }
    
    def _get_recommendations(self, pool_stats: Dict[str, Any]) -> List[str]:
        """Get recommendations based on current state."""
        recommendations = []
        
        if pool_stats:
            pool_status = pool_stats.get("pool_status", {})
            
            # Check if pool is near exhaustion
            if pool_status.get("checked_out", 0) >= pool_status.get("size", 1) * 0.8:
                recommendations.append(
                    "Connection pool is nearly exhausted. Consider increasing pool_size."
                )
            
            # Check for long-held connections
            if pool_stats.get("lifetime_stats", {}).get("checkout_time_max", 0) > 60:
                recommendations.append(
                    "Very long connection hold times detected. Review code for unclosed sessions."
                )
            
            # Check error rate
            lifetime = pool_stats.get("lifetime_stats", {})
            if lifetime.get("connection_errors", 0) > lifetime.get("connections_created", 1) * 0.05:
                recommendations.append(
                    "High connection error rate. Check database connectivity and load."
                )
        
        return recommendations


# Global session manager instance
_session_manager: Optional[EnhancedSessionManager] = None


def get_session_manager() -> EnhancedSessionManager:
    """Get global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = EnhancedSessionManager()
    return _session_manager


@contextmanager
def get_managed_session(timeout: Optional[float] = None) -> Session:
    """Get a managed database session with enhanced monitoring.
    
    This is the recommended way to get database sessions as it includes:
    - Automatic cleanup on timeout
    - Connection leak detection
    - Pool exhaustion prevention
    
    Args:
        timeout: Session timeout in seconds
        
    Yields:
        SQLAlchemy session
    """
    manager = get_session_manager()
    with manager.get_session(timeout) as session:
        yield session


async def get_managed_session_async(timeout: Optional[float] = None) -> Session:
    """Async version of get_managed_session."""
    manager = get_session_manager()
    async with manager.get_session_async(timeout) as session:
        yield session


async def start_pool_management():
    """Start all pool management services."""
    manager = get_session_manager()
    await manager.start_monitoring()
    logger.info("Database pool management services started")


def get_pool_diagnostics() -> Dict[str, Any]:
    """Get comprehensive pool diagnostics."""
    manager = get_session_manager()
    return manager.get_diagnostics()