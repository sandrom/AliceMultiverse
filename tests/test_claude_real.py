#!/usr/bin/env python3
"""Test Claude integration with real image but mocked API."""

from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

# Create a test image
test_dir = Path("test_output")
test_dir.mkdir(exist_ok=True)

img_path = test_dir / "test_ai_image.png"
img = Image.new("RGB", (512, 512), color="blue")
# Add some variation to make it more realistic
for x in range(0, 512, 32):
    for y in range(0, 512, 32):
        img.putpixel((x, y), (255, 0, 0))
img.save(img_path)

print(f"Created test image: {img_path}")

# Test the Claude integration
from alicemultiverse.quality.claude import check_image_defects

# Mock the anthropic client
with patch("alicemultiverse.quality.claude.anthropic") as mock_anthropic:
    # Setup mock client
    mock_client = Mock()
    mock_anthropic.Anthropic.return_value = mock_client

    # Mock successful response
    mock_message = Mock()
    mock_message.content = [
        Mock(
            text="""
defects_found: true
defect_count: 2
severity: medium
confidence: 0.85

defects:
- Unnatural texture pattern on surface
- Repetitive grid artifacts visible
    """
        )
    ]
    mock_message.usage.input_tokens = 1100
    mock_message.usage.output_tokens = 150

    mock_client.messages.create.return_value = mock_message

    # Call the function
    result = check_image_defects(str(img_path), "test-api-key")

    print("\nClaude Analysis Result:")
    print(f"Defects found: {result['defects_found']}")
    print(f"Defect count: {result['defect_count']}")
    print(f"Severity: {result['severity']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Defects: {result['defects']}")
    print(f"Tokens used: {result['tokens_used']}")

    # Verify the API was called correctly
    create_call = mock_client.messages.create.call_args
    print(f"\nAPI called with model: {create_call.kwargs['model']}")
    print(f"Max tokens: {create_call.kwargs['max_tokens']}")

    # Check image encoding
    messages = create_call.kwargs["messages"]
    image_content = messages[0]["content"][0]
    print(f"Image type: {image_content['type']}")
    print(f"Image encoding: {image_content['source']['type']}")
    print(f"Media type: {image_content['source']['media_type']}")
    print(f"Image data length: {len(image_content['source']['data'])} chars")

# Test with pipeline
print("\n" + "=" * 50)
print("Testing with Pipeline Stage")
print("=" * 50)

from alicemultiverse.core.types import MediaType
from alicemultiverse.pipeline.stages import ClaudeStage

# Create stage
stage = ClaudeStage(api_key="test-api-key", min_stars=4)

# Test metadata
metadata = {
    "quality_stars": 5,
    "media_type": MediaType.IMAGE,
    "brisque_score": 25.0,
    "sightengine_quality": 0.85,
    "pipeline_stages": {
        "brisque": {"passed": True, "score": 25.0},
        "sightengine": {"passed": True, "quality_score": 0.85},
    },
}

print(f"\nShould process? {stage.should_process(metadata)}")
print(f"Cost per image: ${stage.get_cost()}")

# Process with mocked API
with patch("alicemultiverse.quality.claude.check_image_defects") as mock_check:
    mock_check.return_value = {
        "defects_found": True,
        "defect_count": 1,
        "severity": "low",
        "defects": ["Minor texture inconsistency in background"],
        "confidence": 0.9,
        "raw_response": "test response",
        "model": "claude-3-haiku-20240307",
        "tokens_used": 1200,
    }

    # Process image
    result = stage.process(img_path, metadata)

    print(f"\nFinal quality stars: {result['quality_stars']}")
    print(f"Final combined score: {result['final_combined_score']:.3f}")
    print(f"Claude score: {result['claude_quality_score']:.3f}")

    # Check pipeline stages
    claude_stage = result["pipeline_stages"]["claude"]
    print("\nClaude stage results:")
    print(f"  Passed: {claude_stage['passed']}")
    print(f"  Defects found: {claude_stage['defects_found']}")
    print(f"  Defect count: {claude_stage['defect_count']}")
    print(f"  Severity: {claude_stage['severity']}")
    print(f"  Final stars: {claude_stage['final_stars']}")

# Clean up
img_path.unlink()
test_dir.rmdir()
print("\n✓ Test completed successfully!")
