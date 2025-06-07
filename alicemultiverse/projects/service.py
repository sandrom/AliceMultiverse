"""Project service for managing projects and budget tracking."""

import uuid
from typing import Any, Optional


from alicemultiverse.events import publish_event_sync
from alicemultiverse.core.config import load_config
from .file_service import FileProjectService


class ProjectService:
    """Service for managing projects and tracking budgets.
    
    Uses file-based storage when database is not available.
    """
    
    def __init__(self, db_session: Optional[Any] = None, event_bus: Optional[Any] = None, config=None):
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
            project_id=str(uuid.uuid4()),
            project_name=name,
            description=description,
            initial_context=creative_context or {}
        )
        
        return None
    
    def get_project(self, project_id: str) -> dict | None:
        """Get project by ID.
        
        Uses file-based storage when database is not available.
        
        Returns:
            Project dict or None
        """
        if self._file_service:
            return self._file_service.get_project(project_id)
        
        return None
    
    def list_projects(self, status: str | None = None) -> list:
        """List all projects, optionally filtered by status.
        
        Uses file-based storage when database is not available.
        
        Returns:
            List of project dicts
        """
        if self._file_service:
            return self._file_service.list_projects(status)
        
        return []
    
    def update_project_context(
        self, 
        project_id: str, 
        creative_context: dict[str, Any]
    ) -> dict | None:
        """Update project creative context.
        
        Uses file-based storage when database is not available.
        
        Returns:
            Updated project dict or None
        """
        if self._file_service:
            return self._file_service.update_project_context(project_id, creative_context)
        
        # Publish event even though we can't update database
        self._publish_event(
            "project.context.updated",
            source="project_service",
            project_id=project_id,
            context_update=creative_context
        )
        
        return None
    
    def update_project_status(
        self,
        project_id: str,
        status: str
    ) -> dict | None:
        """Update project status.
        
        Uses file-based storage when database is not available.
        
        Returns:
            Updated project dict or None
        """
        if self._file_service:
            return self._file_service.update_project_status(project_id, status)
        
        # Publish event even though we can't update database
        self._publish_event(
            "project.status.changed",
            source="project_service",
            project_id=project_id,
            old_status="unknown",
            new_status=status
        )
        
        return None
    
    def record_generation(
        self,
        project_id: str,
        provider: str,
        cost: float,
        request_params: dict[str, Any] | None = None,
        result_metadata: dict[str, Any] | None = None,
        file_path: str | None = None
    ) -> None:
        """Record a generation and update project budget.
        
        Uses file-based storage when database is not available.
        """
        if self._file_service:
            return self._file_service.record_generation(
                project_id=project_id,
                provider=provider,
                cost=cost,
                request_params=request_params,
                result_metadata=result_metadata,
                file_path=file_path
            )
        
        # Publish event for generation
        self._publish_event(
            "generation.completed",
            source="project_service",
            project_id=project_id,
            provider=provider,
            cost=cost,
            request_params=request_params or {},
            result_metadata=result_metadata or {},
            file_path=file_path
        )
        
        # Publish budget warning event (can't check actual budget)
        self._publish_event(
            "project.budget.warning",
            source="project_service",
            project_id=project_id,
            message="Budget tracking unavailable without database"
        )
    
    def get_project_budget_status(self, project_id: str) -> dict[str, Any] | None:
        """Get project budget status.
        
        Uses file-based storage when database is not available.
        
        Returns:
            Budget status dict or None
        """
        if self._file_service:
            return self._file_service.get_project_budget_status(project_id)
        
        return None
    
    def get_project_cost_breakdown(self, project_id: str) -> dict[str, float]:
        """Get cost breakdown by provider.
        
        Uses file-based storage when database is not available.
        
        Returns:
            Dict mapping providers to costs
        """
        if self._file_service:
            return self._file_service.get_project_cost_breakdown(project_id)
        
        return {}
    
    def find_project_from_path(self, current_path: str | None = None) -> dict | None:
        """Find project based on current directory.
        
        Uses file-based storage when database is not available.
        
        Returns:
            Project dict or None
        """
        if self._file_service:
            return self._file_service.find_project_from_path(current_path)
        
        return None
    
    def get_or_create_project_from_path(
        self, 
        path: str | None = None,
        create_if_missing: bool = True
    ) -> dict | None:
        """Get project from path or create one if missing.
        
        Uses file-based storage when database is not available.
        
        Returns:
            Project dict or None
        """
        if self._file_service:
            return self._file_service.get_or_create_project_from_path(path, create_if_missing)
        
        return None