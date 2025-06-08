"""Tests for natural language timeline editing."""

import pytest
from pathlib import Path

from alicemultiverse.interface.timeline_nlp import (
    TimelineNLPProcessor,
    EditIntent,
    TimelineEdit,
)
from alicemultiverse.workflows.video_export import Timeline, TimelineClip


class TestTimelineNLPProcessor:
    """Test natural language processing for timeline edits."""
    
    @pytest.fixture
    def processor(self):
        """Create NLP processor instance."""
        return TimelineNLPProcessor()
    
    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline for testing."""
        clips = [
            TimelineClip(
                asset_path=Path(f"/test/clip{i}.jpg"),
                start_time=i * 3.0,
                duration=3.0
            )
            for i in range(10)
        ]
        
        return Timeline(
            name="Test Timeline",
            duration=30.0,
            clips=clips,
            markers=[
                {"time": 3.0, "type": "beat", "label": "Beat 1"},
                {"time": 6.0, "type": "beat", "label": "Beat 2"},
                {"time": 9.0, "type": "beat", "label": "Beat 3"},
                {"time": 12.0, "type": "section", "label": "Drop"},
            ]
        )
    
    def test_parse_pace_commands(self, processor, sample_timeline):
        """Test parsing pace change commands."""
        # Test "make intro faster"
        edits = processor.parse_command("make the intro faster", sample_timeline)
        assert len(edits) > 0
        assert edits[0].intent == EditIntent.PACE_CHANGE
        assert edits[0].target_section == "intro"
        assert edits[0].parameters["factor"] > 1.0
        
        # Test "slow down outro"
        edits = processor.parse_command("slow down the outro", sample_timeline)
        assert len(edits) > 0
        assert edits[0].intent == EditIntent.PACE_CHANGE
        assert edits[0].target_section == "outro"
        assert edits[0].parameters["factor"] < 1.0
        
        # Test "make it punchier"
        edits = processor.parse_command("make the intro punchier", sample_timeline)
        assert edits[0].parameters["modifier"] == "punchier"
    
    def test_parse_pause_commands(self, processor, sample_timeline):
        """Test parsing pause/breathing room commands."""
        # Test "add breathing room"
        edits = processor.parse_command("add breathing room after the drop", sample_timeline)
        assert len(edits) > 0
        assert edits[0].intent == EditIntent.ADD_PAUSE
        assert edits[0].target_section == "drop"
        assert edits[0].parameters["position"] == "after"
        
        # Test "let it breathe"
        edits = processor.parse_command("let the intro breathe", sample_timeline)
        assert len(edits) > 0
        assert edits[0].intent == EditIntent.ADD_PAUSE
    
    def test_parse_sync_commands(self, processor, sample_timeline):
        """Test parsing sync/rhythm commands."""
        # Test "sync to beat"
        edits = processor.parse_command("sync all cuts to the beat", sample_timeline)
        assert len(edits) > 0
        assert edits[0].intent == EditIntent.SYNC_ADJUST
        assert edits[0].parameters["target"] == "beat"
        
        # Test section-specific sync
        edits = processor.parse_command("put the intro on the beat", sample_timeline)
        assert edits[0].target_section == "intro"
    
    def test_parse_energy_commands(self, processor, sample_timeline):
        """Test parsing energy/intensity commands."""
        # Test increase energy
        edits = processor.parse_command("add more energy to the chorus", sample_timeline)
        assert len(edits) > 0
        assert edits[0].intent == EditIntent.ENERGY_ADJUST
        assert edits[0].parameters["intensity"] > 1.0
        
        # Test decrease energy
        edits = processor.parse_command("make the outro more chill", sample_timeline)
        assert edits[0].parameters["intensity"] < 1.0
    
    def test_apply_pace_change(self, processor, sample_timeline):
        """Test applying pace changes to timeline."""
        # Create pace change edit
        edit = TimelineEdit(
            intent=EditIntent.PACE_CHANGE,
            target_section="intro",
            parameters={"factor": 2.0}  # Double speed
        )
        
        # Apply edit
        modified = processor.apply_edits(sample_timeline, [edit])
        
        # Check first few clips are shorter
        intro_clips = 2  # First 20% of 10 clips
        for i in range(intro_clips):
            assert modified.clips[i].duration < sample_timeline.clips[i].duration
            assert modified.clips[i].duration == pytest.approx(1.5)  # 3.0 / 2.0
    
    def test_apply_pause(self, processor, sample_timeline):
        """Test applying pauses to timeline."""
        # Add pause after first clip
        edit = TimelineEdit(
            intent=EditIntent.ADD_PAUSE,
            target_clips=[0],
            parameters={"position": "after", "duration": 2.0}
        )
        
        modified = processor.apply_edits(sample_timeline, [edit])
        
        # Check subsequent clips are shifted
        assert modified.clips[1].start_time == sample_timeline.clips[1].start_time + 2.0
        assert modified.duration > sample_timeline.duration
    
    def test_apply_sync_to_beat(self, processor, sample_timeline):
        """Test syncing clips to beat markers."""
        # Create clips slightly off beat
        sample_timeline.clips[0].start_time = 0.2  # Should snap to 0
        sample_timeline.clips[1].start_time = 3.3  # Should snap to 3
        
        edit = TimelineEdit(
            intent=EditIntent.SYNC_ADJUST,
            target_clips=[0, 1],
            parameters={"target": "beat"}
        )
        
        modified = processor.apply_edits(sample_timeline, [edit])
        
        # Check clips snapped to beats
        assert modified.clips[0].start_time == 0.0  # Snapped to start
        assert modified.clips[1].start_time == 3.0  # Snapped to beat at 3.0
    
    def test_suggest_edits(self, processor):
        """Test edit suggestions based on timeline analysis."""
        # Create timeline with long clips
        long_clips = [
            TimelineClip(
                asset_path=Path(f"/test/clip{i}.jpg"),
                start_time=i * 8.0,
                duration=8.0
            )
            for i in range(5)
        ]
        
        timeline = Timeline(
            name="Slow Timeline",
            duration=40.0,
            clips=long_clips
        )
        
        suggestions = processor.suggest_edits(timeline)
        
        # Should suggest speeding up
        assert any("faster" in s.lower() for s in suggestions)
        assert any("energy" in s.lower() for s in suggestions)
    
    def test_section_mapping(self, processor):
        """Test section name normalization."""
        assert processor._normalize_section("intro") == "intro"
        assert processor._normalize_section("introduction") == "intro"
        assert processor._normalize_section("beginning") == "intro"
        assert processor._normalize_section("ending") == "outro"
        assert processor._normalize_section("drop") == "drop"
    
    def test_generic_commands(self, processor, sample_timeline):
        """Test parsing generic/fallback commands."""
        # Test transition command
        edits = processor.parse_command("add dissolve transitions", sample_timeline)
        assert any(e.intent == EditIntent.TRANSITION_CHANGE for e in edits)
        
        # Test removal command
        edits = processor.parse_command("remove the weak shots", sample_timeline)
        assert any(e.intent == EditIntent.REMOVE_CLIPS for e in edits)
        
        # Test duplication
        edits = processor.parse_command("duplicate the best part", sample_timeline)
        assert any(e.intent == EditIntent.DUPLICATE for e in edits)
    
    def test_confidence_scores(self, processor, sample_timeline):
        """Test that confidence scores are assigned."""
        # Clear pattern match should have high confidence
        edits = processor.parse_command("make the intro faster", sample_timeline)
        assert edits[0].confidence >= 0.8
        
        # Generic command should have lower confidence
        edits = processor.parse_command("improve the flow", sample_timeline)
        if edits:
            assert all(e.confidence < 0.8 for e in edits)
    
    def test_multiple_edits_in_command(self, processor, sample_timeline):
        """Test commands that trigger multiple edits."""
        # This command should trigger both pace and sync edits
        edits = processor.parse_command(
            "make faster cuts in the intro and sync to beat",
            sample_timeline
        )
        
        intents = [e.intent for e in edits]
        assert EditIntent.PACE_CHANGE in intents
        assert EditIntent.SYNC_ADJUST in intents


@pytest.mark.asyncio
class TestTimelineNLPMCP:
    """Test MCP integration for NLP timeline editing."""
    
    async def test_process_timeline_command(self):
        """Test processing a natural language command."""
        from alicemultiverse.interface.timeline_nlp_mcp import process_timeline_command
        
        timeline_data = {
            "name": "Test",
            "duration": 30.0,
            "clips": [
                {
                    "asset_path": f"/test/clip{i}.jpg",
                    "start_time": i * 3.0,
                    "duration": 3.0
                }
                for i in range(10)
            ],
            "markers": []
        }
        
        result = await process_timeline_command(
            command="make the intro faster",
            timeline_data=timeline_data,
            preview=False
        )
        
        assert result["success"] is True
        assert "timeline" in result
        assert len(result["edits_applied"]) > 0
        
        # Check that intro clips are now shorter
        modified_clips = result["timeline"]["clips"]
        assert modified_clips[0]["duration"] < 3.0
    
    async def test_suggest_timeline_improvements(self):
        """Test getting timeline improvement suggestions."""
        from alicemultiverse.interface.timeline_nlp_mcp import suggest_timeline_edits
        
        timeline_data = {
            "name": "Test",
            "duration": 40.0,
            "clips": [
                {
                    "asset_path": f"/test/clip{i}.jpg",
                    "start_time": i * 8.0,
                    "duration": 8.0
                }
                for i in range(5)
            ],
            "markers": []
        }
        
        result = await suggest_timeline_edits(timeline_data)
        
        assert result["success"] is True
        assert len(result["suggestions"]) > 0
        assert "analysis" in result
        assert result["analysis"]["pace"] == "slow"
    
    async def test_batch_timeline_edits(self):
        """Test applying multiple commands in sequence."""
        from alicemultiverse.interface.timeline_nlp_mcp import batch_timeline_edits
        
        timeline_data = {
            "name": "Test",
            "duration": 30.0,
            "clips": [
                {
                    "asset_path": f"/test/clip{i}.jpg",
                    "start_time": i * 3.0,
                    "duration": 3.0
                }
                for i in range(10)
            ],
            "markers": [
                {"time": i * 3.0, "type": "beat"}
                for i in range(10)
            ]
        }
        
        commands = [
            "make the intro faster",
            "add breathing room after the intro",
            "sync all cuts to the beat"
        ]
        
        result = await batch_timeline_edits(
            commands=commands,
            timeline_data=timeline_data
        )
        
        assert result["success"] is True
        assert result["commands_processed"] == 3
        assert "final_timeline" in result
    
    def test_get_command_examples(self):
        """Test getting command examples."""
        from alicemultiverse.interface.timeline_nlp_mcp import get_command_examples
        
        # Get all examples
        all_examples = get_command_examples()
        assert "pace" in all_examples
        assert "rhythm" in all_examples
        assert "energy" in all_examples
        
        # Get specific category
        pace_examples = get_command_examples("pace")
        assert "pace" in pace_examples
        assert len(pace_examples["pace"]) > 0
        assert any("faster" in ex for ex in pace_examples["pace"])