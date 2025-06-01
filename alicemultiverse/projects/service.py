"""Project service for managing projects and budget tracking."""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

# PostgreSQL removed - SQLAlchemy and database models no longer available
# from sqlalchemy.orm import Session
# from alicemultiverse.database.models import Generation, Project

from alicemultiverse.events import publish_event_sync


class ProjectService:
    """Service for managing projects and tracking budgets.
    
    Note: This service requires PostgreSQL which has been removed.
    All methods will return None or empty results.
    """
    
    def __init__(self, db_session: Optional[Any] = None, event_bus: Optional[Any] = None):
        """Initialize project service.
        
        Args:
            db_session: Database session (no longer used)
            event_bus: Deprecated, kept for compatibility
        """
        self.db = None
        # PostgreSQL removed - service is non-functional
    
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
        
        PostgreSQL removed - this method is non-functional.
        
        Returns:
            None (database not available)
        """
        # Publish event even though we can't store in database
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
        
        PostgreSQL removed - this method is non-functional.
        
        Returns:
            None (database not available)
        """
        return None
    
    def list_projects(self, status: str | None = None) -> list:
        """List all projects, optionally filtered by status.
        
        PostgreSQL removed - this method is non-functional.
        
        Returns:
            Empty list (database not available)
        """
        return []
    
    def update_project_context(
        self, 
        project_id: str, 
        creative_context: dict[str, Any]
    ) -> dict | None:
        """Update project creative context.
        
        PostgreSQL removed - this method is non-functional.
        
        Returns:
            None (database not available)
        """
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
        
        PostgreSQL removed - this method is non-functional.
        
        Returns:
            None (database not available)
        """
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
        
        PostgreSQL removed - budget tracking not available.
        Only publishes events.
        """
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
        
        PostgreSQL removed - this method is non-functional.
        
        Returns:
            None (database not available)
        """
        return None
    
    def get_project_cost_breakdown(self, project_id: str) -> dict[str, float]:
        """Get cost breakdown by provider.
        
        PostgreSQL removed - this method is non-functional.
        
        Returns:
            Empty dict (database not available)
        """
        return {}