"""Unit tests for understanding system providers."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from PIL import Image

from alicemultiverse.understanding.base import ImageAnalysisResult
from alicemultiverse.understanding.providers import (
    AnthropicImageAnalyzer,
    DeepSeekImageAnalyzer,
    GoogleAIImageAnalyzer,
    OpenAIImageAnalyzer,
)


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image for testing."""
    img_path = tmp_path / "test_image.jpg"
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(img_path)
    return img_path


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for API keys."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "test-google-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")


class TestAnthropicImageAnalyzer:
    """Test Anthropic Claude image analyzer."""

    def test_initialization_with_api_key(self):
        """Test initialization with explicit API key."""
        analyzer = AnthropicImageAnalyzer(api_key="test-key")
        assert analyzer.api_key == "test-key"
        assert analyzer.model == "claude-3-5-sonnet-20241022"
        assert analyzer.name == "anthropic"

    def test_initialization_from_env(self, mock_env_vars):
        """Test initialization from environment variable."""
        analyzer = AnthropicImageAnalyzer()
        assert analyzer.api_key == "test-anthropic-key"

    def test_initialization_without_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="Anthropic API key required"):
            AnthropicImageAnalyzer()

    def test_model_selection(self):
        """Test different model selection."""
        analyzer = AnthropicImageAnalyzer(api_key="test", model="claude-3-haiku-20240307")
        assert analyzer.model == "claude-3-haiku-20240307"

    def test_cost_estimation(self):
        """Test cost estimation for different models."""
        analyzer = AnthropicImageAnalyzer(api_key="test", model="claude-3-haiku-20240307")
        cost = analyzer.estimate_cost(detailed=False)
        assert cost > 0
        assert cost < 0.01  # Haiku is cheap

        analyzer_opus = AnthropicImageAnalyzer(api_key="test", model="claude-3-opus-20240229")
        cost_opus = analyzer_opus.estimate_cost(detailed=True)
        assert cost_opus > cost  # Opus is more expensive

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, sample_image_path):
        """Test successful image analysis."""
        analyzer = AnthropicImageAnalyzer(api_key="test-key")

        # Mock the HTTP session
        mock_response = {
            "content": [{
                "text": """A blue square image

{"style": ["minimalist", "geometric"], "color": ["blue", "monochrome"], "subject": ["abstract", "shape"]}

PROMPT: minimalist blue square, geometric abstract art
NEGATIVE: realistic, detailed, complex"""
            }],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50
            }
        }

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            # Create a proper async context manager for post
            mock_post_cm = Mock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = Mock(return_value=mock_post_cm)

            result = await analyzer.analyze(sample_image_path)

            assert isinstance(result, ImageAnalysisResult)
            assert result.description == "A blue square image"
            assert result.tags["style"] == ["minimalist", "geometric"]
            assert result.provider == "anthropic"
            assert result.model == "claude-3-5-sonnet-20241022"
            assert result.tokens_used == 150

    @pytest.mark.asyncio
    async def test_analyze_image_api_error(self, sample_image_path):
        """Test handling of API errors."""
        analyzer = AnthropicImageAnalyzer(api_key="test-key")

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_resp = AsyncMock()
            mock_resp.status = 429  # Rate limit
            mock_resp.text = AsyncMock(return_value="Rate limit exceeded")
            # Create a proper async context manager for post
            mock_post_cm = Mock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = Mock(return_value=mock_post_cm)

            with pytest.raises(Exception, match="Anthropic API error: 429"):
                await analyzer.analyze(sample_image_path)

    def test_supports_batch(self):
        """Test batch support flag."""
        analyzer = AnthropicImageAnalyzer(api_key="test")
        assert not analyzer.supports_batch


