"""
Tests for the music video template.
"""

from unittest.mock import patch

import pytest

from alicemultiverse.workflows.base import WorkflowContext
from alicemultiverse.workflows.templates.music_video import (
    CinematicMusicVideoTemplate,
    MusicVideoTemplate,
    QuickMusicVideoTemplate,
)


class TestMusicVideoTemplate:
    """Test music video template functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock workflow context."""
        context = WorkflowContext(initial_prompt="Create a music video")
        context.results = {}  # Initialize results dict

        # Add get_result method
        def get_result(step_name):
            return context.results.get(step_name)
        context.get_result = get_result

        context.initial_params = {
            "music_file": "test_music.mp3",
            "images": ["img1.jpg", "img2.jpg", "img3.jpg"],
            "sync_mode": "beat",
            "transition_style": "auto",
            "export_formats": ["xml"],
            "target_duration": 30,
            "min_shot_duration": 0.5,
            "max_shot_duration": 5.0,
        }
        return context

    @pytest.fixture
    def mock_music_analysis(self):
        """Mock music analysis results."""
        return {
            "success": True,
            "tempo": 120,
            "beats": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
            "downbeats": [0.5, 2.5],
            "sections": [
                {"name": "intro", "start": 0, "end": 5, "energy": 0.3},
                {"name": "verse", "start": 5, "end": 20, "energy": 0.6},
                {"name": "chorus", "start": 20, "end": 30, "energy": 0.9},
            ],
            "mood": "energetic",
            "energy_profile": [
                {"time": 0, "energy": 0.3},
                {"time": 5, "energy": 0.6},
                {"time": 20, "energy": 0.9},
            ],
            "duration": 30,
            "file_path": "test_music.mp3",
        }

    def test_template_creation(self):
        """Test creating music video template."""
        template = MusicVideoTemplate()
        assert template is not None
        assert template.name == "MusicVideo"
        assert template.music_analyzer is not None
        assert template.transition_matcher is not None

    def test_define_steps(self, mock_context):
        """Test workflow step definition."""
        template = MusicVideoTemplate()
        steps = template.define_steps(mock_context)

        # Should have at least: analyze_music, sequence, transitions, timeline, export
        assert len(steps) >= 5

        # Check step names
        step_names = [step.name for step in steps]
        assert "analyze_music" in step_names
        assert "sequence_images" in step_names
        assert "analyze_transitions" in step_names
        assert "create_timeline" in step_names
        assert "export_xml" in step_names

        # Check first step
        first_step = steps[0]
        assert first_step.name == "analyze_music"
        assert first_step.provider == "local"
        assert first_step.operation == "analyze_music"

    def test_validate(self, mock_context):
        """Test workflow validation."""
        template = MusicVideoTemplate()

        # Valid params should pass
        errors = template.validate(mock_context)
        assert len(errors) == 0

        # Missing music file
        mock_context.initial_params.pop("music_file")
        errors = template.validate(mock_context)
        assert "music_file is required" in errors

        # Invalid sync mode
        mock_context.initial_params["music_file"] = "test.mp3"
        mock_context.initial_params["sync_mode"] = "invalid"
        errors = template.validate(mock_context)
        assert any("sync_mode" in e for e in errors)

    def test_estimate_cost(self, mock_context):
        """Test cost estimation."""
        template = MusicVideoTemplate()
        cost = template.estimate_cost(mock_context)

        # All operations are local, so cost should be 0
        assert cost == 0.0

    def test_analyze_music_operation(self, mock_context):
        """Test music analysis operation."""
        template = MusicVideoTemplate()

        # Mock the music analyzer
        with patch.object(template.music_analyzer, 'analyze_audio') as mock_analyzer:
            mock_analyzer.return_value = {
                "tempo": 120,
                "beats": [0.5, 1.0],
                "downbeats": [0.5],
                "sections": [],
                "duration": 30,
            }

            params = {"music_file": "test.mp3"}
            result = template._analyze_music(params)

            assert result["success"] is True
            assert result["tempo"] == 120
            assert len(result["beats"]) == 2

    def test_sequence_images_operation(self, mock_context, mock_music_analysis):
        """Test image sequencing operation."""
        template = MusicVideoTemplate()

        # Mock the context to return music analysis
        mock_context.results = {"analyze_music": mock_music_analysis}

        params = {
            "images": ["img1.jpg", "img2.jpg", "img3.jpg"],
            "music_analysis_from": "analyze_music",
            "energy_matching": True,
            "target_duration": 30,
        }

        result = template._sequence_images(params, mock_context)

        assert result["success"] is True
        assert "sequence" in result
        assert len(result["sequence"]) > 0
        assert "shot_count" in result
        assert "avg_shot_duration" in result

    def test_create_timeline_operation(self, mock_context, mock_music_analysis):
        """Test timeline creation operation."""
        template = MusicVideoTemplate()

        # Mock the context results
        mock_context.results = {
            "analyze_music": mock_music_analysis,
            "sequence_images": {
                "success": True,
                "sequence": ["img1.jpg", "img2.jpg", "img3.jpg"],
                "avg_shot_duration": 2.0,
            },
            "analyze_transitions": {
                "success": True,
                "transitions": [
                    {
                        "source": "img1.jpg",
                        "target": "img2.jpg",
                        "type": "dissolve",
                        "duration": 1.0,
                    },
                    {
                        "source": "img2.jpg",
                        "target": "img3.jpg",
                        "type": "cut",
                        "duration": 0.0,
                    },
                ],
            },
        }

        params = {
            "sequence_from": "sequence_images",
            "transitions_from": "analyze_transitions",
            "music_from": "analyze_music",
            "sync_mode": "beat",
            "min_shot_duration": 0.5,
            "max_shot_duration": 5.0,
        }

        result = template._create_timeline(params, mock_context)

        assert result["success"] is True
        assert "timeline" in result
        assert len(result["timeline"]) > 0

        # Check timeline structure
        clip = result["timeline"][0]
        assert "clip_id" in clip
        assert "source" in clip
        assert "start_time" in clip
        assert "duration" in clip
        assert "beat_aligned" in clip

    def test_quick_template(self):
        """Test quick music video template."""
        # Create a fresh context for quick template
        context = WorkflowContext(initial_prompt="Create quick music video")
        context.initial_params = {
            "music_file": "test.mp3",
            "images": ["img1.jpg", "img2.jpg"],
        }

        template = QuickMusicVideoTemplate()
        steps = template.define_steps(context)

        # Should have modified defaults
        assert context.initial_params["sync_mode"] == "downbeat"
        assert context.initial_params["transition_style"] == "energetic"
        assert context.initial_params["generate_proxies"] is False
        assert context.initial_params["export_formats"] == ["edl"]

    def test_cinematic_template(self):
        """Test cinematic music video template."""
        # Create a fresh context for cinematic template
        context = WorkflowContext(initial_prompt="Create cinematic music video")
        context.initial_params = {
            "music_file": "test.mp3",
            "images": ["img1.jpg", "img2.jpg"],
        }

        template = CinematicMusicVideoTemplate()
        steps = template.define_steps(context)

        # Should have quality defaults
        assert context.initial_params["sync_mode"] == "beat"
        assert context.initial_params["transition_style"] == "smooth"
        assert context.initial_params["generate_proxies"] is True
        assert "xml" in context.initial_params["export_formats"]

        # Should have color analysis step
        step_names = [step.name for step in steps]
        assert "analyze_color_flow" in step_names

    def test_energy_matching(self):
        """Test image-to-energy matching logic."""
        template = MusicVideoTemplate()

        images = ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"]
        energy_profile = [
            {"time": 0, "energy": 0.3},
            {"time": 10, "energy": 0.8},
            {"time": 20, "energy": 0.5},
        ]
        sections = [
            {"name": "intro", "start": 0, "end": 10, "energy": 0.3},
            {"name": "chorus", "start": 10, "end": 20, "energy": 0.8},
            {"name": "outro", "start": 20, "end": 30, "energy": 0.5},
        ]

        result = template._match_images_to_energy(images, energy_profile, sections)

        assert isinstance(result, list)
        assert len(result) > 0
        # High energy section should use different images than low energy

    def test_export_operation(self, mock_context):
        """Test timeline export operation."""
        template = MusicVideoTemplate()

        mock_context.results = {
            "create_timeline": {
                "success": True,
                "timeline": [
                    {
                        "clip_id": "clip_0",
                        "source": "img1.jpg",
                        "start_time": 0,
                        "duration": 2.0,
                    }
                ],
                "total_duration": 2.0,
                "music_file": "test.mp3",
            }
        }

        params = {
            "timeline_from": "create_timeline",
            "project_name": "Test Project",
            "frame_rate": 30,
        }

        # Mock the DaVinciResolveExporter
        with patch('alicemultiverse.workflows.video_export.DaVinciResolveExporter.export_xml') as mock_export:
            mock_export.return_value = True

            result = template._export_timeline("export_xml", params, mock_context)

            assert result["success"] is True
            assert result["format"] == "xml"
            assert "output_path" in result
