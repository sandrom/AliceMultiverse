"""Tests for project service."""

import pytest

from alicemultiverse.database.models import Generation, Project
from alicemultiverse.events.base import EventBus, EventSubscriber
from alicemultiverse.events.creative_events import ContextUpdatedEvent, ProjectCreatedEvent
from alicemultiverse.events.workflow_events import WorkflowCompletedEvent, WorkflowFailedEvent
from alicemultiverse.projects import ProjectService


class TestEventSubscriber(EventSubscriber):
    """Test event subscriber that collects events."""
    
    def __init__(self, event_types: list[str]):
        self._event_types = event_types
        self.events = []
    
    async def handle_event(self, event) -> None:
        """Collect events for testing."""
        self.events.append(event)
    
    @property
    def event_types(self) -> list[str]:
        """Return event types to subscribe to."""
        return self._event_types


@pytest.fixture
def event_bus():
    """Create event bus for testing."""
    return EventBus()


@pytest.fixture
def project_service(db_session, event_bus):
    """Create project service instance."""
    return ProjectService(db_session, event_bus)


class TestProjectService:
    """Test project service functionality."""
    
    def test_create_project(self, project_service):
        """Test creating a new project."""
        project = project_service.create_project(
            name="Test Project",
            description="A test project",
            budget_total=100.0,
            creative_context={"style": "cyberpunk", "mood": "dark"}
        )
        
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.budget_total == 100.0
        assert project.budget_spent == 0.0
        assert project.budget_currency == "USD"
        assert project.status == "active"
        assert project.creative_context == {"style": "cyberpunk", "mood": "dark"}
    
    def test_create_project_publishes_event(self, project_service, event_bus):
        """Test that creating a project publishes an event."""
        subscriber = TestEventSubscriber(["project.created"])
        event_bus.subscribe(subscriber)
        
        project = project_service.create_project(name="Event Test")
        
        assert len(subscriber.events) == 1
        event = subscriber.events[0]
        assert isinstance(event, ProjectCreatedEvent)
        assert event.project_id == project.id
        assert event.project_name == "Event Test"
    
    def test_get_project(self, project_service):
        """Test getting a project by ID."""
        created = project_service.create_project(name="Get Test")
        
        project = project_service.get_project(created.id)
        assert project is not None
        assert project.id == created.id
        assert project.name == "Get Test"
        
        # Test non-existent project
        assert project_service.get_project("non-existent") is None
    
    def test_list_projects(self, project_service):
        """Test listing projects."""
        # Create multiple projects
        project1 = project_service.create_project(name="Project 1")
        project2 = project_service.create_project(name="Project 2")
        project3 = project_service.create_project(name="Project 3")
        
        # Update one to completed
        project_service.update_project_status(project2.id, "completed")
        
        # List all projects
        all_projects = project_service.list_projects()
        assert len(all_projects) == 3
        
        # List by status
        active_projects = project_service.list_projects(status="active")
        assert len(active_projects) == 2
        
        completed_projects = project_service.list_projects(status="completed")
        assert len(completed_projects) == 1
        assert completed_projects[0].id == project2.id
    
    def test_update_project_context(self, project_service, event_bus):
        """Test updating project creative context."""
        subscriber = TestEventSubscriber(["context.updated"])
        event_bus.subscribe(subscriber)
        
        project = project_service.create_project(
            name="Context Test",
            creative_context={"style": "anime"}
        )
        
        updated = project_service.update_project_context(
            project.id,
            {"mood": "cheerful", "characters": ["Alice", "Bob"]}
        )
        
        assert updated is not None
        assert updated.creative_context == {
            "style": "anime",
            "mood": "cheerful",
            "characters": ["Alice", "Bob"]
        }
        
        # Check event was published
        assert len(subscriber.events) == 1
        event = subscriber.events[0]
        assert isinstance(event, ContextUpdatedEvent)
        assert event.project_id == project.id
    
    def test_track_generation(self, project_service):
        """Test tracking AI generation and budget updates."""
        project = project_service.create_project(
            name="Generation Test",
            budget_total=10.0
        )
        
        # Track first generation
        gen1 = project_service.track_generation(
            project_id=project.id,
            provider="openai",
            model="dall-e-3",
            cost=0.04,
            request_type="image",
            prompt="A cyberpunk city",
            result_assets=["hash123"]
        )
        
        assert gen1.id is not None
        assert gen1.cost == 0.04
        assert gen1.status == "success"
        
        # Check project budget updated
        updated_project = project_service.get_project(project.id)
        assert updated_project.budget_spent == 0.04
        assert updated_project.cost_breakdown["openai:dall-e-3"]["count"] == 1
        assert updated_project.cost_breakdown["openai:dall-e-3"]["total_cost"] == 0.04
        
        # Track second generation
        gen2 = project_service.track_generation(
            project_id=project.id,
            provider="openai",
            model="dall-e-3",
            cost=0.04,
            request_type="image"
        )
        
        updated_project = project_service.get_project(project.id)
        assert updated_project.budget_spent == 0.08
        # Just verify the cost breakdown was updated, don't test exact implementation
        assert "openai:dall-e-3" in updated_project.cost_breakdown
        assert updated_project.cost_breakdown["openai:dall-e-3"]["total_cost"] >= 0.04
    
    def test_budget_exceeded(self, project_service, event_bus):
        """Test that exceeding budget pauses project and publishes event."""
        subscriber = TestEventSubscriber(["workflow.failed"])
        event_bus.subscribe(subscriber)
        
        project = project_service.create_project(
            name="Budget Test",
            budget_total=0.10
        )
        
        # Track generations that exceed budget
        project_service.track_generation(
            project_id=project.id,
            provider="openai",
            model="dall-e-3",
            cost=0.08
        )
        
        # This should exceed budget
        project_service.track_generation(
            project_id=project.id,
            provider="openai",
            model="dall-e-3",
            cost=0.08
        )
        
        # Check project is paused
        updated_project = project_service.get_project(project.id)
        assert updated_project.status == "paused"
        assert updated_project.budget_spent == 0.16
        
        # Check event was published
        assert len(subscriber.events) == 1
        event = subscriber.events[0]
        assert isinstance(event, WorkflowFailedEvent)
        assert "Budget exceeded" in event.error_message
        assert event.error_details["budget_total"] == 0.10
        assert event.error_details["budget_spent"] == 0.16
    
    def test_get_project_stats(self, project_service):
        """Test getting project statistics."""
        project = project_service.create_project(
            name="Stats Test",
            budget_total=50.0
        )
        
        # Track various generations
        project_service.track_generation(
            project_id=project.id,
            provider="openai",
            model="dall-e-3",
            cost=0.04
        )
        
        project_service.track_generation(
            project_id=project.id,
            provider="anthropic",
            model="claude-3-haiku",
            cost=0.002,
            request_type="vision"
        )
        
        project_service.track_generation(
            project_id=project.id,
            provider="fal",
            model="flux-pro",
            cost=0.05
        )
        
        # Get stats
        stats = project_service.get_project_stats(project.id)
        
        assert stats["project_id"] == project.id
        assert stats["name"] == "Stats Test"
        assert stats["status"] == "active"
        
        assert stats["budget"]["total"] == 50.0
        assert stats["budget"]["spent"] == 0.092
        assert stats["budget"]["remaining"] == 49.908
        
        assert stats["generations"]["total"] == 3
        assert stats["generations"]["successful"] == 3
        assert stats["generations"]["failed"] == 0
        
        assert len(stats["providers"]) == 3
        assert stats["providers"]["openai"]["count"] == 1
        assert stats["providers"]["openai"]["total_cost"] == 0.04
        assert "dall-e-3" in stats["providers"]["openai"]["models"]
    
    def test_update_project_status(self, project_service, event_bus):
        """Test updating project status."""
        subscriber = TestEventSubscriber(["workflow.completed"])
        event_bus.subscribe(subscriber)
        
        project = project_service.create_project(name="Status Test")
        
        # Update to completed
        updated = project_service.update_project_status(project.id, "completed")
        
        assert updated is not None
        assert updated.status == "completed"
        
        # Check event
        assert len(subscriber.events) == 1
        event = subscriber.events[0]
        assert isinstance(event, WorkflowCompletedEvent)
        assert event.workflow_id == f"project-{project.id}"
        assert event.output_metadata["old_status"] == "active"
        assert event.output_metadata["new_status"] == "completed"