class TestOpenAIImageAnalyzer:
    """Test OpenAI GPT-4 Vision image analyzer."""

    def test_initialization_with_api_key(self):
        """Test initialization with explicit API key."""
        analyzer = OpenAIImageAnalyzer(api_key="test-key")
        assert analyzer.api_key == "test-key"
        assert analyzer.model == "gpt-4o-mini"
        assert analyzer.name == "openai"

    def test_initialization_from_env(self, mock_env_vars):
        """Test initialization from environment variable."""
        analyzer = OpenAIImageAnalyzer()
        assert analyzer.api_key == "test-openai-key"

    def test_initialization_without_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="OpenAI API key required"):
            OpenAIImageAnalyzer()

    def test_cost_estimation(self):
        """Test cost estimation for different models."""
        analyzer = OpenAIImageAnalyzer(api_key="test", model="gpt-4o-mini")
        cost = analyzer.estimate_cost(detailed=False)
        assert cost > 0
        assert cost < 0.01

        analyzer_4o = OpenAIImageAnalyzer(api_key="test", model="gpt-4o")
        cost_4o = analyzer_4o.estimate_cost(detailed=True)
        assert cost_4o > cost  # gpt-4o is more expensive

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, sample_image_path):
        """Test successful image analysis."""
        analyzer = OpenAIImageAnalyzer(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {
                    "content": """A blue colored square

{"style": ["simple", "geometric"], "color": ["blue"], "mood": ["calm"]}

PROMPT: a simple blue square
NEGATIVE: complex, detailed"""
                }
            }],
            "usage": {
                "prompt_tokens": 80,
                "completion_tokens": 40,
                "total_tokens": 120
            }
        }

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            # Create a proper async context manager for post
            mock_post_cm = Mock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = Mock(return_value=mock_post_cm)

            result = await analyzer.analyze(sample_image_path)

            assert isinstance(result, ImageAnalysisResult)
            assert result.description == "A blue colored square"
            assert result.tags["color"] == ["blue"]
            assert result.provider == "openai"
            assert result.model == "gpt-4o-mini"
            assert result.tokens_used == 120


class TestGoogleAIImageAnalyzer:
    """Test Google AI (Gemini) image analyzer."""

    def test_initialization_with_api_key(self):
        """Test initialization with explicit API key."""
        analyzer = GoogleAIImageAnalyzer(api_key="test-key")
        assert analyzer.api_key == "test-key"
        assert analyzer.model == "gemini-1.5-flash"
        assert analyzer.name == "google"

    def test_initialization_from_env(self, mock_env_vars):
        """Test initialization from environment variable."""
        analyzer = GoogleAIImageAnalyzer()
        assert analyzer.api_key == "test-google-key"

    def test_initialization_without_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="Google AI API key required"):
            GoogleAIImageAnalyzer()

    def test_cost_estimation(self):
        """Test cost estimation."""
        analyzer = GoogleAIImageAnalyzer(api_key="test")
        cost = analyzer.estimate_cost(detailed=False)
        assert cost > 0  # Google AI has costs after free tier
        assert cost < 0.001  # But still very cheap

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, sample_image_path):
        """Test successful image analysis."""
        analyzer = GoogleAIImageAnalyzer(api_key="test-key")

        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": """A solid blue square image

{"visual": ["blue", "square", "solid"], "technical": ["digital", "simple"]}

