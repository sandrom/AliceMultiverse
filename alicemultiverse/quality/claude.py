"""Claude API integration for AI defect detection."""

import base64
import logging
from pathlib import Path

import anthropic

from ..core.config import settings

logger = logging.getLogger(__name__)

# Prompt for Claude to detect AI-generated image defects
CLAUDE_PROMPT = """Analyze this AI-generated image for common defects and artifacts. Focus on:

1. Anatomical errors (extra fingers, merged limbs, impossible poses)
2. Facial distortions (asymmetry, unnatural features)
3. Texture inconsistencies (skin, fabric, materials)
4. Lighting and shadow errors
5. Background anomalies
6. Object coherence issues
7. Perspective and scale problems

Provide a structured response with:
- defects_found: true/false
- defect_count: number of defects found
- severity: low/medium/high
- defects: list of specific defects found
- confidence: your confidence level (0-1)

Be specific but concise. Focus only on actual defects, not artistic choices."""


def check_image_defects(
    image_path: str, api_key: str, model: str = None
) -> dict | None:
    """Check image for AI-generated defects using Claude.

    Args:
        image_path: Path to the image file
        api_key: Anthropic API key
        model: Claude model to use (default from settings)

    Returns:
        Analysis results dict or None if error
    """
    try:
        # Use model from settings if not specified
        if model is None:
            model = settings.providers.anthropic.default_model
            
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)

        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        # Determine media type
        image_path_obj = Path(image_path)
        ext = image_path_obj.suffix.lower()
        media_type_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
        media_type = media_type_map.get(ext, "image/jpeg")

        # Send to Claude
        message = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": CLAUDE_PROMPT},
                    ],
                }
            ],
        )

        # Parse response
        response_text = message.content[0].text

        # Try to parse structured response
        result = _parse_claude_response(response_text)
        result["raw_response"] = response_text
        result["model"] = model
        result["tokens_used"] = message.usage.input_tokens + message.usage.output_tokens

        return result

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


def _parse_claude_response(response_text: str) -> dict:
    """Parse Claude's response into structured data.

    Args:
        response_text: Raw response from Claude

    Returns:
        Parsed results dict
    """
    import re

    result = {
        "defects_found": False,
        "defect_count": 0,
        "severity": "low",
        "defects": [],
        "confidence": 0.0,
    }

    try:
        lines = response_text.lower().split("\n")

        for line in lines:
            line = line.strip()

            if "defects_found:" in line or "defects found:" in line:
                result["defects_found"] = "true" in line or "yes" in line

            elif "defect_count:" in line:
                # Extract number
                match = re.search(r"\d+", line)
                if match:
                    result["defect_count"] = int(match.group())

            elif "severity:" in line:
                if "high" in line:
                    result["severity"] = "high"
                elif "medium" in line:
                    result["severity"] = "medium"
                else:
                    result["severity"] = "low"

            elif "confidence:" in line:
                # Extract float
                match = re.search(r"[\d.]+", line)
                if match:
                    result["confidence"] = float(match.group())

            elif line.startswith("-") or line.startswith("•"):
                # Defect list item
                defect = line.lstrip("-•").strip()
                if defect and len(defect) > 5:  # Skip very short items
                    result["defects"].append(defect)

        # Ensure defect_count matches defects list
        if result["defects"] and result["defect_count"] == 0:
            result["defect_count"] = len(result["defects"])

        # Set defects_found based on defect_count
        if result["defect_count"] > 0:
            result["defects_found"] = True

    except Exception as e:
        logger.warning(f"Failed to parse Claude response: {e}")

    return result


def estimate_cost(model: str = "claude-3-haiku-20240307") -> float:
    """Estimate cost per image for Claude analysis.

    Args:
        model: Claude model name

    Returns:
        Estimated cost in USD
    """
    # Approximate costs as of 2024
    # Assuming ~1000 input tokens for image + prompt, ~200 output tokens
    costs = {
        "claude-3-haiku-20240307": 0.002,  # ~$0.25/$0.125 per 1M tokens
        "claude-3-sonnet-20240229": 0.008,  # ~$3/$1.5 per 1M tokens
        "claude-3-opus-20240229": 0.024,  # ~$15/$7.5 per 1M tokens
    }

    return costs.get(model, 0.02)  # Default to ~2 cents
