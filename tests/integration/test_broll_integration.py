"""Integration tests for the B-roll suggestion system."""

import tempfile
from pathlib import Path

import pytest

from alicemultiverse.storage import UnifiedDuckDBStorage
from alicemultiverse.workflows.broll_suggestions import BRollSuggestionEngine, SceneContext


class TestBRollIntegration:
    """Test B-roll suggestion functionality with real DuckDB integration."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as f:
            db_path = Path(f.name)
        yield str(db_path)
        db_path.unlink(missing_ok=True)

    @pytest.fixture
    def populated_db(self, temp_db_path):
        """Create and populate a test database."""
        db = UnifiedDuckDBStorage(temp_db_path)

        # Add various assets for b-roll suggestions
        test_assets = [
            # Primary footage
            ("primary1", "/primary/interview.mp4", {
                "media_type": "video",
                "tags": {"subject": ["person", "interview"], "mood": ["serious"]},
                "asset_role": "primary"
            }),

            # B-roll footage
            ("broll1", "/broll/cityscape.mp4", {
                "media_type": "video",
                "tags": {"subject": ["city", "buildings"], "mood": ["busy"], "style": ["urban"]},
                "asset_role": "b-roll"
            }),
            ("broll2", "/broll/nature.mp4", {
                "media_type": "video",
                "tags": {"subject": ["nature", "trees"], "mood": ["peaceful"], "style": ["calm"]},
                "asset_role": "b-roll"
            }),
            ("broll3", "/broll/abstract.mp4", {
                "media_type": "video",
                "tags": {"style": ["abstract", "texture"], "mood": ["neutral"]},
                "asset_role": "b-roll"
            }),

            # More primary footage
            ("primary2", "/primary/landscape.mp4", {
                "media_type": "video",
                "tags": {"subject": ["landscape", "mountains"], "mood": ["peaceful"]},
                "asset_role": "primary"
            }),

            # Additional b-roll
            ("broll4", "/broll/mountains.mp4", {
                "media_type": "video",
                "tags": {"subject": ["mountains", "landscape"], "mood": ["peaceful"], "style": ["nature"]},
                "asset_role": "b-roll"
            }),
            ("broll5", "/broll/transition1.mp4", {
                "media_type": "video",
                "tags": {"style": ["abstract", "pattern", "flowing"], "energy": ["high"]},
                "asset_role": "b-roll"
            }),
        ]

        for content_hash, path, metadata in test_assets:
            db.upsert_asset(content_hash, Path(path), metadata)

        db.close()
        return temp_db_path

    @pytest.fixture
    def broll_engine(self, populated_db):
        """Create a B-roll suggestion engine."""
        return BRollSuggestionEngine(db_path=populated_db)

    @pytest.mark.asyncio
    async def test_contextual_broll_suggestions(self, broll_engine):
        """Test finding b-roll based on subject context."""
        timeline = {
            "clips": [
                {"asset_path": "/primary/landscape.mp4", "duration": 10.0}
            ]
        }

        suggestions = await broll_engine.suggest_broll_for_timeline(
            timeline,
            max_suggestions_per_scene=5
        )

        # Should get suggestions for the landscape clip
        assert "0" in suggestions
        clip_suggestions = suggestions["0"]

        # Should find the mountains b-roll (matching subject)
        mountain_broll = [s for s in clip_suggestions if "mountains" in s.asset_path]
        assert len(mountain_broll) > 0
        assert mountain_broll[0].suggestion_type in ["contextual", "mood"]

    @pytest.mark.asyncio
    async def test_role_based_prioritization(self, broll_engine):
        """Test that assets marked as b-roll are prioritized."""
        # Create a scene needing abstract b-roll
        context = SceneContext(
            start_time=0.0,
            end_time=5.0,
            scene_type="transition",
            primary_subject=None,
            mood="neutral",
            location=None,
            dialogue=False,
            energy_level="medium",
            needs_visual_interest=True
        )

        clip = {"asset_path": "/primary/interview.mp4", "duration": 5.0}

        suggestions = await broll_engine._get_suggestions_for_context(
            context, clip, None, max_suggestions=10
        )

        # Assets marked as b-roll should appear
        broll_paths = [s.asset_path for s in suggestions if "broll" in s.asset_path]
        assert len(broll_paths) > 0

        # Abstract b-roll should be suggested for transitions
        abstract_suggestions = [s for s in suggestions if "abstract" in s.asset_path]
        assert len(abstract_suggestions) > 0

    @pytest.mark.asyncio
    async def test_mood_matching(self, broll_engine):
        """Test b-roll suggestions based on mood."""
        suggestions = await broll_engine._find_mood_matching_broll(
            mood="peaceful",
            energy_level="low",
            exclude_path="/primary/landscape.mp4"
        )

        # Should find nature b-roll (peaceful mood)
        assert len(suggestions) > 0
        peaceful_suggestions = [s for s in suggestions if "nature" in s.asset_path or "mountains" in s.asset_path]
        assert len(peaceful_suggestions) > 0

        # Verify suggestion metadata
        for suggestion in peaceful_suggestions:
            assert suggestion.suggestion_type == "mood"
            assert "peaceful" in suggestion.reasoning.lower()

    @pytest.mark.asyncio
    async def test_transition_broll(self, broll_engine):
        """Test finding b-roll suitable for transitions."""
        suggestions = await broll_engine._find_transition_broll(
            energy_level="high",
            project_context=None
        )

        # Should find abstract/flowing b-roll
        assert len(suggestions) > 0

        # High energy transitions should find flowing content
        flowing_suggestions = [s for s in suggestions if "flowing" in str(s.tags) or "transition" in s.asset_path]
        assert len(flowing_suggestions) > 0

        for suggestion in suggestions:
            assert suggestion.suggestion_type == "transition"
            assert suggestion.duration_suggestion == 1.0  # Short for transitions

    @pytest.mark.asyncio
    async def test_timeline_analysis(self, broll_engine):
        """Test full timeline b-roll analysis."""
        timeline = {
            "clips": [
                {"asset_path": "/primary/interview.mp4", "duration": 15.0},  # Long clip needs b-roll
                {"asset_path": "/primary/landscape.mp4", "duration": 3.0},   # Short clip
                {"asset_path": "/primary/interview.mp4", "duration": 20.0},  # Repetitive, needs variety
            ]
        }

        suggestions = await broll_engine.suggest_broll_for_timeline(timeline)

        # Long clips should get b-roll suggestions
        assert "0" in suggestions  # First long clip
        assert "2" in suggestions  # Second long clip (repetitive)

        # Should not suggest b-roll for short clips
        assert "1" not in suggestions or len(suggestions.get("1", [])) == 0

    @pytest.mark.asyncio
    async def test_deduplication(self, broll_engine):
        """Test that b-roll suggestions are deduplicated."""
        # Create multiple contexts that might suggest the same b-roll
        context = SceneContext(
            start_time=0.0,
            end_time=10.0,
            scene_type="wide",
            primary_subject="mountains",
            mood="peaceful",
            location="outdoor",
            dialogue=False,
            energy_level="low",
            needs_visual_interest=True
        )

        clip = {"asset_path": "/primary/interview.mp4", "duration": 10.0}

        suggestions = await broll_engine._get_suggestions_for_context(
            context, clip, None, max_suggestions=20
        )

        # Check for duplicates
        seen_hashes = set()
        for suggestion in suggestions:
            assert suggestion.content_hash not in seen_hashes
            seen_hashes.add(suggestion.content_hash)

    @pytest.mark.asyncio
    async def test_exclude_self(self, broll_engine):
        """Test that b-roll doesn't suggest the same clip."""
        suggestions = await broll_engine._find_contextual_broll(
            subject="mountains",
            location="outdoor",
            exclude_path="/broll/mountains.mp4"
        )

        # Should not suggest the excluded path
        for suggestion in suggestions:
            assert suggestion.asset_path != "/broll/mountains.mp4"

    def test_tag_extraction(self, broll_engine):
        """Test tag value extraction from structured format."""
        # Test with structured tags
        structured_tags = {
            "subject": [{"value": "mountains", "confidence": 0.9}],
            "mood": [{"value": "peaceful", "confidence": 0.8}],
            "style": [{"value": "landscape", "confidence": 0.7}]
        }

        tag_values = broll_engine._extract_tag_values(structured_tags)
        assert "mountains" in tag_values
        assert "peaceful" in tag_values
        assert "landscape" in tag_values

        # Test with mixed format
        mixed_tags = {
            "subject": ["direct_value"],
            "mood": [{"value": "calm", "confidence": 0.9}]
        }

        tag_values = broll_engine._extract_tag_values(mixed_tags)
        assert "direct_value" in tag_values
        assert "calm" in tag_values
