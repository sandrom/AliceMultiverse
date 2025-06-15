"""Smoke tests for recently implemented features.

These tests ensure basic functionality works without errors.
They don't test deep functionality but verify imports and basic operations.
"""

from pathlib import Path

import pytest


class TestBatchOptimization:
    """Test batch analysis optimization with similarity detection."""

    def test_import_and_instantiate(self):
        """Test that OptimizedBatchAnalyzer can be imported and instantiated."""
        from alicemultiverse.understanding.analyzer import ImageAnalyzer
        from alicemultiverse.understanding.optimized_batch_analyzer import OptimizedBatchAnalyzer

        analyzer = ImageAnalyzer()
        optimizer = OptimizedBatchAnalyzer(analyzer)

        assert optimizer is not None
        assert optimizer.similarity_threshold == 0.9
        assert optimizer.min_group_size == 2

    def test_image_grouping_structures(self):
        """Test that image grouping data structures work."""
        from alicemultiverse.understanding.optimized_batch_analyzer import (
            ImageGroup,
            OptimizationStats,
        )

        group = ImageGroup(representative=Path("test.jpg"))
        assert group.representative == Path("test.jpg")
        assert len(group.members) == 0

        stats = OptimizationStats()
        assert stats.total_images == 0
        assert stats.cost_saved == 0.0


class TestOllamaIntegration:
    """Test Ollama local vision model integration."""

    def test_import_and_instantiate(self):
        """Test that OllamaImageAnalyzer can be imported and instantiated."""
        from alicemultiverse.understanding.ollama_provider import OllamaImageAnalyzer

        analyzer = OllamaImageAnalyzer()
        assert analyzer is not None
        assert analyzer.model == "llava:latest"
        assert analyzer.base_url == "http://localhost:11434"

    def test_available_models(self):
        """Test that Ollama models are properly defined."""
        from alicemultiverse.understanding.ollama_provider import OllamaImageAnalyzer

        models = OllamaImageAnalyzer.VISION_MODELS
        assert "llava" in models
        assert models["llava"]["name"] == "llava:latest"
        assert "objects" in models["llava"]["capabilities"]

    @pytest.mark.asyncio
    async def test_check_availability(self):
        """Test availability check (will fail if Ollama not running, which is OK)."""
        from alicemultiverse.understanding.ollama_provider import OllamaImageAnalyzer

        analyzer = OllamaImageAnalyzer()
        # This will return False if Ollama isn't running, which is fine for a smoke test
        is_available = await analyzer.check_availability()
        assert isinstance(is_available, bool)


class TestTagHierarchies:
    """Test intelligent tag hierarchy system."""

    def test_import_and_instantiate(self):
        """Test that TagHierarchy can be imported and instantiated."""
        from alicemultiverse.understanding.tag_hierarchy import TagHierarchy, TagNode

        hierarchy = TagHierarchy()
        assert hierarchy is not None
        assert len(hierarchy.nodes) > 0  # Should have default nodes

        # Test TagNode creation
        node = TagNode(name="test_tag")
        assert node.name == "test_tag"
        assert len(node.children) == 0

    def test_default_hierarchy_structure(self):
        """Test that default hierarchy is properly initialized."""
        from alicemultiverse.understanding.tag_hierarchy import TagHierarchy

        hierarchy = TagHierarchy()

        # Check some expected default tags
        assert "art_style" in hierarchy.nodes
        assert "digital_art" in hierarchy.nodes
        assert hierarchy.nodes["digital_art"].parent == "art_style"

    def test_tag_operations(self):
        """Test basic tag operations."""
        from alicemultiverse.understanding.tag_hierarchy import TagHierarchy

        hierarchy = TagHierarchy()

        # Test adding a tag
        hierarchy.add_tag("new_style", parent="art_style", category="style")
        assert "new_style" in hierarchy.nodes
        assert hierarchy.nodes["new_style"].parent == "art_style"

        # Test normalization
        normalized = hierarchy.normalize_tag("b&w")
        assert normalized == "black_and_white"  # Assuming this alias exists


