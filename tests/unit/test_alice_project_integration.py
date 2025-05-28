"""Tests for Alice interface project management integration."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from alicemultiverse.interface.alice_interface import AliceInterface


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = MagicMock()
    config.enhanced_metadata = True
    config.database_url = "sqlite:///:memory:"
    return config


@pytest.fixture
def alice_interface(mock_config):
    """Create Alice interface with mocked dependencies."""
    with patch("alicemultiverse.interface.alice_interface.load_config", return_value=mock_config):
        with patch("alicemultiverse.interface.alice_interface.init_db") as mock_init_db:
            with patch("alicemultiverse.interface.alice_interface.AssetRepository"):
                with patch("alicemultiverse.interface.alice_interface.ProjectRepository"):
                    with patch("alicemultiverse.interface.alice_interface.ProjectService") as mock_project_service_class:
                        # Mock database session
                        mock_session = MagicMock()
                        mock_init_db.return_value = mock_session
                        
                        # Create interface
                        interface = AliceInterface()
                        
                        # Mock the organizer to prevent initialization errors
                        interface.organizer = MagicMock()
                        interface.initialization_error = None
                        
                        # The project service is already mocked via the patch
                        
                        return interface


class TestAliceProjectIntegration:
    """Test project management through Alice interface."""
    
    def test_create_project(self, alice_interface):
        """Test creating a project through Alice."""
        # Mock project service response
        mock_project = MagicMock()
        mock_project.id = "proj-123"
        mock_project.name = "Test Project"
        mock_project.budget_total = 100.0
        mock_project.status = "active"
        
        alice_interface.project_service.create_project.return_value = mock_project
        
        # Create project
        response = alice_interface.create_project(
            name="Test Project",
            description="A test project",
            budget=100.0,
            creative_context={"style": "cyberpunk"}
        )
        
        assert response["success"] is True
        assert response["message"] == "Created project 'Test Project'"
        assert response["data"]["project_id"] == "proj-123"
        assert response["data"]["budget"] == 100.0
        
        # Verify service was called correctly
        alice_interface.project_service.create_project.assert_called_once_with(
            name="Test Project",
            description="A test project",
            budget_total=100.0,
            creative_context={"style": "cyberpunk"}
        )
    
    def test_update_project_context(self, alice_interface):
        """Test updating project context."""
        # Mock project service response
        mock_project = MagicMock()
        mock_project.id = "proj-123"
        mock_project.creative_context = {"style": "cyberpunk", "mood": "dark"}
        
        alice_interface.project_service.update_project_context.return_value = mock_project
        
        # Update context
        response = alice_interface.update_project_context(
            project_id="proj-123",
            creative_context={"mood": "dark"}
        )
        
        assert response["success"] is True
        assert response["message"] == "Updated project context"
        assert response["data"]["creative_context"]["mood"] == "dark"
    
    def test_update_project_context_not_found(self, alice_interface):
        """Test updating non-existent project."""
        alice_interface.project_service.update_project_context.return_value = None
        
        response = alice_interface.update_project_context(
            project_id="non-existent",
            creative_context={"mood": "dark"}
        )
        
        assert response["success"] is False
        assert "not found" in response["message"]
    
    def test_get_project_budget_status(self, alice_interface):
        """Test getting project budget status."""
        # Mock stats
        mock_stats = {
            "project_id": "proj-123",
            "name": "Test Project",
            "status": "active",
            "budget": {
                "total": 100.0,
                "spent": 25.0,
                "remaining": 75.0,
                "currency": "USD"
            },
            "generations": {
                "total": 5,
                "successful": 5,
                "failed": 0
            }
        }
        
        alice_interface.project_service.get_project_stats.return_value = mock_stats
        
        response = alice_interface.get_project_budget_status("proj-123")
        
        assert response["success"] is True
        assert response["data"]["budget"]["spent"] == 25.0
        assert response["data"]["budget"]["remaining"] == 75.0
    
    def test_list_projects(self, alice_interface):
        """Test listing projects."""
        # Mock projects
        mock_projects = []
        for i in range(3):
            project = MagicMock()
            project.id = f"proj-{i}"
            project.name = f"Project {i}"
            project.description = f"Description {i}"
            project.status = "active"
            project.budget_total = 100.0 * (i + 1)
            project.budget_spent = 10.0 * (i + 1)
            project.created_at = None
            mock_projects.append(project)
        
        alice_interface.project_service.list_projects.return_value = mock_projects
        
        response = alice_interface.list_projects()
        
        assert response["success"] is True
        assert len(response["data"]["projects"]) == 3
        assert response["data"]["projects"][0]["name"] == "Project 0"
        assert response["data"]["projects"][2]["budget_spent"] == 30.0
    
    def test_track_generation_cost(self, alice_interface):
        """Test tracking generation cost."""
        # Mock generation
        mock_generation = MagicMock()
        mock_generation.id = "gen-123"
        mock_generation.cost = 0.04
        
        # Mock stats
        mock_stats = {
            "status": "active",
            "budget": {"remaining": 95.96}
        }
        
        alice_interface.project_service.track_generation.return_value = mock_generation
        alice_interface.project_service.get_project_stats.return_value = mock_stats
        
        response = alice_interface.track_generation_cost(
            project_id="proj-123",
            provider="openai",
            model="dall-e-3",
            cost=0.04,
            prompt="A cyberpunk city",
            result_assets=["hash123"]
        )
        
        assert response["success"] is True
        assert response["data"]["generation_id"] == "gen-123"
        assert response["data"]["cost"] == 0.04
        assert response["data"]["budget_remaining"] == 95.96
        assert response["data"]["project_status"] == "active"
    
    def test_track_generation_cost_project_not_found(self, alice_interface):
        """Test tracking cost for non-existent project."""
        alice_interface.project_service.track_generation.side_effect = ValueError("Project not found")
        
        response = alice_interface.track_generation_cost(
            project_id="non-existent",
            provider="openai",
            model="dall-e-3",
            cost=0.04
        )
        
        assert response["success"] is False
        assert response["error"] == "Project not found"
    
    def test_create_project_with_error(self, alice_interface):
        """Test project creation error handling."""
        alice_interface.project_service.create_project.side_effect = Exception("Database error")
        
        response = alice_interface.create_project(name="Test Project")
        
        assert response["success"] is False
        assert "suggestions" in response["data"]  # AI-friendly error