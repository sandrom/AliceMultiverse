"""Project service for managing projects and budget tracking."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from alicemultiverse.database.models import Generation, Project
from alicemultiverse.events.base import BaseEvent, EventBus, create_event
from alicemultiverse.events.creative_events import ContextUpdatedEvent, ProjectCreatedEvent
from alicemultiverse.events.workflow_events import WorkflowCompletedEvent, WorkflowFailedEvent


class ProjectService:
    """Service for managing projects and tracking budgets."""
    
    def __init__(self, db_session: Session, event_bus: EventBus | None = None):
        """Initialize project service.
        
        Args:
            db_session: Database session
            event_bus: Optional event bus for publishing events
        """
        self.db = db_session
        self.event_bus = event_bus
    
    def _publish_event(self, event: BaseEvent) -> None:
        """Publish event handling async in sync context."""
        if not self.event_bus:
            return
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, schedule as task
                asyncio.create_task(self.event_bus.publish(event))
            else:
                loop.run_until_complete(self.event_bus.publish(event))
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.event_bus.publish(event))
            loop.close()
    
    def create_project(
        self, 
        name: str, 
        description: str | None = None,
        budget_total: float | None = None,
        creative_context: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None
    ) -> Project:
        """Create a new project.
        
        Args:
            name: Project name
            description: Optional project description
            budget_total: Optional budget limit in USD
            creative_context: Optional creative context (style, characters, etc.)
            settings: Optional project-specific settings
            
        Returns:
            Created project
        """
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            budget_total=budget_total,
            budget_spent=0.0,
            budget_currency="USD",
            status="active",
            creative_context=creative_context or {},
            settings=settings or {},
            cost_breakdown={}
        )
        
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        
        # Publish event
        event = create_event(
            ProjectCreatedEvent,
            source="project_service",
            project_id=project.id,
            project_name=project.name,
            description=project.description,
            initial_context=project.creative_context
        )
        self._publish_event(event)
        
        return project
    
    def get_project(self, project_id: str) -> Project | None:
        """Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project or None if not found
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project:
            self.db.refresh(project)
        return project
    
    def list_projects(self, status: str | None = None) -> list[Project]:
        """List all projects, optionally filtered by status.
        
        Args:
            status: Optional status filter (active, paused, completed, archived)
            
        Returns:
            List of projects
        """
        query = self.db.query(Project)
        if status:
            query = query.filter(Project.status == status)
        return query.order_by(Project.created_at.desc()).all()
    
    def update_project_context(
        self, 
        project_id: str, 
        creative_context: dict[str, Any]
    ) -> Project | None:
        """Update project creative context.
        
        Args:
            project_id: Project ID
            creative_context: New creative context to merge
            
        Returns:
            Updated project or None if not found
        """
        project = self.get_project(project_id)
        if not project:
            return None
        
        # Merge creative context
        project.creative_context = {**project.creative_context, **creative_context}
        project.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(project)
        
        # Publish event
        event = create_event(
            ContextUpdatedEvent,
            source="project_service",
            project_id=project.id,
            context_type="creative",
            update_type="modification",
            context_key="creative_context",
            new_value=project.creative_context
        )
        self._publish_event(event)
        
        return project
    
    def track_generation(
        self,
        project_id: str,
        provider: str,
        model: str,
        cost: float,
        request_type: str = "image",
        prompt: str | None = None,
        parameters: dict[str, Any] | None = None,
        result_assets: list[str] | None = None
    ) -> Generation:
        """Track an AI generation request and update project budget.
        
        Args:
            project_id: Project ID
            provider: Provider name (fal, openai, anthropic)
            model: Model name
            cost: Cost in USD
            request_type: Type of request (image, video, vision, text)
            prompt: Optional prompt used
            parameters: Optional model parameters
            result_assets: Optional list of resulting asset content hashes
            
        Returns:
            Created generation record
        """
        # Get fresh project from DB to avoid stale data
        # First expire any existing project instance
        existing = self.db.query(Project).filter(Project.id == project_id).first()
        if existing:
            self.db.expire(existing)
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Create generation record
        generation = Generation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            provider=provider,
            model=model,
            request_type=request_type,
            prompt=prompt,
            parameters=parameters or {},
            cost=cost,
            currency="USD",
            status="success",
            result_assets=result_assets or [],
            completed_at=datetime.now(timezone.utc)
        )
        
        self.db.add(generation)
        
        # Update project budget
        project.budget_spent = (project.budget_spent or 0.0) + cost
        
        # Update cost breakdown - need to create new dict for SQLAlchemy to track changes
        provider_key = f"{provider}:{model}"
        cost_breakdown = dict(project.cost_breakdown) if project.cost_breakdown else {}
        
        if provider_key not in cost_breakdown:
            cost_breakdown[provider_key] = {
                "count": 0,
                "total_cost": 0.0,
                "average_cost": 0.0
            }
        
        breakdown = cost_breakdown[provider_key]
        breakdown["count"] += 1
        breakdown["total_cost"] += cost
        breakdown["average_cost"] = breakdown["total_cost"] / breakdown["count"]
        
        # Assign back to trigger SQLAlchemy change detection
        project.cost_breakdown = cost_breakdown
        
        # Check if budget exceeded
        if project.budget_total and project.budget_spent > project.budget_total:
            project.status = "paused"
            
            # Publish budget exceeded event
            event = create_event(
                WorkflowFailedEvent,
                source="project_service",
                workflow_id=f"project-{project.id}",
                workflow_type="budget_management",
                error_type="resource_limit",
                error_message=f"Budget exceeded: spent ${project.budget_spent:.2f} of ${project.budget_total:.2f}",
                error_details={
                    "budget_total": project.budget_total,
                    "budget_spent": project.budget_spent,
                    "overage": project.budget_spent - project.budget_total
                }
            )
            self._publish_event(event)
        
        self.db.commit()
        self.db.refresh(generation)
        
        return generation
    
    def get_project_stats(self, project_id: str) -> dict[str, Any]:
        """Get project statistics including budget and generation details.
        
        Args:
            project_id: Project ID
            
        Returns:
            Dictionary with project statistics
        """
        project = self.get_project(project_id)
        if not project:
            return {}
        
        # Get generation stats
        generations = self.db.query(Generation).filter(
            Generation.project_id == project_id
        ).all()
        
        total_generations = len(generations)
        successful_generations = sum(1 for g in generations if g.status == "success")
        failed_generations = sum(1 for g in generations if g.status == "failed")
        
        # Group by provider
        provider_stats = {}
        for gen in generations:
            if gen.provider not in provider_stats:
                provider_stats[gen.provider] = {
                    "count": 0,
                    "total_cost": 0.0,
                    "models": set()
                }
            provider_stats[gen.provider]["count"] += 1
            provider_stats[gen.provider]["total_cost"] += gen.cost or 0.0
            provider_stats[gen.provider]["models"].add(gen.model)
        
        # Convert sets to lists for JSON serialization
        for provider in provider_stats:
            provider_stats[provider]["models"] = list(provider_stats[provider]["models"])
        
        return {
            "project_id": project.id,
            "name": project.name,
            "status": project.status,
            "budget": {
                "total": project.budget_total,
                "spent": project.budget_spent,
                "remaining": (project.budget_total - project.budget_spent) if project.budget_total else None,
                "currency": project.budget_currency
            },
            "generations": {
                "total": total_generations,
                "successful": successful_generations,
                "failed": failed_generations
            },
            "providers": provider_stats,
            "cost_breakdown": project.cost_breakdown,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        }
    
    def update_project_status(self, project_id: str, status: str) -> Project | None:
        """Update project status.
        
        Args:
            project_id: Project ID
            status: New status (active, paused, completed, archived)
            
        Returns:
            Updated project or None if not found
        """
        project = self.get_project(project_id)
        if not project:
            return None
        
        old_status = project.status
        project.status = status
        project.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(project)
        
        # Publish event
        if status == "completed":
            event = create_event(
                WorkflowCompletedEvent,
                source="project_service",
                workflow_id=f"project-{project.id}",
                workflow_type="project_lifecycle",
                total_duration_ms=0,  # Would need to calculate from created_at
                steps_completed=0,  # Would need to track
                output_metadata={
                    "old_status": old_status,
                    "new_status": status,
                    "project_name": project.name
                }
            )
        else:
            event = create_event(
                ContextUpdatedEvent,
                source="project_service",
                project_id=project.id,
                context_type="status",
                update_type="modification",
                context_key="status",
                new_value={"status": status},
                previous_value={"status": old_status}
            )
        self._publish_event(event)
        
        return project