"""Tests for advanced image understanding features."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alicemultiverse.understanding import (
    AdvancedTagger,
    BatchAnalyzer,
    BatchAnalysisRequest,
    CustomInstructionManager,
    InstructionTemplate,
    ProviderOptimizer,
    TagVocabulary,
)
from alicemultiverse.understanding.base import ImageAnalysisResult


class TestTagVocabulary:
    """Test the tag vocabulary system."""
    
    def test_initialization(self):
        """Test vocabulary initialization with default hierarchies."""
        vocab = TagVocabulary()
        
        # Check that default hierarchies are loaded
        assert "animal" in vocab.hierarchies
        assert "mood" in vocab.hierarchies
        assert "composition" in vocab.hierarchies
        assert "style" in vocab.hierarchies
        assert "technical" in vocab.hierarchies
        
        # Check some specific relationships
        animal_hierarchy = vocab.hierarchies["animal"]
        assert "dog" in animal_hierarchy
        assert animal_hierarchy["dog"].parent == "mammal"
        assert "golden_retriever" in animal_hierarchy["dog"].children
    
    def test_get_ancestors(self):
        """Test getting ancestors in hierarchy."""
        vocab = TagVocabulary()
        
        # Test animal hierarchy
        ancestors = vocab.get_ancestors("animal", "golden_retriever")
        assert "dog" in ancestors
        assert "mammal" in ancestors
        assert "animal" in ancestors
        
        # Test with tag that has no parent
        ancestors = vocab.get_ancestors("animal", "animal")
        assert ancestors == []
        
        # Test with non-existent tag
        ancestors = vocab.get_ancestors("animal", "nonexistent")
        assert ancestors == []
    
    def test_get_descendants(self):
        """Test getting descendants in hierarchy."""
        vocab = TagVocabulary()
        
        # Test getting descendants of animal
        descendants = vocab.get_descendants("animal", "mammal")
        assert "dog" in descendants
        assert "cat" in descendants
        assert "horse" in descendants
        
        # Test getting descendants of dog
        descendants = vocab.get_descendants("animal", "dog")
        assert "golden_retriever" in descendants
        assert "labrador" in descendants
        assert "german_shepherd" in descendants
    
    def test_expand_tag(self):
        """Test tag expansion with ancestors and descendants."""
        vocab = TagVocabulary()
        
        # Test expanding with ancestors only
        expanded = vocab.expand_tag("animal", "golden_retriever", include_ancestors=True, include_descendants=False)
        assert "golden_retriever" in expanded
        assert "dog" in expanded
        assert "mammal" in expanded
        assert "animal" in expanded
        
        # Test expanding with descendants only
        expanded = vocab.expand_tag("animal", "mammal", include_ancestors=False, include_descendants=True)
        assert "mammal" in expanded
        assert "dog" in expanded
        assert "cat" in expanded
        assert "horse" in expanded
        assert "golden_retriever" in expanded


class TestAdvancedTagger:
    """Test the advanced tagging system."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        repo = MagicMock()
        session = MagicMock()
        repo.get_session.return_value.__enter__.return_value = session
        repo.get_session.return_value.__exit__.return_value = None
        return repo
    
    @pytest.fixture
    def advanced_tagger(self, mock_repository):
        """Create an advanced tagger instance."""
        return AdvancedTagger(mock_repository)
    
    def test_expand_tags(self, advanced_tagger):
        """Test tag expansion with hierarchical relationships."""
        # Create a mock analysis result
        result = ImageAnalysisResult(
            description="A golden retriever dog",
            tags={
                "animal": ["golden_retriever"],
                "mood": ["happy"]
            }
        )
        
        # Expand tags
        expanded = advanced_tagger.expand_tags(result)
        
        # Check that ancestors are added
        assert "dog" in expanded["animal"]
        assert "mammal" in expanded["animal"]
        assert "animal" in expanded["animal"]
        assert "golden_retriever" in expanded["animal"]
        
        # Check mood expansion
        assert "positive" in expanded["mood"]
        assert "emotional" in expanded["mood"]
    
    def test_add_specialized_categories(self, advanced_tagger):
        """Test adding specialized tag categories."""
        # Create a mock analysis result
        result = ImageAnalysisResult(
            description="A dramatic, mysterious portrait with soft lighting",
            tags={"style": ["portrait"]}
        )
        
        # Create a temporary image path
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            image_path = Path(tmp.name)
            
            # Add specialized categories
            specialized = advanced_tagger.add_specialized_categories(result, image_path)
            
            # Check that mood was extracted from description
            assert "dramatic" in result.tags.get("mood", [])
            assert "mysterious" in result.tags.get("mood", [])


