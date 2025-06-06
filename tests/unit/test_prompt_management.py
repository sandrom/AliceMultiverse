"""Tests for the prompt management system."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import json
import yaml

from alicemultiverse.prompts import (
    Prompt, PromptService, ProjectPromptStorage,
    PromptCategory, ProviderType, PromptUsage
)
from alicemultiverse.prompts.integration import PromptProviderIntegration
from alicemultiverse.providers.types import GenerationResult


class TestPromptModels:
    """Test prompt data models."""
    
    def test_prompt_creation(self):
        """Test creating a prompt."""
        prompt = Prompt(
            id="test-001",
            text="A beautiful sunset over mountains",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY, ProviderType.FLUX],
            tags=["landscape", "nature"],
            project="TestProject",
            style="photorealistic"
        )
        
        assert prompt.id == "test-001"
        assert prompt.text == "A beautiful sunset over mountains"
        assert prompt.category == PromptCategory.IMAGE_GENERATION
        assert len(prompt.providers) == 2
        assert "landscape" in prompt.tags
        
    def test_prompt_success_rate(self):
        """Test calculating success rate."""
        prompt = Prompt(
            id="test-002",
            text="Test prompt",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY],
            use_count=10,
            success_count=8
        )
        
        assert prompt.success_rate() == 0.8
        
        # Test with no uses
        prompt.use_count = 0
        assert prompt.success_rate() == 0.0


class TestPromptService:
    """Test prompt service operations."""
    
    @pytest.fixture
    def service(self, tmp_path):
        """Create a service with temporary database."""
        db_path = tmp_path / "test_prompts.duckdb"
        return PromptService(db_path)
    
    def test_create_and_get_prompt(self, service):
        """Test creating and retrieving a prompt."""
        prompt = service.create_prompt(
            text="Test prompt for unit test",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY],
            tags=["test", "unit"],
            project="TestProject"
        )
        
        assert prompt.id is not None
        
        # Retrieve prompt
        retrieved = service.get_prompt(prompt.id)
        assert retrieved is not None
        assert retrieved.text == "Test prompt for unit test"
        assert retrieved.project == "TestProject"
    
    def test_search_prompts(self, service):
        """Test searching for prompts."""
        # Create test prompts
        prompt1 = service.create_prompt(
            text="Cyberpunk city at night",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY],
            tags=["cyberpunk", "city"],
            style="cyberpunk"
        )
        
        prompt2 = service.create_prompt(
            text="Medieval castle in fog",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.FLUX],
            tags=["medieval", "castle"],
            style="fantasy"
        )
        
        # Search by text
        results = service.search_prompts(query="cyberpunk")
        assert len(results) == 1
        assert results[0].id == prompt1.id
        
        # Search by tag
        results = service.search_prompts(tags=["castle"])
        assert len(results) == 1
        assert results[0].id == prompt2.id
        
        # Search by style
        results = service.search_prompts(style="cyberpunk")
        assert len(results) == 1
        assert results[0].id == prompt1.id
    
    def test_record_usage(self, service):
        """Test recording prompt usage."""
        prompt = service.create_prompt(
            text="Test prompt",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY]
        )
        
        # Record successful usage
        usage = service.record_usage(
            prompt_id=prompt.id,
            provider=ProviderType.MIDJOURNEY,
            success=True,
            cost=0.10,
            duration_seconds=15.5
        )
        
        assert usage.id is not None
        assert usage.success is True
        assert usage.cost == 0.10
        
        # Check that prompt stats were updated
        updated_prompt = service.get_prompt(prompt.id)
        assert updated_prompt.use_count == 1
        assert updated_prompt.success_count == 1
        assert updated_prompt.success_rate() == 1.0
    
    def test_get_effective_prompts(self, service):
        """Test finding effective prompts."""
        # Create prompts with different success rates
        prompt1 = service.create_prompt(
            text="High success prompt",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY]
        )
        
        prompt2 = service.create_prompt(
            text="Low success prompt",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY]
        )
        
        # Record usage
        for _ in range(10):
            service.record_usage(prompt1.id, ProviderType.MIDJOURNEY, success=True)
        
        for i in range(10):
            service.record_usage(prompt2.id, ProviderType.MIDJOURNEY, success=(i < 3))
        
        # Get effective prompts
        effective = service.get_effective_prompts(
            min_success_rate=0.8,
            min_uses=5
        )
        
        assert len(effective) == 1
        assert effective[0].id == prompt1.id
    
    def test_export_import_prompts(self, service, tmp_path):
        """Test exporting and importing prompts."""
        # Create test prompts
        prompt1 = service.create_prompt(
            text="Export test 1",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY],
            tags=["export", "test"]
        )
        
        prompt2 = service.create_prompt(
            text="Export test 2",
            category=PromptCategory.VIDEO_GENERATION,
            providers=[ProviderType.RUNWAY],
            tags=["export", "test"]
        )
        
        # Export
        export_path = tmp_path / "export.json"
        service.export_prompts(export_path)
        
        assert export_path.exists()
        
        # Create new service and import
        new_service = PromptService(tmp_path / "new_prompts.duckdb")
        count = new_service.import_prompts(export_path)
        
        assert count == 2
        
        # Verify imported prompts
        imported = new_service.search_prompts(tags=["export"])
        assert len(imported) == 2


class TestProjectPromptStorage:
    """Test project-based prompt storage."""
    
    @pytest.fixture
    def storage(self):
        """Create storage instance."""
        return ProjectPromptStorage(format="yaml")
    
    @pytest.fixture
    def project_path(self, tmp_path):
        """Create temporary project directory."""
        project = tmp_path / "TestProject"
        project.mkdir()
        return project
    
    def test_save_to_project(self, storage, project_path):
        """Test saving prompt to project."""
        prompt = Prompt(
            id="proj-001",
            text="Project prompt test",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY],
            tags=["project", "test"],
            project="TestProject"
        )
        
        saved_path = storage.save_to_project(prompt, project_path)
        
        assert saved_path.exists()
        assert saved_path.suffix == ".yaml"
        
        # Check main prompts file
        prompts_file = project_path / ".alice/prompts/prompts.yaml"
        assert prompts_file.exists()
        
        with open(prompts_file) as f:
            data = yaml.safe_load(f)
        
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["id"] == "proj-001"
    
    def test_load_from_project(self, storage, project_path):
        """Test loading prompts from project."""
        # Create test prompt
        prompt = Prompt(
            id="proj-002",
            text="Load test prompt",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.FLUX],
            tags=["load", "test"]
        )
        
        storage.save_to_project(prompt, project_path)
        
        # Load prompts
        loaded = storage.load_from_project(project_path)
        
        assert len(loaded) == 1
        assert loaded[0].id == "proj-002"
        assert loaded[0].text == "Load test prompt"
    
    def test_initialize_project(self, storage, project_path):
        """Test initializing project prompt storage."""
        storage.initialize_project_prompts(project_path)
        
        # Check created structure
        prompts_dir = project_path / ".alice/prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "README.md").exists()
        assert (prompts_dir / "templates/example.yaml").exists()
        assert (prompts_dir / "exports").exists()
    
    def test_sync_operations(self, storage, project_path):
        """Test syncing between project and index."""
        # Create prompt in project
        prompt = Prompt(
            id="sync-001",
            text="Sync test prompt",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY],
            project="TestProject"
        )
        
        storage.save_to_project(prompt, project_path)
        
        # Sync to index
        synced = storage.sync_project_to_index(project_path)
        assert synced == 1
        
        # Verify in index
        found = storage.service.get_prompt("sync-001")
        assert found is not None
        assert found.text == "Sync test prompt"


class TestPromptIntegration:
    """Test prompt provider integration."""
    
    @pytest.fixture
    def integration(self, tmp_path):
        """Create integration instance."""
        service = PromptService(tmp_path / "test_prompts.duckdb")
        return PromptProviderIntegration(service)
    
    def test_track_generation(self, integration):
        """Test tracking generation with prompt."""
        result = GenerationResult(
            success=True,
            file_path=Path("/tmp/test.png"),
            asset_id="asset-123",
            generation_id="gen-456",
            cost=0.05,
            metadata={
                "prompt": "Test generation prompt",
                "model": "test-v1"
            }
        )
        
        prompt_id = integration.track_generation(
            provider="midjourney",
            prompt_text="Test generation prompt",
            result=result,
            cost=0.05,
            duration=10.5,
            project="TestProject"
        )
        
        assert prompt_id is not None
        
        # Verify prompt was created
        prompt = integration.service.get_prompt(prompt_id)
        assert prompt is not None
        assert prompt.text == "Test generation prompt"
        assert prompt.use_count == 1
        assert prompt.success_count == 1
    
    def test_extract_prompt_from_metadata(self, integration):
        """Test extracting prompt from various metadata formats."""
        # Test different metadata structures
        test_cases = [
            ({"prompt": "Direct prompt"}, "Direct prompt"),
            ({"text": "Text field prompt"}, "Text field prompt"),
            ({"input": "Input field prompt"}, "Input field prompt"),
            ({"prompt": {"text": "Nested prompt"}}, "Nested prompt"),
            ({}, None)
        ]
        
        for metadata, expected in test_cases:
            result = integration.extract_prompt_from_metadata(metadata)
            assert result == expected
    
    def test_provider_mapping(self, integration):
        """Test mapping provider names to enums."""
        mappings = [
            ("midjourney", ProviderType.MIDJOURNEY),
            ("MidJourney", ProviderType.MIDJOURNEY),
            ("dalle", ProviderType.DALLE),
            ("openai", ProviderType.OPENAI),
            ("claude", ProviderType.ANTHROPIC),
            ("unknown_provider", ProviderType.OTHER)
        ]
        
        for name, expected in mappings:
            result = integration.map_provider_to_enum(name)
            assert result == expected
    
    def test_find_prompts_for_project(self, integration):
        """Test finding and analyzing project prompts."""
        # Create test prompts
        for i in range(3):
            prompt = integration.service.create_prompt(
                text=f"Project prompt {i}",
                category=PromptCategory.IMAGE_GENERATION,
                providers=[ProviderType.MIDJOURNEY],
                project="TestProject"
            )
            
            # Record some usage
            for j in range(i + 1):
                integration.service.record_usage(
                    prompt_id=prompt.id,
                    provider=ProviderType.MIDJOURNEY,
                    success=True,
                    cost=0.10
                )
        
        # Get project data
        data = integration.find_prompts_for_project("TestProject")
        
        assert len(data["prompts"]) == 3
        assert data["statistics"]["total_prompts"] == 3
        assert data["statistics"]["total_uses"] == 6  # 1 + 2 + 3
        assert data["statistics"]["total_cost"] == 0.60  # 6 * 0.10


class TestPromptYAMLFormat:
    """Test YAML formatting functionality."""
    
    def test_yaml_format_readability(self, tmp_path):
        """Test that YAML format is human-readable."""
        from alicemultiverse.prompts.yaml_format import PromptYAMLFormatter
        
        prompt = Prompt(
            id="yaml-001",
            text="A beautiful landscape",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY],
            tags=["landscape", "nature"],
            description="Creates scenic landscapes",
            effectiveness_rating=8.5,
            use_count=10,
            success_count=9
        )
        
        yaml_file = tmp_path / "test_prompt.yaml"
        PromptYAMLFormatter.save_readable_prompt(prompt, yaml_file)
        
        # Read and verify
        with open(yaml_file) as f:
            content = f.read()
        
        # Check that important fields are at the top
        lines = content.strip().split('\n')
        assert lines[0].startswith('prompt:')
        assert 'category:' in content
        assert 'effectiveness:' in content
        assert 'success_rate: "90.0%"' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])