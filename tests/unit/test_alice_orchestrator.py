"""Tests for Alice orchestrator."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from alicemultiverse.interface import (
    AliceAPI,
    AliceOrchestrator,
    CreativeIntent,
    ask_alice,
    ask_alice_sync,
)


class TestAliceOrchestrator:
    """Test AliceOrchestrator functionality."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator without database."""
        with patch("alicemultiverse.interface.alice_orchestrator.get_session"):
            return AliceOrchestrator()

    def test_determine_intent(self, orchestrator):
        """Test intent determination from natural language."""
        # Search intents
        assert orchestrator._determine_intent("Find cyberpunk images") == CreativeIntent.SEARCH
        assert orchestrator._determine_intent("Show me the neon stuff") == CreativeIntent.SEARCH
        assert orchestrator._determine_intent("Where is that character?") == CreativeIntent.SEARCH

        # Create intents
        assert orchestrator._determine_intent("Create a new character") == CreativeIntent.CREATE
        assert orchestrator._determine_intent("Generate a landscape") == CreativeIntent.CREATE
        assert orchestrator._determine_intent("Make something cool") == CreativeIntent.CREATE

        # Memory intents
        assert orchestrator._determine_intent("Remember what we did") == CreativeIntent.REMEMBER
        assert orchestrator._determine_intent("What did we work on?") == CreativeIntent.REMEMBER

        # Explore intents
        assert orchestrator._determine_intent("Explore variations") == CreativeIntent.EXPLORE
        assert orchestrator._determine_intent("Show similar images") == CreativeIntent.EXPLORE

    def test_parse_temporal_reference(self, orchestrator):
        """Test parsing temporal references."""
        now = datetime.now(UTC)

        # Yesterday
        yesterday = orchestrator._parse_temporal_reference("yesterday")
        assert yesterday is not None
        # Check it's approximately 1 day ago (within a few seconds)
        diff = now - yesterday
        assert 0.99 < diff.total_seconds() / 86400 < 1.01

        # Last week
        last_week = orchestrator._parse_temporal_reference("last week")
        assert last_week is not None
        # Check it's approximately 7 days ago
        diff = now - last_week
        assert 6.99 < diff.total_seconds() / 86400 < 7.01

        # Last month
        last_month = orchestrator._parse_temporal_reference("last month")
        assert last_month is not None
        # Check it's approximately 30 days ago
        diff = now - last_month  
        assert 29.99 < diff.total_seconds() / 86400 < 30.01

        # X days ago
        three_days = orchestrator._parse_temporal_reference("3 days ago")
        assert three_days is not None
        # Check it's approximately 3 days ago
        diff = now - three_days
        assert 2.99 < diff.total_seconds() / 86400 < 3.01

        # Month names
        october = orchestrator._parse_temporal_reference("in October")
        assert october is not None
        assert october.month == 10

        # Invalid
        assert orchestrator._parse_temporal_reference("random text") is None

    def test_extract_creative_elements(self, orchestrator):
        """Test extracting creative elements from text."""
        # Styles
        elements = orchestrator._extract_creative_elements("cyberpunk neon city")
        assert "cyberpunk" in elements["styles"]

        # Moods
        elements = orchestrator._extract_creative_elements("dark moody atmosphere")
        assert "dark" in elements["moods"]
        assert "moody" in elements["moods"]

        # Colors
        elements = orchestrator._extract_creative_elements("vibrant blue and purple")
        assert "vibrant" in elements["colors"]
        assert "blue" in elements["colors"]
        assert "purple" in elements["colors"]

        # Multiple elements
        elements = orchestrator._extract_creative_elements(
            "dark cyberpunk scene with neon pink lights"
        )
        assert "cyberpunk" in elements["styles"]
        assert "dark" in elements["moods"]
        assert "neon" in elements["colors"]
        assert "pink" in elements["colors"]

    def test_update_memory(self, orchestrator):
        """Test memory updates."""
        # Search memory
        orchestrator._update_memory(CreativeIntent.SEARCH, {"query": "cyberpunk characters"})
        assert "cyberpunk characters" in orchestrator.memory.recent_searches

        # Creation memory
        orchestrator._update_memory(
            CreativeIntent.CREATE, {"prompt": "neon city scene", "style": "cyberpunk"}
        )
        assert "neon city scene" in orchestrator.memory.recent_creations

        # Pattern tracking
        assert "create:cyberpunk" in orchestrator.memory.creative_patterns
        assert orchestrator.memory.creative_patterns["create:cyberpunk"] == 1

        # Multiple updates increase count
        orchestrator._update_memory(
            CreativeIntent.CREATE, {"prompt": "another scene", "style": "cyberpunk"}
        )
        assert orchestrator.memory.creative_patterns["create:cyberpunk"] == 2

    @pytest.mark.asyncio
    async def test_understand_search_request(self, orchestrator):
        """Test understanding search requests."""
        # Mock search methods
        orchestrator._semantic_search = AsyncMock(return_value=[])
        orchestrator._structured_search = AsyncMock(return_value=[])

        response = await orchestrator.understand("Find cyberpunk images from last week")

        assert response.success
        assert "Found 0 assets" in response.message
        assert response.memory_updated

    @pytest.mark.asyncio
    async def test_understand_create_request(self, orchestrator):
        """Test understanding creation requests."""
        response = await orchestrator.understand("Create a neon city scene")

        assert response.success
        assert "Creation workflow initiated" in response.message
        assert "workflow_id" in response.context
        assert response.events_published == ["workflow.started"]

    @pytest.mark.asyncio
    async def test_understand_memory_request(self, orchestrator):
        """Test understanding memory requests."""
        # Add some memory
        orchestrator.memory.recent_searches = ["cyberpunk", "neon"]
        orchestrator.memory.recent_creations = ["city scene"]

        # Test search memory
        response = await orchestrator.understand("What have I searched for?")
        assert response.success
        assert "recent_searches" in response.context

        # Test creation memory
        response = await orchestrator.understand("What have we created?")
        assert response.success
        assert "recent_creations" in response.context

    @pytest.mark.asyncio
    async def test_handle_vague_request(self, orchestrator):
        """Test handling vague/unclear requests."""
        response = await orchestrator.understand("Do something creative")

        assert response.success
        assert len(response.suggestions) > 0
        # Print suggestions for debugging
        print(f"Suggestions: {response.suggestions}")
        # Check that suggestions are helpful
        assert any(s for s in response.suggestions)  # Just verify we have suggestions