class TestCustomInstructionManager:
    """Test the custom instruction management system."""
    
    @pytest.fixture
    def instruction_manager(self):
        """Create an instruction manager with in-memory database."""
        return CustomInstructionManager()  # Uses in-memory DB by default
    
    def test_initialization(self, instruction_manager):
        """Test that default templates are loaded."""
        templates = instruction_manager.list_templates()
        template_ids = [t.id for t in templates]
        
        assert "fashion_detailed" in template_ids
        assert "product_photography" in template_ids
        assert "artistic_style" in template_ids
        assert "content_moderation" in template_ids
        assert "character_consistency" in template_ids
    
    def test_template_rendering(self, instruction_manager):
        """Test template variable rendering."""
        template = instruction_manager.get_template("fashion_detailed")
        assert template is not None
        
        # Render with variables
        rendered = template.render(additional_focus="Focus on vintage styling")
        assert "Focus on vintage styling" in rendered
    
    def test_project_instructions(self, instruction_manager):
        """Test project-specific instructions."""
        project_id = "test_project"
        
        # Set project instructions
        instructions = {
            "general": "Analyze this image for fashion elements",
            "product": "Focus on product details and quality"
        }
        templates = ["fashion_detailed"]
        variables = {"additional_focus": "Vintage styling elements"}
        
        instruction_manager.set_project_instructions(
            project_id, instructions, templates, variables
        )
        
        # Retrieve and verify
        project_inst = instruction_manager.get_project_instructions(project_id)
        assert project_inst is not None
        assert project_inst.instructions["general"] == instructions["general"]
        assert "fashion_detailed" in project_inst.templates
        
        # Build complete instructions
        built = instruction_manager.build_analysis_instructions(project_id, "general")
        assert instructions["general"] in built
        assert "Fashion Photography Analysis" in built  # Template name
    
    def test_template_creation(self, instruction_manager):
        """Test creating custom templates."""
        template = InstructionTemplate(
            id="test_template",
            name="Test Template",
            description="A test template",
            instructions="Test instruction with {variable}",
            variables={"variable": "Test variable"}
        )
        
        instruction_manager.create_template(template)
        
        # Verify it was created
        retrieved = instruction_manager.get_template("test_template")
        assert retrieved is not None
        assert retrieved.name == "Test Template"
        assert retrieved.variables["variable"] == "Test variable"


class TestBatchAnalyzer:
    """Test the batch analysis system."""
    
    @pytest.fixture
    def mock_analyzer(self):
        """Create a mock image analyzer."""
        analyzer = MagicMock()
        analyzer.get_available_providers.return_value = ["test_provider"]
        analyzer.analyzers = {
            "test_provider": MagicMock()
        }
        analyzer.analyzers["test_provider"].estimate_cost.return_value = 0.01
        return analyzer
    
    @pytest.fixture
    def batch_analyzer(self, mock_analyzer):
        """Create a batch analyzer instance."""
        return BatchAnalyzer(mock_analyzer)
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, batch_analyzer, mock_analyzer):
        """Test batch cost estimation."""
        # Create test images
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            image_paths = []
            for i in range(3):
                img_path = test_dir / f"test_{i}.jpg"
                img_path.touch()
                image_paths.append(img_path)
            
            # Create batch request
            request = BatchAnalysisRequest(
                image_paths=image_paths,
                provider="test_provider"
            )
            
            # Estimate cost
            cost, details = await batch_analyzer.estimate_cost(request)
            
            # Should be 3 images * $0.01 = $0.03
            assert cost == 0.03
            assert details["image_count"] == 3
            assert details["selected_provider"] == "test_provider"
    
    def test_batch_request_validation(self):
        """Test batch request validation."""
        # Valid request
        request = BatchAnalysisRequest(image_paths=[Path("test.jpg")])
        request.validate()  # Should not raise
        
        # Invalid request - no input specified
        request = BatchAnalysisRequest()
        with pytest.raises(ValueError, match="Must specify either"):
            request.validate()
        
        # Invalid concurrent limit
        request = BatchAnalysisRequest(
            image_paths=[Path("test.jpg")],
            max_concurrent=0
        )
        with pytest.raises(ValueError, match="max_concurrent must be at least 1"):
            request.validate()


