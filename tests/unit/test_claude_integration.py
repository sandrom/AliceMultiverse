"""Unit tests for Claude API integration."""

from unittest.mock import Mock, patch

import pytest
from PIL import Image

from alicemultiverse.core.types import MediaType
from alicemultiverse.quality.claude import (
    CLAUDE_PROMPT,
    _parse_claude_response,
    check_image_defects,
    estimate_cost,
)


class TestClaudeIntegration:
    """Test Claude API integration for defect detection."""

    @pytest.mark.unit
    def test_check_image_defects_success(self, temp_dir):
        """Test successful image defect check."""
        # Create test image
        test_img = temp_dir / "test.png"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(test_img)

        # Mock anthropic client
        with patch("alicemultiverse.quality.claude.anthropic") as mock_anthropic:
            # Setup mock client
            mock_client = Mock()
            mock_anthropic.Anthropic.return_value = mock_client

            # Mock message response
            mock_message = Mock()
            mock_message.content = [
                Mock(
                    text="""
defects_found: true
defect_count: 3
severity: medium
confidence: 0.85

defects:
- Extra finger on right hand
- Unnatural skin texture on arm
- Perspective error in background
            """
                )
            ]
            mock_message.usage.input_tokens = 1000
            mock_message.usage.output_tokens = 200

            mock_client.messages.create.return_value = mock_message

            # Call function
            result = check_image_defects(str(test_img), "test-api-key")

            # Verify client was initialized correctly
            mock_anthropic.Anthropic.assert_called_once_with(api_key="test-api-key")

            # Verify message creation
            create_call = mock_client.messages.create.call_args
            assert create_call.kwargs["model"] == "claude-3-haiku-20240307"
            assert create_call.kwargs["max_tokens"] == 1000
            assert create_call.kwargs["temperature"] == 0

            # Check message content
            messages = create_call.kwargs["messages"]
            assert len(messages) == 1
            assert messages[0]["role"] == "user"
            assert len(messages[0]["content"]) == 2  # Image and text

            # Verify image encoding
            image_content = messages[0]["content"][0]
            assert image_content["type"] == "image"
            assert image_content["source"]["type"] == "base64"
            assert image_content["source"]["media_type"] == "image/png"
            assert isinstance(image_content["source"]["data"], str)

            # Verify prompt
            text_content = messages[0]["content"][1]
            assert text_content["type"] == "text"
            assert text_content["text"] == CLAUDE_PROMPT

            # Verify parsed result
            assert result is not None
            assert result["defects_found"] is True
            assert result["defect_count"] == 3
            assert result["severity"] == "medium"
            assert result["confidence"] == 0.85
            assert len(result["defects"]) == 3
            assert "extra finger" in result["defects"][0]
            assert result["tokens_used"] == 1200

    @pytest.mark.unit
    def test_check_image_defects_no_defects(self, temp_dir):
        """Test image with no defects found."""
        test_img = temp_dir / "test.jpg"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(test_img)

        with patch("alicemultiverse.quality.claude.anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.Anthropic.return_value = mock_client

            mock_message = Mock()
            mock_message.content = [
                Mock(
                    text="""
defects_found: false
defect_count: 0
severity: low
confidence: 0.95

No significant defects found. The image appears to be well-generated with proper anatomical proportions and consistent textures.
            """
                )
            ]
            mock_message.usage.input_tokens = 1000
            mock_message.usage.output_tokens = 100

            mock_client.messages.create.return_value = mock_message

            result = check_image_defects(str(test_img), "test-api-key")

            assert result["defects_found"] is False
            assert result["defect_count"] == 0
            assert result["severity"] == "low"
            assert result["confidence"] == 0.95
            assert len(result["defects"]) == 0

    @pytest.mark.unit
    def test_check_image_defects_api_error(self, temp_dir):
        """Test handling of API errors."""
        test_img = temp_dir / "test.png"
        img = Image.new("RGB", (100, 100), color="green")
        img.save(test_img)

        with patch("alicemultiverse.quality.claude.anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.Anthropic.return_value = mock_client

            # Simulate API error
            mock_client.messages.create.side_effect = Exception("API rate limit exceeded")

            result = check_image_defects(str(test_img), "test-api-key")

            # Should return None on error
            assert result is None

    @pytest.mark.unit
    def test_different_image_formats(self, temp_dir):
        """Test handling of supported image formats."""
        formats = [
            ("test.png", "image/png"),
            ("test.jpg", "image/jpeg"),
            ("test.jpeg", "image/jpeg"),
        ]

        for filename, expected_media_type in formats:
            test_img = temp_dir / filename
            img = Image.new("RGB", (50, 50), color="yellow")
            img.save(test_img)

            with patch("alicemultiverse.quality.claude.anthropic") as mock_anthropic:
                mock_client = Mock()
                mock_anthropic.Anthropic.return_value = mock_client

                mock_message = Mock()
                mock_message.content = [Mock(text="defects_found: false")]
                mock_message.usage.input_tokens = 100
                mock_message.usage.output_tokens = 50
                mock_client.messages.create.return_value = mock_message

                check_image_defects(str(test_img), "test-api-key")

                # Verify correct media type was used
                create_call = mock_client.messages.create.call_args
                image_content = create_call.kwargs["messages"][0]["content"][0]
                assert image_content["source"]["media_type"] == expected_media_type

    @pytest.mark.unit
    def test_parse_claude_response_variations(self):
        """Test parsing various response formats from Claude."""
        test_cases = [
            # Case 1: Well-structured response
            (
                """
defects_found: true
defect_count: 2
severity: high
confidence: 0.9

defects:
- Missing left eye
- Three arms visible
            """,
                {
                    "defects_found": True,
                    "defect_count": 2,
                    "severity": "high",
                    "confidence": 0.9,
                    "defects": ["missing left eye", "three arms visible"],
                },
            ),
            # Case 2: Bullet points with •
            (
                """
Defects Found: Yes
Severity: Medium
Confidence: 0.75

• Distorted facial features
• Unnatural hand position
• Background object phasing through subject
            """,
                {
                    "defects_found": True,
                    "severity": "medium",
                    "confidence": 0.75,
                    "defect_count": 3,
                    "defects": [
                        "distorted facial features",
                        "unnatural hand position",
                        "background object phasing through subject",
                    ],
                },
            ),
            # Case 3: No defects found
            (
                """
defects_found: no
severity: low
confidence: 1.0

The image appears to be well-generated without visible defects.
            """,
                {
                    "defects_found": False,
                    "defect_count": 0,
                    "severity": "low",
                    "confidence": 1.0,
                    "defects": [],
                },
            ),
            # Case 4: Malformed response (should handle gracefully)
            (
                """
I found some issues with the image but it's hard to quantify.
There might be problems with the hands.
            """,
                {
                    "defects_found": False,  # Default values
                    "defect_count": 0,
                    "severity": "low",
                    "confidence": 0.0,
                    "defects": [],
                },
            ),
        ]

        for response_text, expected in test_cases:
            result = _parse_claude_response(response_text)
            assert result["defects_found"] == expected["defects_found"]
            assert result["severity"] == expected["severity"]
            assert result["confidence"] == expected["confidence"]
            assert result["defect_count"] == expected["defect_count"]
            assert len(result["defects"]) == len(expected["defects"])
            # Check defects content (normalized to lowercase)
            for i, defect in enumerate(expected["defects"]):
                assert defect in result["defects"][i]

    @pytest.mark.unit
    def test_estimate_cost(self):
        """Test cost estimation for different models."""
        assert estimate_cost("claude-3-haiku-20240307") == 0.002
        assert estimate_cost("claude-3-sonnet-20240229") == 0.008
        assert estimate_cost("claude-3-opus-20240229") == 0.024
        assert estimate_cost("unknown-model") == 0.02  # Default

    @pytest.mark.unit
    def test_check_image_defects_with_custom_model(self, temp_dir):
        """Test using a custom model."""
        test_img = temp_dir / "test.png"
        img = Image.new("RGB", (100, 100), color="purple")
        img.save(test_img)

        with patch("alicemultiverse.quality.claude.anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.Anthropic.return_value = mock_client

            mock_message = Mock()
            mock_message.content = [Mock(text="defects_found: false")]
            mock_message.usage.input_tokens = 1500
            mock_message.usage.output_tokens = 300
            mock_client.messages.create.return_value = mock_message

            # Use Sonnet model
            result = check_image_defects(
                str(test_img), "test-api-key", model="claude-3-sonnet-20240229"
            )

            # Verify correct model was used
            create_call = mock_client.messages.create.call_args
            assert create_call.kwargs["model"] == "claude-3-sonnet-20240229"
            assert result["model"] == "claude-3-sonnet-20240229"


class TestClaudeStageIntegration:
    """Test Claude integration with pipeline stages."""

    @pytest.mark.unit
    def test_claude_stage_process(self, temp_dir):
        """Test ClaudeStage processing in pipeline."""
        from alicemultiverse.pipeline.stages import ClaudeStage

        # Create test image
        test_img = temp_dir / "test.png"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(test_img)

        # Mock check_image_defects
        with patch("alicemultiverse.quality.claude.check_image_defects") as mock_check:
            mock_check.return_value = {
                "defects_found": True,
                "defect_count": 2,
                "severity": "medium",
                "defects": ["anatomical error", "texture issue"],
                "confidence": 0.8,
                "raw_response": "mock response",
                "model": "claude-3-haiku-20240307",
                "tokens_used": 1200,
            }

            # Create stage
            stage = ClaudeStage(api_key="test-key", min_stars=4, model="claude-3-haiku-20240307")

            # Test metadata
            metadata = {
                "quality_stars": 5,
                "pipeline_stages": {
                    "brisque": {"passed": True, "score": 20.0},
                    "sightengine": {"passed": True, "quality_score": 0.9},
                },
            }

            # Process
            result = stage.process(test_img, metadata)

            # Verify the call
            mock_check.assert_called_once_with(str(test_img), "test-key", "claude-3-haiku-20240307")

            # Check result
            assert "claude" in result["pipeline_stages"]
            claude_result = result["pipeline_stages"]["claude"]
            assert claude_result["passed"] is True  # Even with defects, it passed
            assert claude_result["defects_found"] is True
            assert claude_result["defect_count"] == 2
            assert len(claude_result["defects"]) == 2
            assert claude_result["severity"] == "medium"
            assert claude_result["confidence"] == 0.8

    @pytest.mark.unit
    def test_claude_stage_should_process(self):
        """Test ClaudeStage should_process logic."""
        from alicemultiverse.pipeline.stages import ClaudeStage

        stage = ClaudeStage(api_key="test-key", min_stars=4)

        # Should process 4-5 star images
        assert stage.should_process({"quality_stars": 5, "media_type": MediaType.IMAGE}) is True
        assert stage.should_process({"quality_stars": 4, "media_type": MediaType.IMAGE}) is True
        assert stage.should_process({"quality_stars": 3, "media_type": MediaType.IMAGE}) is False
        assert stage.should_process({"quality_stars": 2, "media_type": MediaType.IMAGE}) is False
        assert stage.should_process({"quality_stars": 1, "media_type": MediaType.IMAGE}) is False

        # Should not process if no quality stars
        assert stage.should_process({"media_type": MediaType.IMAGE}) is False
        assert stage.should_process({"quality_stars": None, "media_type": MediaType.IMAGE}) is False

        # Should not process non-images
        assert stage.should_process({"quality_stars": 5, "media_type": MediaType.VIDEO}) is False
        assert stage.should_process({"quality_stars": 5}) is False  # No media type

    @pytest.mark.unit
    def test_claude_stage_cost(self):
        """Test ClaudeStage cost calculation."""
        from alicemultiverse.pipeline.stages import ClaudeStage

        # Test different models
        stage_haiku = ClaudeStage("key", model="claude-3-haiku-20240307")
        assert stage_haiku.get_cost() == 0.002

        stage_sonnet = ClaudeStage("key", model="claude-3-sonnet-20240229")
        assert stage_sonnet.get_cost() == 0.008

        stage_opus = ClaudeStage("key", model="claude-3-opus-20240229")
        assert stage_opus.get_cost() == 0.024