class TestAliceAPI:
    """Test AliceAPI wrapper."""

    @pytest.fixture
    def api(self):
        """Create API without database."""
        with patch("alicemultiverse.interface.alice_orchestrator.get_session"):
            return AliceAPI()

    @pytest.mark.asyncio
    async def test_request_method(self, api):
        """Test main request method."""
        result = await api.request("Find cyberpunk images")

        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        assert "data" in result
        assert "suggestions" in result

    @pytest.mark.asyncio
    async def test_remember_method(self, api):
        """Test remember method."""
        result = await api.remember()

        assert isinstance(result, dict)
        assert "success" in result
        assert "memory" in result

    @pytest.mark.asyncio
    async def test_suggest_method(self, api):
        """Test suggest method."""
        result = await api.suggest()

        assert isinstance(result, dict)
        assert "success" in result
        assert "suggestions" in result


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_ask_alice(self):
        """Test ask_alice helper."""
        with patch("alicemultiverse.interface.alice_orchestrator.get_session"):
            result = await ask_alice("Find images")

            assert isinstance(result, dict)
            assert "success" in result

    def test_ask_alice_sync(self):
        """Test synchronous ask_alice."""
        with patch("alicemultiverse.interface.alice_orchestrator.get_session"):
            result = ask_alice_sync("Find images")

            assert isinstance(result, dict)
            assert "success" in result


class TestCreativeMemory:
    """Test creative memory functionality."""

    def test_memory_limits(self):
        """Test memory size limits."""
        with patch("alicemultiverse.interface.alice_orchestrator.get_session"):
            orchestrator = AliceOrchestrator()

            # Add many searches
            for i in range(30):
                orchestrator._update_memory(CreativeIntent.SEARCH, {"query": f"search {i}"})

            # Should only keep last 20
            assert len(orchestrator.memory.recent_searches) == 20
            assert "search 29" in orchestrator.memory.recent_searches
            assert "search 9" not in orchestrator.memory.recent_searches

            # Add many creations
            for i in range(15):
                orchestrator._update_memory(CreativeIntent.CREATE, {"prompt": f"creation {i}"})

            # Should only keep last 10
            assert len(orchestrator.memory.recent_creations) == 10
            assert "creation 14" in orchestrator.memory.recent_creations
            assert "creation 4" not in orchestrator.memory.recent_creations


class TestPatternExtraction:
    """Test pattern extraction from requests."""

    @pytest.fixture
    def orchestrator(self):
        with patch("alicemultiverse.interface.alice_orchestrator.get_session"):
            return AliceOrchestrator()

    def test_extract_prompt(self, orchestrator):
        """Test prompt extraction from creation requests."""
        # Simple
        prompt = orchestrator._extract_prompt("Create a beautiful sunset")
        assert prompt == "a beautiful sunset"

        # With multiple create words
        prompt = orchestrator._extract_prompt("Generate and create a city scene")
        assert "city scene" in prompt

        # Case insensitive
        prompt = orchestrator._extract_prompt("MAKE a robot character")
        assert prompt == "a robot character"

    def test_enhance_prompt_with_style(self, orchestrator):
        """Test prompt enhancement with styles."""
        orchestrator.memory.active_styles = {"mood": "dark", "color": "neon"}

        enhanced = orchestrator._enhance_prompt_with_style(
            "city scene", orchestrator.memory.active_styles
        )

        assert "city scene" in enhanced
        assert "dark" in enhanced
        assert "neon" in enhanced