class TestProviderOptimizer:
    """Test the provider optimization system."""
    
    @pytest.fixture
    def mock_analyzer(self):
        """Create a mock image analyzer."""
        analyzer = MagicMock()
        analyzer.get_available_providers.return_value = ["cheap_provider", "expensive_provider"]
        analyzer.analyzers = {
            "cheap_provider": MagicMock(),
            "expensive_provider": MagicMock()
        }
        analyzer.analyzers["cheap_provider"].estimate_cost.return_value = 0.001
        analyzer.analyzers["expensive_provider"].estimate_cost.return_value = 0.01
        return analyzer
    
    @pytest.fixture
    def optimizer(self, mock_analyzer):
        """Create a provider optimizer instance."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics_file = Path(tmp.name)
        return ProviderOptimizer(mock_analyzer, metrics_file)
    
    def test_budget_management(self, optimizer):
        """Test budget management functionality."""
        # Set budget
        optimizer.set_budget(10.0, daily_budget=2.0)
        
        assert optimizer.budget_manager.total_budget == 10.0
        assert optimizer.budget_manager.daily_budget == 2.0
        assert optimizer.budget_manager.available == 10.0
        
        # Test reservation and commitment
        assert optimizer.budget_manager.reserve(1.0) is True
        assert optimizer.budget_manager.available == 9.0
        
        optimizer.budget_manager.commit(1.0, 0.8)
        assert optimizer.budget_manager.spent == 0.8
        assert optimizer.budget_manager.reserved == 0.0
        assert optimizer.budget_manager.available == 9.2
    
    def test_provider_selection(self, optimizer):
        """Test optimal provider selection."""
        # Test cost-based selection
        provider = optimizer.select_optimal_provider(
            optimization_criteria="cost",
            detailed=False
        )
        assert provider == "cheap_provider"
        
        # Test with budget limit
        provider = optimizer.select_optimal_provider(
            optimization_criteria="cost",
            budget_limit=0.005,
            detailed=False
        )
        assert provider == "cheap_provider"
        
        # Test with very low budget
        provider = optimizer.select_optimal_provider(
            optimization_criteria="cost",
            budget_limit=0.0005,
            detailed=False
        )
        assert provider is None
    
    def test_metrics_tracking(self, optimizer):
        """Test provider metrics tracking."""
        provider = "test_provider"
        
        # Initialize metrics for the test provider
        from alicemultiverse.understanding.provider_optimizer import ProviderMetrics
        optimizer.metrics[provider] = ProviderMetrics(provider_name=provider)
        
        # Record a successful request
        optimizer.metrics[provider].record_success(
            cost=0.01,
            quality_score=0.8,
            response_time=1.5
        )
        
        metrics = optimizer.metrics[provider]
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.total_cost == 0.01
        assert metrics.average_quality == 0.8
        assert metrics.success_rate == 100.0
        
        # Record a failure
        optimizer.metrics[provider].record_failure("API Error")
        
        assert metrics.total_requests == 2
        assert metrics.failed_requests == 1
        assert metrics.success_rate == 50.0
        assert len(metrics.recent_failures) == 1
    
    @pytest.mark.asyncio
    async def test_analyze_with_optimization(self, optimizer, mock_analyzer):
        """Test optimized analysis with failover."""
        # Mock successful analysis
        mock_result = ImageAnalysisResult(
            description="Test image",
            cost=0.001,
            provider="cheap_provider"
        )
        
        mock_analyzer.analyze = AsyncMock(return_value=mock_result)
        
        # Create test image
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            image_path = Path(tmp.name)
            
            # Analyze with optimization
            result = await optimizer.analyze_with_optimization(image_path)
            
            assert result is not None
            assert result.provider == "cheap_provider"
            assert result.cost == 0.001
            
            # Check that metrics were updated
            assert optimizer.metrics["cheap_provider"].total_requests == 1
            assert optimizer.metrics["cheap_provider"].successful_requests == 1


@pytest.mark.integration
class TestIntegration:
    """Integration tests for advanced understanding features."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_advanced_understanding(self):
        """Test the complete advanced understanding workflow."""
        # This would require actual API keys and images
        # Skipping for now, but structure shows how integration tests would work
        pytest.skip("Integration test requires API keys and test images")
        
        # Example of what the test would do:
        # 1. Create test images
        # 2. Initialize all components (tagger, instruction manager, optimizer)
        # 3. Set up project with custom instructions
        # 4. Run batch analysis
        # 5. Verify hierarchical tags, custom vocabulary, and cost optimization
        # 6. Check database storage
        pass


if __name__ == "__main__":
    pytest.main([__file__])