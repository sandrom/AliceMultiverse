"""Integration tests for the timeline flow analyzer with vision provider."""

import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from alicemultiverse.workflows.composition.flow_analyzer import FlowAnalyzer, FlowIssueType
from alicemultiverse.workflows.video_export import Timeline, TimelineClip
from alicemultiverse.understanding.base import ImageAnalysisResult


class TestFlowAnalyzerIntegration:
    """Test flow analyzer with vision provider integration."""
    
    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline for testing."""
        return Timeline(
            duration=30.0,
            clips=[
                TimelineClip(
                    asset_path=Path("/images/fast_action.jpg"),
                    start_time=0.0,
                    duration=2.0,
                    clip_type="image"
                ),
                TimelineClip(
                    asset_path=Path("/images/slow_peaceful.jpg"),
                    start_time=2.0,
                    duration=8.0,  # Long peaceful shot
                    clip_type="image"
                ),
                TimelineClip(
                    asset_path=Path("/images/fast_action2.jpg"),
                    start_time=10.0,
                    duration=1.5,
                    clip_type="image"
                ),
                TimelineClip(
                    asset_path=Path("/images/fast_action3.jpg"),
                    start_time=11.5,
                    duration=1.5,
                    clip_type="image"
                ),
            ]
        )
    
    @pytest.fixture
    def mock_metadata_cache(self):
        """Mock metadata cache with test data."""
        cache = Mock()
        cache.get_metadata.side_effect = lambda path: {
            "/images/fast_action.jpg": {
                "tags": {"mood": ["energetic", "dynamic"], "style": ["action"]},
                "dominant_colors": ["#FF0000", "#FF6600"],
                "brightness": 0.8
            },
            "/images/slow_peaceful.jpg": {
                "tags": {"mood": ["calm", "peaceful"], "style": ["landscape"]},
                "dominant_colors": ["#0066CC", "#00AAFF"],
                "brightness": 0.5
            },
            "/images/fast_action2.jpg": {
                "tags": {"mood": ["energetic"], "style": ["action"]},
                "dominant_colors": ["#FF0000", "#FFAA00"],
                "brightness": 0.9
            },
            "/images/fast_action3.jpg": {
                "tags": {"mood": ["energetic", "intense"], "style": ["action"]},
                "dominant_colors": ["#FF0000", "#FF3300"],
                "brightness": 0.85
            },
        }.get(str(path), {})
        return cache
    
    @pytest.mark.asyncio
    async def test_basic_flow_analysis(self, sample_timeline, mock_metadata_cache):
        """Test basic timeline flow analysis without vision provider."""
        analyzer = FlowAnalyzer(metadata_cache=mock_metadata_cache)
        
        issues, suggestions = await analyzer.analyze_timeline_flow(sample_timeline)
        
        # Should detect pacing issues
        pacing_issues = [i for i in issues if i.issue_type in [
            FlowIssueType.PACING_TOO_SLOW,
            FlowIssueType.PACING_TOO_FAST,
            FlowIssueType.INCONSISTENT_RHYTHM
        ]]
        assert len(pacing_issues) > 0
        
        # Should detect the jarring mood transition
        mood_issues = [i for i in issues if i.issue_type == FlowIssueType.JARRING_TRANSITION]
        assert len(mood_issues) > 0  # Peaceful to energetic transition
        
        # Should have suggestions
        assert len(suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_vision_provider_integration(self, sample_timeline, mock_metadata_cache):
        """Test flow analysis with vision provider."""
        # Mock the ImageAnalyzer
        with patch('alicemultiverse.workflows.composition.flow_analyzer.ImageAnalyzer') as MockAnalyzer:
            mock_analyzer = Mock()
            MockAnalyzer.return_value = mock_analyzer
            
            # Mock available providers
            mock_analyzer.get_available_providers.return_value = ["test_provider"]
            
            # Mock analysis results
            async def mock_analyze(path, **kwargs):
                if "fast_action" in str(path):
                    return ImageAnalysisResult(
                        description="Fast action scene with high motion. motion=0.9, complexity=0.8, energy=0.9",
                        provider="test_provider",
                        model="test-model",
                        cost=0.001
                    )
                else:
                    return ImageAnalysisResult(
                        description="Peaceful landscape with low motion. motion=0.1, complexity=0.3, energy=0.2",
                        provider="test_provider", 
                        model="test-model",
                        cost=0.001
                    )
            
            mock_analyzer.analyze.side_effect = mock_analyze
            
            # Create analyzer with vision provider
            analyzer = FlowAnalyzer(
                metadata_cache=mock_metadata_cache,
                vision_provider="test_provider"
            )
            
            issues, suggestions = await analyzer.analyze_timeline_flow(sample_timeline)
            
            # Should have called vision analysis
            assert mock_analyzer.analyze.called
            
            # Should detect energy spikes/drops with vision data
            energy_issues = [i for i in issues if i.issue_type in [
                FlowIssueType.ENERGY_DROP,
                FlowIssueType.ENERGY_SPIKE
            ]]
            assert len(energy_issues) > 0
    
    @pytest.mark.asyncio
    async def test_target_energy_curve(self, sample_timeline, mock_metadata_cache):
        """Test analysis with target energy curve."""
        analyzer = FlowAnalyzer(metadata_cache=mock_metadata_cache)
        
        # Analyze with "build" energy curve
        issues, suggestions = await analyzer.analyze_timeline_flow(
            sample_timeline,
            target_energy="build"
        )
        
        # Should detect that peaceful shot doesn't fit build curve
        energy_issues = [i for i in issues if "energy" in str(i.issue_type).lower()]
        assert len(energy_issues) > 0
        
        # Should suggest reordering or adjusting timing
        timing_suggestions = [s for s in suggestions if "timing" in str(s.suggestion_type).lower()]
        assert len(timing_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_color_continuity(self, sample_timeline, mock_metadata_cache):
        """Test color continuity analysis."""
        analyzer = FlowAnalyzer(metadata_cache=mock_metadata_cache)
        
        issues, suggestions = await analyzer.analyze_timeline_flow(sample_timeline)
        
        # Should detect color discontinuity (red to blue)
        color_issues = [i for i in issues if i.issue_type == FlowIssueType.COLOR_DISCONTINUITY]
        assert len(color_issues) > 0
        
        # The issue should be between clips 0 and 1
        assert any(i.clip_indices == [0, 1] for i in color_issues)
    
    @pytest.mark.asyncio
    async def test_repetitive_sequence_detection(self):
        """Test detection of repetitive sequences."""
        # Create timeline with repetitive clips
        repetitive_timeline = Timeline(
            duration=10.0,
            clips=[
                TimelineClip(
                    asset_path=Path("/images/same.jpg"),
                    start_time=0.0,
                    duration=2.0,
                    clip_type="image"
                ),
                TimelineClip(
                    asset_path=Path("/images/same.jpg"),  # Same asset
                    start_time=2.0,
                    duration=2.0,
                    clip_type="image"
                ),
                TimelineClip(
                    asset_path=Path("/images/different.jpg"),
                    start_time=4.0,
                    duration=2.0,
                    clip_type="image"
                ),
            ]
        )
        
        cache = Mock()
        cache.get_metadata.return_value = {"tags": {}}
        
        analyzer = FlowAnalyzer(metadata_cache=cache)
        issues, suggestions = await analyzer.analyze_timeline_flow(repetitive_timeline)
        
        # Should detect repetitive sequence
        repetitive_issues = [i for i in issues if i.issue_type == FlowIssueType.REPETITIVE_SEQUENCE]
        assert len(repetitive_issues) > 0
    
    @pytest.mark.asyncio
    async def test_narrative_structure(self, sample_timeline, mock_metadata_cache):
        """Test narrative structure analysis."""
        analyzer = FlowAnalyzer(metadata_cache=mock_metadata_cache)
        
        issues, suggestions = await analyzer.analyze_timeline_flow(
            sample_timeline,
            target_mood="dramatic"
        )
        
        # Should detect narrative issues
        narrative_issues = [i for i in issues if i.issue_type in [
            FlowIssueType.MISSING_CLIMAX,
            FlowIssueType.NARRATIVE_BREAK
        ]]
        
        # A dramatic timeline should have climax
        assert any(i.issue_type == FlowIssueType.MISSING_CLIMAX for i in issues)
    
    def test_clip_analysis_caching(self, mock_metadata_cache):
        """Test that clip analyses are cached."""
        analyzer = FlowAnalyzer(metadata_cache=mock_metadata_cache)
        
        # Analyze same clip twice
        clip = TimelineClip(
            asset_path=Path("/images/test.jpg"),
            start_time=0.0,
            duration=2.0,
            clip_type="image"
        )
        
        # Run synchronously for testing
        loop = asyncio.new_event_loop()
        analysis1 = loop.run_until_complete(analyzer._analyze_clip(clip, 0))
        analysis2 = loop.run_until_complete(analyzer._analyze_clip(clip, 0))
        
        # Should return cached result
        assert str(clip.asset_path) in analyzer.clip_analyses
        assert analysis1 == analysis2
        
        # Cache should have called metadata only once
        assert mock_metadata_cache.get_metadata.call_count == 1