"""Project service for managing projects and budget tracking."""

import hashlib
from datetime import datetime
from typing import Any

from alicemultiverse.core.config import load_config
from alicemultiverse.events import publish_event_sync

from .file_service import FileProjectService


class ProjectService:
    """Service for managing projects and tracking budgets.

    Uses file-based storage when database is not available.
    """

    def __init__(self, db_session: Any | None = None, event_bus: Any | None = None, config=None):
        """Initialize project service.

        Args:
            db_session: Database session (no longer used)
            event_bus: Deprecated, kept for compatibility
            config: Optional configuration object
        """
        self.db = None

        # Load config if not provided
        if not config:
            config = load_config()

        # Get storage paths from config
        storage_paths = None
        if hasattr(config, 'storage') and hasattr(config.storage, 'project_paths'):
            storage_paths = list(config.storage.project_paths)

        # Always use file-based service
        self._file_service = FileProjectService(storage_paths)

    def _publish_event(self, event_type: str, **data) -> None:
        """Publish event using Redis Streams."""
        publish_event_sync(event_type, data)

    def create_project(
        self,
        name: str,
        description: str | None = None,
        budget_total: float | None = None,
        creative_context: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None
    ) -> dict | None:
        """Create a new project.

        Uses file-based storage when database is not available.

        Returns:
            Project dict or None
        """
        if self._file_service:
            return self._file_service.create_project(
                name=name,
                description=description,
                budget_total=budget_total,
                creative_context=creative_context,
                settings=settings
            )

        # Database implementation would go here
        # For now, just publish event
        self._publish_event(
            "project.created",
            source="project_service",
            # Use name-based project ID for easier identification
            project_id=hashlib.sha256(f"{name}:{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            project_name=name,
            description=description,
            initial_context=creative_context or {}
        )

        return None

    # TODO: Review unreachable code - def get_project(self, project_id: str) -> dict | None:
    # TODO: Review unreachable code - """Get project by ID.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.get_project(project_id)

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def list_projects(self, status: str | None = None) -> list:
    # TODO: Review unreachable code - """List all projects, optionally filtered by status.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of project dicts
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.list_projects(status)

    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - def update_project_context(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_id: str,
    # TODO: Review unreachable code - creative_context: dict[str, Any]
    # TODO: Review unreachable code - ) -> dict | None:
    # TODO: Review unreachable code - """Update project creative context.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Updated project dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.update_project_context(project_id, creative_context)

    # TODO: Review unreachable code - # Publish event even though we can't update database
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "project.context.updated",
    # TODO: Review unreachable code - source="project_service",
    # TODO: Review unreachable code - project_id=project_id,
    # TODO: Review unreachable code - context_update=creative_context
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def update_project_status(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_id: str,
    # TODO: Review unreachable code - status: str
    # TODO: Review unreachable code - ) -> dict | None:
    # TODO: Review unreachable code - """Update project status.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Updated project dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.update_project_status(project_id, status)

    # TODO: Review unreachable code - # Publish event even though we can't update database
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "project.status.changed",
    # TODO: Review unreachable code - source="project_service",
    # TODO: Review unreachable code - project_id=project_id,
    # TODO: Review unreachable code - old_status="unknown",
    # TODO: Review unreachable code - new_status=status
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def record_generation(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_id: str,
    # TODO: Review unreachable code - provider: str,
    # TODO: Review unreachable code - cost: float,
    # TODO: Review unreachable code - request_params: dict[str, Any] | None = None,
    # TODO: Review unreachable code - result_metadata: dict[str, Any] | None = None,
    # TODO: Review unreachable code - file_path: str | None = None
    # TODO: Review unreachable code - ) -> None:
    # TODO: Review unreachable code - """Record a generation and update project budget.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.record_generation(
    # TODO: Review unreachable code - project_id=project_id,
    # TODO: Review unreachable code - provider=provider,
    # TODO: Review unreachable code - cost=cost,
    # TODO: Review unreachable code - request_params=request_params,
    # TODO: Review unreachable code - result_metadata=result_metadata,
    # TODO: Review unreachable code - file_path=file_path
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Publish event for generation
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "generation.completed",
    # TODO: Review unreachable code - source="project_service",
    # TODO: Review unreachable code - project_id=project_id,
    # TODO: Review unreachable code - provider=provider,
    # TODO: Review unreachable code - cost=cost,
    # TODO: Review unreachable code - request_params=request_params or {},
    # TODO: Review unreachable code - result_metadata=result_metadata or {},
    # TODO: Review unreachable code - file_path=file_path
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Publish budget warning event (can't check actual budget)
    # TODO: Review unreachable code - self._publish_event(
    # TODO: Review unreachable code - "project.budget.warning",
    # TODO: Review unreachable code - source="project_service",
    # TODO: Review unreachable code - project_id=project_id,
    # TODO: Review unreachable code - message="Budget tracking unavailable without database"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def get_project_budget_status(self, project_id: str) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Get project budget status.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Budget status dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.get_project_budget_status(project_id)

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def get_project_cost_breakdown(self, project_id: str) -> dict[str, float]:
    # TODO: Review unreachable code - """Get cost breakdown by provider.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dict mapping providers to costs
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.get_project_cost_breakdown(project_id)

    # TODO: Review unreachable code - return {}

    # TODO: Review unreachable code - def find_project_from_path(self, current_path: str | None = None) -> dict | None:
    # TODO: Review unreachable code - """Find project based on current directory.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.find_project_from_path(current_path)

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def get_or_create_project_from_path(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - path: str | None = None,
    # TODO: Review unreachable code - create_if_missing: bool = True
    # TODO: Review unreachable code - ) -> dict | None:
    # TODO: Review unreachable code - """Get project from path or create one if missing.

    # TODO: Review unreachable code - Uses file-based storage when database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self._file_service:
    # TODO: Review unreachable code - return self._file_service.get_or_create_project_from_path(path, create_if_missing)

    # TODO: Review unreachable code - return None
