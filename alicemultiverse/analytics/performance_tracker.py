"""Performance tracking for creative workflows."""

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from ..core.config import DictConfig as Config
from ..core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowMetrics:
    """Metrics for a single workflow execution."""
    workflow_id: str
    workflow_type: str  # video_creation, timeline_export, etc.
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "in_progress"  # in_progress, completed, failed
    
    # Performance metrics
    clips_processed: int = 0
    effects_applied: int = 0
    exports_created: int = 0
    api_calls_made: int = 0
    
    # Resource usage
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    
    # Quality metrics
    output_resolution: Optional[Tuple[int, int]] = None
    output_duration: Optional[float] = None
    file_size_mb: Optional[float] = None
    
    # User actions
    manual_adjustments: int = 0
    preview_views: int = 0
    exports_redone: int = 0
    
    # Platform performance
    platforms_exported: List[str] = field(default_factory=list)
    platform_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMetrics:
    """Metrics for a complete user session."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    workflows_completed: int = 0
    workflows_failed: int = 0
    total_exports: int = 0
    total_api_calls: int = 0
    total_duration_seconds: float = 0.0
    popular_features: Dict[str, int] = field(default_factory=dict)
    common_errors: Dict[str, int] = field(default_factory=dict)


class PerformanceTracker:
    """Track and analyze workflow performance."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize performance tracker.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        
        # Storage paths
        self.data_dir = Path.home() / ".alice" / "analytics"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.data_dir / "performance_metrics.json"
        self.sessions_file = self.data_dir / "session_metrics.json"
        
        # Active tracking
        self.active_workflows: Dict[str, WorkflowMetrics] = {}
        self.current_session: Optional[SessionMetrics] = None
        
        # Load historical data
        self.historical_metrics = self._load_metrics()
        self.historical_sessions = self._load_sessions()
    
    def start_session(self, session_id: str) -> SessionMetrics:
        """Start a new tracking session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            New session metrics
        """
        self.current_session = SessionMetrics(
            session_id=session_id,
            start_time=datetime.now()
        )
        return self.current_session
    
    def end_session(self) -> Optional[SessionMetrics]:
        """End current session and save metrics.
        
        Returns:
            Completed session metrics
        """
        if not self.current_session:
            return None
        
        self.current_session.end_time = datetime.now()
        
        # Calculate total duration
        duration = (self.current_session.end_time - self.current_session.start_time).total_seconds()
        self.current_session.total_duration_seconds = duration
        
        # Save session
        self._save_session(self.current_session)
        
        session = self.current_session
        self.current_session = None
        
        return session
    
    def start_workflow(
        self,
        workflow_id: str,
        workflow_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowMetrics:
        """Start tracking a workflow.
        
        Args:
            workflow_id: Unique workflow identifier
            workflow_type: Type of workflow (video_creation, export, etc.)
            metadata: Additional metadata
            
        Returns:
            New workflow metrics
        """
        metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self.active_workflows[workflow_id] = metrics
        logger.info(f"Started tracking workflow: {workflow_id} ({workflow_type})")
        
        return metrics
    
    def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> Optional[WorkflowMetrics]:
        """Update workflow metrics.
        
        Args:
            workflow_id: Workflow to update
            updates: Dictionary of updates
            
        Returns:
            Updated metrics or None
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow not found: {workflow_id}")
            return None
        
        metrics = self.active_workflows[workflow_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(metrics, key):
                if isinstance(getattr(metrics, key), list):
                    getattr(metrics, key).extend(value if isinstance(value, list) else [value])
                elif isinstance(getattr(metrics, key), dict):
                    getattr(metrics, key).update(value)
                elif isinstance(getattr(metrics, key), int) and isinstance(value, int):
                    setattr(metrics, key, getattr(metrics, key) + value)
                else:
                    setattr(metrics, key, value)
        
        return metrics
    
    def end_workflow(
        self,
        workflow_id: str,
        status: str = "completed"
    ) -> Optional[WorkflowMetrics]:
        """End workflow tracking.
        
        Args:
            workflow_id: Workflow to end
            status: Final status
            
        Returns:
            Completed metrics or None
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow not found: {workflow_id}")
            return None
        
        metrics = self.active_workflows[workflow_id]
        metrics.end_time = datetime.now()
        metrics.status = status
        metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
        
        # Update session
        if self.current_session:
            if status == "completed":
                self.current_session.workflows_completed += 1
            else:
                self.current_session.workflows_failed += 1
            
            self.current_session.total_exports += metrics.exports_created
            self.current_session.total_api_calls += metrics.api_calls_made
            
            # Track feature usage
            feature = metrics.workflow_type
            self.current_session.popular_features[feature] = \
                self.current_session.popular_features.get(feature, 0) + 1
            
            # Track errors
            for error in metrics.errors:
                self.current_session.common_errors[error] = \
                    self.current_session.common_errors.get(error, 0) + 1
        
        # Save metrics
        self._save_workflow_metrics(metrics)
        
        # Remove from active
        del self.active_workflows[workflow_id]
        
        logger.info(f"Completed workflow: {workflow_id} ({status})")
        return metrics
    
    def track_export(
        self,
        workflow_id: str,
        platform: str,
        success: bool,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track an export operation.
        
        Args:
            workflow_id: Associated workflow
            platform: Export platform
            success: Whether export succeeded
            duration: Export duration in seconds
            metadata: Additional metadata
        """
        updates = {
            "exports_created": 1 if success else 0,
            "platforms_exported": [platform] if success else [],
            "platform_metrics": {
                platform: {
                    "success": success,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            }
        }
        
        self.update_workflow(workflow_id, updates)
    
    def track_api_call(
        self,
        workflow_id: str,
        provider: str,
        success: bool,
        duration: float,
        cost: Optional[float] = None
    ):
        """Track an API call.
        
        Args:
            workflow_id: Associated workflow
            provider: API provider
            success: Whether call succeeded
            duration: Call duration
            cost: API cost if applicable
        """
        updates = {
            "api_calls_made": 1,
            "metadata": {
                f"api_{provider}_calls": 1,
                f"api_{provider}_duration": duration
            }
        }
        
        if cost is not None:
            updates["metadata"][f"api_{provider}_cost"] = cost
        
        if not success:
            updates["errors"] = [f"API call failed: {provider}"]
        
        self.update_workflow(workflow_id, updates)
    
    def track_user_action(
        self,
        workflow_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track a user action.
        
        Args:
            workflow_id: Associated workflow
            action: Action type (adjustment, preview, redo, etc.)
            metadata: Additional context
        """
        action_map = {
            "adjustment": "manual_adjustments",
            "preview": "preview_views",
            "redo": "exports_redone"
        }
        
        if action in action_map:
            updates = {action_map[action]: 1}
            self.update_workflow(workflow_id, updates)
        
        # Log detailed action
        if metadata:
            self.update_workflow(workflow_id, {
                "metadata": {f"action_{action}": metadata}
            })
    
    def get_workflow_summary(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of workflow performance.
        
        Args:
            workflow_id: Workflow to summarize
            
        Returns:
            Summary dictionary or None
        """
        metrics = None
        
        # Check active workflows
        if workflow_id in self.active_workflows:
            metrics = self.active_workflows[workflow_id]
        else:
            # Check historical
            for m in self.historical_metrics:
                if m["workflow_id"] == workflow_id:
                    metrics = WorkflowMetrics(**m)
                    break
        
        if not metrics:
            return None
        
        return {
            "workflow_id": metrics.workflow_id,
            "type": metrics.workflow_type,
            "status": metrics.status,
            "duration": metrics.duration_seconds,
            "performance": {
                "clips_processed": metrics.clips_processed,
                "effects_applied": metrics.effects_applied,
                "exports_created": metrics.exports_created,
                "api_calls": metrics.api_calls_made
            },
            "quality": {
                "resolution": metrics.output_resolution,
                "duration": metrics.output_duration,
                "file_size_mb": metrics.file_size_mb
            },
            "user_actions": {
                "adjustments": metrics.manual_adjustments,
                "previews": metrics.preview_views,
                "redos": metrics.exports_redone
            },
            "platforms": metrics.platforms_exported,
            "errors": len(metrics.errors),
            "warnings": len(metrics.warnings)
        }
    
    def get_performance_stats(
        self,
        time_range: Optional[timedelta] = None,
        workflow_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated performance statistics.
        
        Args:
            time_range: Time range to analyze
            workflow_type: Filter by workflow type
            
        Returns:
            Performance statistics
        """
        # Filter metrics
        metrics = self.historical_metrics.copy()
        
        if time_range:
            cutoff = datetime.now() - time_range
            metrics = [
                m for m in metrics
                if datetime.fromisoformat(m["start_time"]) > cutoff
            ]
        
        if workflow_type:
            metrics = [m for m in metrics if m["workflow_type"] == workflow_type]
        
        if not metrics:
            return {
                "total_workflows": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "common_errors": {},
                "popular_platforms": {},
                "resource_usage": {}
            }
        
        # Calculate stats
        total = len(metrics)
        completed = sum(1 for m in metrics if m["status"] == "completed")
        
        durations = [m["duration_seconds"] for m in metrics if m.get("duration_seconds")]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Aggregate errors
        error_counts = defaultdict(int)
        for m in metrics:
            for error in m.get("errors", []):
                error_counts[error] += 1
        
        # Aggregate platforms
        platform_counts = defaultdict(int)
        for m in metrics:
            for platform in m.get("platforms_exported", []):
                platform_counts[platform] += 1
        
        # Resource usage
        memory_values = [m["memory_mb"] for m in metrics if m.get("memory_mb")]
        cpu_values = [m["cpu_percent"] for m in metrics if m.get("cpu_percent")]
        
        return {
            "total_workflows": total,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "average_duration": avg_duration,
            "common_errors": dict(sorted(
                error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            "popular_platforms": dict(sorted(
                platform_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            "resource_usage": {
                "avg_memory_mb": sum(memory_values) / len(memory_values) if memory_values else 0,
                "avg_cpu_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0
            }
        }
    
    def get_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """Identify areas for improvement based on historical data.
        
        Returns:
            List of improvement suggestions
        """
        opportunities = []
        
        stats = self.get_performance_stats(time_range=timedelta(days=30))
        
        # Check success rate
        if stats["success_rate"] < 90:
            opportunities.append({
                "area": "reliability",
                "issue": f"Success rate is {stats['success_rate']:.1f}%",
                "suggestion": "Review common errors and add error handling",
                "impact": "high"
            })
        
        # Check common errors
        if stats["common_errors"]:
            top_error = list(stats["common_errors"].keys())[0]
            count = stats["common_errors"][top_error]
            opportunities.append({
                "area": "errors",
                "issue": f"'{top_error}' occurred {count} times",
                "suggestion": "Investigate and fix root cause",
                "impact": "high"
            })
        
        # Check export efficiency
        recent_workflows = [
            m for m in self.historical_metrics[-20:]
            if m.get("exports_redone", 0) > 0
        ]
        
        if len(recent_workflows) > 5:
            opportunities.append({
                "area": "efficiency",
                "issue": "Many exports are being redone",
                "suggestion": "Improve preview accuracy or default settings",
                "impact": "medium"
            })
        
        # Check manual adjustments
        high_adjustment_workflows = [
            m for m in self.historical_metrics[-20:]
            if m.get("manual_adjustments", 0) > 3
        ]
        
        if len(high_adjustment_workflows) > 5:
            opportunities.append({
                "area": "automation",
                "issue": "Workflows require many manual adjustments",
                "suggestion": "Analyze common adjustments and automate them",
                "impact": "medium"
            })
        
        return opportunities
    
    def _save_workflow_metrics(self, metrics: WorkflowMetrics):
        """Save workflow metrics to disk."""
        try:
            # Convert to dict
            metrics_dict = asdict(metrics)
            
            # Convert datetime objects
            for key in ["start_time", "end_time"]:
                if metrics_dict.get(key):
                    metrics_dict[key] = metrics_dict[key].isoformat()
            
            # Append to historical
            self.historical_metrics.append(metrics_dict)
            
            # Keep only recent data (last 1000 workflows)
            if len(self.historical_metrics) > 1000:
                self.historical_metrics = self.historical_metrics[-1000:]
            
            # Save to file
            with open(self.metrics_file, 'w') as f:
                json.dump(self.historical_metrics, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def _save_session(self, session: SessionMetrics):
        """Save session metrics to disk."""
        try:
            # Convert to dict
            session_dict = asdict(session)
            
            # Convert datetime objects
            for key in ["start_time", "end_time"]:
                if session_dict.get(key):
                    session_dict[key] = session_dict[key].isoformat()
            
            # Append to historical
            self.historical_sessions.append(session_dict)
            
            # Keep only recent sessions (last 100)
            if len(self.historical_sessions) > 100:
                self.historical_sessions = self.historical_sessions[-100:]
            
            # Save to file
            with open(self.sessions_file, 'w') as f:
                json.dump(self.historical_sessions, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def _load_metrics(self) -> List[Dict[str, Any]]:
        """Load historical metrics from disk."""
        if not self.metrics_file.exists():
            return []
        
        try:
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            return []
    
    def _load_sessions(self) -> List[Dict[str, Any]]:
        """Load historical sessions from disk."""
        if not self.sessions_file.exists():
            return []
        
        try:
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return []