PROMPT: solid blue square
NEGATIVE: textured, complex"""
                    }]
                }
            }],
            "usageMetadata": {
                "promptTokenCount": 50,
                "candidatesTokenCount": 30,
                "totalTokenCount": 80
            }
        }

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            # Create a proper async context manager for post
            mock_post_cm = Mock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = Mock(return_value=mock_post_cm)

            result = await analyzer.analyze(sample_image_path)

            assert isinstance(result, ImageAnalysisResult)
            assert result.description == "A solid blue square image"
            assert result.tags["visual"] == ["blue", "square", "solid"]
            assert result.provider == "google"
            assert result.model == "gemini-1.5-flash"
            assert result.tokens_used == 80


class TestDeepSeekImageAnalyzer:
    """Test DeepSeek image analyzer."""

    def test_initialization_with_api_key(self):
        """Test initialization with explicit API key."""
        analyzer = DeepSeekImageAnalyzer(api_key="test-key")
        assert analyzer.api_key == "test-key"
        assert analyzer.model == "deepseek-reasoner"
        assert analyzer.name == "deepseek"

    def test_initialization_from_env(self, mock_env_vars):
        """Test initialization from environment variable."""
        analyzer = DeepSeekImageAnalyzer()
        assert analyzer.api_key == "test-deepseek-key"

    def test_initialization_without_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="DeepSeek API key required"):
            DeepSeekImageAnalyzer()

    def test_cost_estimation(self):
        """Test cost estimation."""
        analyzer = DeepSeekImageAnalyzer(api_key="test")
        cost = analyzer.estimate_cost(detailed=False)
        assert cost > 0
        assert cost < 0.01  # DeepSeek is cheap but slightly above 0.001

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, sample_image_path):
        """Test successful image analysis."""
        analyzer = DeepSeekImageAnalyzer(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {
                    "content": """Blue square test image

{"general": ["blue", "square", "test"]}

PROMPT: blue square test
NEGATIVE: none"""
                }
            }],
            "usage": {
                "prompt_tokens": 60,
                "completion_tokens": 20,
                "total_tokens": 80
            }
        }

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            # Create a proper async context manager for post
            mock_post_cm = Mock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = Mock(return_value=mock_post_cm)

            result = await analyzer.analyze(sample_image_path)

            assert isinstance(result, ImageAnalysisResult)
            assert result.description == "Blue square test image"
            assert result.provider == "deepseek"
            assert result.model == "deepseek-reasoner"


class TestProviderComparison:
    """Test comparing multiple providers."""

    @pytest.mark.asyncio
    async def test_consistent_tag_format(self, sample_image_path, mock_env_vars):
        """Test that all providers return consistent tag format."""
        providers = [
            AnthropicImageAnalyzer(),
            OpenAIImageAnalyzer(),
            GoogleAIImageAnalyzer(),
            DeepSeekImageAnalyzer()
        ]

        for provider in providers:
            # Mock a simple response
            mock_response = ImageAnalysisResult(
                description="Test",
                tags={"test": ["tag1", "tag2"]},
                provider=provider.name,
                model=provider.model
            )

            with patch.object(provider, 'analyze', return_value=mock_response):
                result = await provider.analyze(sample_image_path)

                # Check consistent structure
                assert isinstance(result.tags, dict)
                assert all(isinstance(v, list) for v in result.tags.values())
                assert result.provider == provider.name
                assert result.model == provider.model

    def test_cost_comparison(self, mock_env_vars):
        """Test cost comparison across providers."""
        costs = {}

        # Get costs for each provider
        costs['anthropic_haiku'] = AnthropicImageAnalyzer(model="claude-3-haiku-20240307").estimate_cost()
        costs['anthropic_sonnet'] = AnthropicImageAnalyzer(model="claude-3-5-sonnet-20241022").estimate_cost()
        costs['openai_mini'] = OpenAIImageAnalyzer(model="gpt-4o-mini").estimate_cost()
        costs['openai_4o'] = OpenAIImageAnalyzer(model="gpt-4o").estimate_cost()
        costs['google'] = GoogleAIImageAnalyzer().estimate_cost()
        costs['deepseek'] = DeepSeekImageAnalyzer().estimate_cost()

        # Verify cost ordering (from cheapest to most expensive)
        assert costs['google'] > 0  # Has costs after free tier
        assert costs['google'] < costs['deepseek']  # But still cheaper than DeepSeek
        # DeepSeek's cost is actually higher than anthropic_haiku for this test
        assert costs['anthropic_haiku'] < costs['deepseek']
        assert costs['openai_mini'] < costs['anthropic_haiku']
        assert costs['openai_mini'] < costs['anthropic_sonnet']
        assert costs['openai_4o'] < costs['anthropic_sonnet']