class TestStyleAnalysis:
    """Test style similarity and clustering features."""

    def test_import_and_instantiate(self):
        """Test that StyleAnalyzer can be imported and instantiated."""
        from alicemultiverse.understanding.style_analyzer import StyleAnalyzer

        analyzer = StyleAnalyzer()
        assert analyzer is not None

    def test_style_fingerprint_structure(self):
        """Test style fingerprint data structures."""
        from alicemultiverse.understanding.style_analyzer import (
            ColorPalette,
            CompositionAnalysis,
        )

        # Test ColorPalette
        palette = ColorPalette()
        assert palette.dominant_colors == []
        assert palette.color_percentages == []

        # Test CompositionAnalysis
        comp = CompositionAnalysis()
        assert comp.rule_of_thirds == 0.0
        assert comp.symmetry_score == 0.0

        # StyleFingerprint requires all components to be passed
        # So we'll skip instantiation test here

    def test_style_clustering_import(self):
        """Test that style clustering can be imported."""
        from alicemultiverse.understanding.style_clustering import StyleClusteringSystem

        system = StyleClusteringSystem()
        assert system is not None
        # StyleClusteringSystem doesn't expose min_cluster_size as attribute


class TestQuickSelection:
    """Test quick selection workflow."""

    def test_selection_models_import(self):
        """Test that selection models can be imported."""
        from alicemultiverse.selections.models import Selection, SelectionPurpose, SelectionStatus

        # Test enums
        assert SelectionPurpose.CURATION is not None
        assert SelectionStatus.ACTIVE is not None

        # Test Selection model (uses 'id' not 'selection_id')
        selection = Selection(
            id="test123",
            name="Test Selection",
            purpose=SelectionPurpose.CURATION
        )
        assert selection.id == "test123"

    def test_selection_service_import(self):
        """Test that selection service can be imported."""
        from alicemultiverse.selections.service import SelectionService

        # SelectionService takes optional project_service, not storage_path
        service = SelectionService()
        assert service is not None


class TestMusicAnalyzer:
    """Test music analyzer module."""

    def test_import_music_analyzer_directly(self):
        """Test that music analyzer can be imported directly."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "music_analyzer",
            "alicemultiverse/workflows/music_analyzer.py"
        )
        music_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(music_module)

        # Test data structures
        beat_info = music_module.BeatInfo(tempo=120.0)
        assert beat_info.tempo == 120.0
        assert beat_info.time_signature == (4, 4)

        mood = music_module.MusicMood()
        assert mood.energy == 0.5
        assert mood.get_mood_category() == "neutral"

        # Test analyzer instantiation
        analyzer = music_module.MusicAnalyzer()
        assert analyzer is not None


class TestEnhancedAnalyzer:
    """Test enhanced analyzer integration."""

    def test_import_and_instantiate(self):
        """Test that EnhancedImageAnalyzer can be imported."""
        from alicemultiverse.understanding.enhanced_analyzer import EnhancedImageAnalyzer

        analyzer = EnhancedImageAnalyzer()
        assert analyzer is not None
        assert analyzer.taxonomy is not None
        assert analyzer.analyzer is not None


class TestTaxonomyManager:
    """Test taxonomy manager for custom organization schemes."""

    def test_import_and_instantiate(self):
        """Test that TaxonomyManager can be imported."""
        from alicemultiverse.understanding.taxonomy_manager import TaxonomyManager

        manager = TaxonomyManager()
        assert manager is not None
        assert manager.hierarchy is not None  # It's 'hierarchy' not 'tag_hierarchy'

    def test_mood_board_structure(self):
        """Test mood board data structure."""
        from alicemultiverse.understanding.taxonomy_manager import MoodBoard

        board = MoodBoard(
            id="test123",
            name="Test Mood",
            description="Test mood board"
        )
        assert board.name == "Test Mood"
        assert board.id == "test123"
