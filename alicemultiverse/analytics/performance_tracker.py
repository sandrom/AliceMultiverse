"""Performance tracking for creative workflows."""

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..core.config import DictConfig as Config
from ..core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowMetrics:
    """Metrics for a single workflow execution."""
    workflow_id: str
    workflow_type: str  # video_creation, timeline_export, etc.
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float | None = None
    status: str = "in_progress"  # in_progress, completed, failed

    # Performance metrics
    clips_processed: int = 0
    effects_applied: int = 0
    exports_created: int = 0
    api_calls_made: int = 0

    # Resource usage
    memory_mb: float | None = None
    cpu_percent: float | None = None

    # Quality metrics
    output_resolution: tuple[int, int] | None = None
    output_duration: float | None = None
    file_size_mb: float | None = None

    # User actions
    manual_adjustments: int = 0
    preview_views: int = 0
    exports_redone: int = 0

    # Platform performance
    platforms_exported: list[str] = field(default_factory=list)
    platform_metrics: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Errors and warnings
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Custom metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMetrics:
    """Metrics for a complete user session."""
    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    workflows_completed: int = 0
    workflows_failed: int = 0
    total_exports: int = 0
    total_api_calls: int = 0
    total_duration_seconds: float = 0.0
    popular_features: dict[str, int] = field(default_factory=dict)
    common_errors: dict[str, int] = field(default_factory=dict)


class PerformanceTracker:
    """Track and analyze workflow performance."""

    def __init__(self, config: Config | None = None):
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
        self.active_workflows: dict[str, WorkflowMetrics] = {}
        self.current_session: SessionMetrics | None = None

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

    def end_session(self) -> SessionMetrics | None:
        """End current session and save metrics.

        Returns:
            Completed session metrics
        """
        if not self.current_session:
            return None

        self.current_session.end_time = datetime.now()

        # Calculate total duration
        duration = (self.current_session.end_time -
                    self.current_session.start_time).total_seconds()
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
        metadata: dict[str, Any] | None = None
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

    def get_performance_stats(
        self,
        time_range: timedelta | None = None,
        workflow_type: str | None = None
    ) -> dict[str, Any]:
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
                if m and datetime.fromisoformat(m["start_time"]) > cutoff
            ]

        if workflow_type:
            metrics = [
                m for m in metrics if m and m["workflow_type"] == workflow_type
            ]

        if not metrics:
            return {
                "total_workflows": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "common_errors": {},
                "popular_platforms": {},
            }

        # Calculate stats
        total = len(metrics)
        completed = sum(
            1 for m in metrics if m and m["status"] == "completed")

        durations = [m["duration_seconds"]
                     for m in metrics if m and m.get("duration_seconds")]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_workflows": total,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "average_duration": avg_duration,
        }

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

    def _load_metrics(self) -> list[dict[str, Any]]:
        """Load historical metrics from disk."""
        if not self.metrics_file.exists():
            return []

        try:
            with open(self.metrics_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            return []

    def _load_sessions(self) -> list[dict[str, Any]]:
        """Load historical sessions from disk."""
        if not self.sessions_file.exists():
            return []

        try:
            with open(self.sessions_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return []