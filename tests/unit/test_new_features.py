"""Smoke tests for recently implemented features.

These tests ensure basic functionality works without errors.
They don't test deep functionality but verify imports and basic operations.
"""

from pathlib import Path

import pytest


# TestBatchOptimization removed - OptimizedBatchAnalyzer module was deleted


class TestOllamaIntegration:
    """Test Ollama local vision model integration."""

    def test_import_and_instantiate(self):
        """Test that OllamaImageAnalyzer can be imported and instantiated."""
        from alicemultiverse.understanding.ollama_provider import OllamaImageAnalyzer

        analyzer = OllamaImageAnalyzer()
        assert analyzer is not None
        assert analyzer.base_url == "http://localhost:11434"

    def test_model_configuration(self):
        """Test Ollama model configuration."""
        from alicemultiverse.understanding.ollama_provider import OllamaImageAnalyzer

        custom_analyzer = OllamaImageAnalyzer(
            model="llama-vision:custom",
            base_url="http://custom:11434"
        )
        assert custom_analyzer.model == "llama-vision:custom"
        assert custom_analyzer.base_url == "http://custom:11434"


# TestTagHierarchies removed - tag_hierarchy module was deleted
# TestStyleAnalysis removed - style_analyzer and style_clustering modules were deleted


class TestQuickSelection:
    """Test quick selection storage."""

    def test_import_and_instantiate(self):
        """Test that quick selection components can be imported."""
        from alicemultiverse.comparison.quick_selection import (
            QuickSelectionStorage,
            SelectionBatch,
            SelectionStats,
        )

        storage = QuickSelectionStorage()
        assert storage is not None

        batch = SelectionBatch(batch_id="test123")
        assert batch.batch_id == "test123"
        assert batch.images == []

        stats = SelectionStats()
        assert stats.total_comparisons == 0


class TestMusicAnalyzer:
    """Test music generation and analysis capabilities."""

    def test_import_music_module(self):
        """Test that music module components can be imported."""
        import alicemultiverse.music as music_module

        # Test data structures
        params = music_module.MusicGenerationParams()
        assert params.duration == 30.0
        assert params.tempo == 120.0

        beat_info = music_module.BeatInfo()
        assert beat_info.tempo == 120.0
        assert beat_info.time_signature == (4, 4)

        mood = music_module.MusicMood()
        assert mood.energy == 0.5
        assert mood.get_mood_category() == "neutral"

        # Test analyzer instantiation
        analyzer = music_module.MusicAnalyzer()
        assert analyzer is not None


# TestEnhancedAnalyzer removed - enhanced_analyzer module was deleted
# TestTaxonomyManager removed - taxonomy_manager module was deleted