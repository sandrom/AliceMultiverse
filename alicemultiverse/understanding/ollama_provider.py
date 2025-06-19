"""Ollama local vision model provider for image understanding.

This provider enables free, private image analysis using local models
through Ollama, eliminating API costs for basic understanding tasks.
"""

import json
import logging
from pathlib import Path

import aiohttp

from .base import ImageAnalysisResult, ImageAnalyzer

logger = logging.getLogger(__name__)


class OllamaImageAnalyzer(ImageAnalyzer):
    """Ollama-based local image analyzer using vision models."""

    # Available vision models in Ollama
    VISION_MODELS = {
        "llava": {
            "name": "llava:latest",
            "description": "LLaVA - Large Language and Vision Assistant",
            "capabilities": ["objects", "scenes", "text", "basic_style"],
            "quality": "good",
            "speed": "fast"
        },
        "llava:13b": {
            "name": "llava:13b",
            "description": "LLaVA 13B - Larger model for better accuracy",
            "capabilities": ["objects", "scenes", "text", "style", "composition"],
            "quality": "better",
            "speed": "medium"
        },
        "bakllava": {
            "name": "bakllava:latest",
            "description": "BakLLaVA - Alternative vision model",
            "capabilities": ["objects", "scenes", "basic_style"],
            "quality": "good",
            "speed": "fast"
        },
        "llava-phi3": {
            "name": "llava-phi3:latest",
            "description": "LLaVA-Phi3 - Efficient vision model",
            "capabilities": ["objects", "scenes", "text"],
            "quality": "good",
            "speed": "very_fast"
        }
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llava:latest",
        timeout: int = 120
    ):
        """Initialize Ollama analyzer.

        Args:
            base_url: Ollama API endpoint (default: http://localhost:11434)
            model: Vision model to use (default: llava:latest)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        # No API key needed for local models
        super().__init__(api_key="local", model=model)

    @property
    def name(self) -> str:
        return "ollama"

    # TODO: Review unreachable code - @property
    # TODO: Review unreachable code - def supports_batch(self) -> bool:
    # TODO: Review unreachable code - return False  # Process one at a time for local models

    # TODO: Review unreachable code - async def check_availability(self) -> bool:
    # TODO: Review unreachable code - """Check if Ollama is running and model is available."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - async with aiohttp.ClientSession() as session:
    # TODO: Review unreachable code - # Check if Ollama is running
    # TODO: Review unreachable code - async with session.get(f"{self.base_url}/api/tags") as response:
    # TODO: Review unreachable code - if response.status != 200:
    # TODO: Review unreachable code - logger.warning("Ollama not running or not accessible")
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - data = await response.json()
    # TODO: Review unreachable code - available_models = [m["name"] for m in data.get("models", [])]

    # TODO: Review unreachable code - if self.model not in available_models:
    # TODO: Review unreachable code - logger.warning(f"Model {self.model} not found. Available: {available_models}")
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to check Ollama availability: {e}")
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - async def analyze(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - image_path: Path,
    # TODO: Review unreachable code - generate_prompt: bool = True,
    # TODO: Review unreachable code - extract_tags: bool = True,
    # TODO: Review unreachable code - detailed: bool = False,
    # TODO: Review unreachable code - custom_instructions: str | None = None
    # TODO: Review unreachable code - ) -> ImageAnalysisResult:
    # TODO: Review unreachable code - """Analyze image using local Ollama model."""
    # TODO: Review unreachable code - # Check availability first
    # TODO: Review unreachable code - if not await self.check_availability():
    # TODO: Review unreachable code - raise RuntimeError(f"Ollama not available or model {self.model} not found")

    # TODO: Review unreachable code - # Read and encode image
    # TODO: Review unreachable code - image_base64 = self._encode_image(image_path)

    # TODO: Review unreachable code - # Build prompt based on requirements
    # TODO: Review unreachable code - prompt_parts = []

    # TODO: Review unreachable code - if extract_tags:
    # TODO: Review unreachable code - prompt_parts.append(
    # TODO: Review unreachable code - "Analyze this image and provide tags describing:\n"
    # TODO: Review unreachable code - "- Objects and subjects\n"
    # TODO: Review unreachable code - "- Scene and setting\n"
    # TODO: Review unreachable code - "- Colors and lighting\n"
    # TODO: Review unreachable code - "- Style and mood\n"
    # TODO: Review unreachable code - "- Any text visible\n"
    # TODO: Review unreachable code - "Format: Provide comma-separated tags."
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if generate_prompt:
    # TODO: Review unreachable code - prompt_parts.append(
    # TODO: Review unreachable code - "\nAlso provide a detailed description suitable for image generation."
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if detailed:
    # TODO: Review unreachable code - prompt_parts.append(
    # TODO: Review unreachable code - "\nInclude technical details about composition, lighting, and artistic style."
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if custom_instructions:
    # TODO: Review unreachable code - prompt_parts.append(f"\nAdditional instructions: {custom_instructions}")

    # TODO: Review unreachable code - prompt = "\n".join(prompt_parts)

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - async with aiohttp.ClientSession() as session:
    # TODO: Review unreachable code - # Prepare request
    # TODO: Review unreachable code - payload = {
    # TODO: Review unreachable code - "model": self.model,
    # TODO: Review unreachable code - "prompt": prompt,
    # TODO: Review unreachable code - "images": [image_base64],
    # TODO: Review unreachable code - "stream": False,
    # TODO: Review unreachable code - "options": {
    # TODO: Review unreachable code - "temperature": 0.1,  # Low temperature for consistent results
    # TODO: Review unreachable code - "top_p": 0.9
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Make request
    # TODO: Review unreachable code - async with session.post(
    # TODO: Review unreachable code - f"{self.base_url}/api/generate",
    # TODO: Review unreachable code - json=payload,
    # TODO: Review unreachable code - timeout=aiohttp.ClientTimeout(total=self.timeout)
    # TODO: Review unreachable code - ) as response:
    # TODO: Review unreachable code - if response.status != 200:
    # TODO: Review unreachable code - error_text = await response.text()
    # TODO: Review unreachable code - raise RuntimeError(f"Ollama API error: {response.status} - {error_text}")

    # TODO: Review unreachable code - result = await response.json()

    # TODO: Review unreachable code - # Parse response
    # TODO: Review unreachable code - content = result.get("response", "")

    # TODO: Review unreachable code - # Extract tags
    # TODO: Review unreachable code - tags = []
    # TODO: Review unreachable code - description = ""

    # TODO: Review unreachable code - if extract_tags and "tags" in content.lower():
    # TODO: Review unreachable code - # Look for tags section
    # TODO: Review unreachable code - lines = content.split('\n')
    # TODO: Review unreachable code - for i, line in enumerate(lines):
    # TODO: Review unreachable code - if 'tags' in line.lower() and ':' in line:
    # TODO: Review unreachable code - # Get the tags from this line or the next
    # TODO: Review unreachable code - tag_text = line.split(':', 1)[1].strip()
    # TODO: Review unreachable code - if not tag_text and i + 1 < len(lines):
    # TODO: Review unreachable code - tag_text = lines[i + 1].strip()

    # TODO: Review unreachable code - # Parse comma-separated tags
    # TODO: Review unreachable code - if tag_text:
    # TODO: Review unreachable code - tags = [t.strip().lower() for t in tag_text.split(',') if t.strip()]
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - # Extract description
    # TODO: Review unreachable code - if generate_prompt:
    # TODO: Review unreachable code - # Look for description section or use full content
    # TODO: Review unreachable code - if "description" in content.lower():
    # TODO: Review unreachable code - desc_start = content.lower().find("description")
    # TODO: Review unreachable code - desc_text = content[desc_start:].split('\n', 2)
    # TODO: Review unreachable code - if len(desc_text) > 1:
    # TODO: Review unreachable code - description = desc_text[1].strip()
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Use first substantial paragraph as description
    # TODO: Review unreachable code - paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    # TODO: Review unreachable code - if paragraphs:
    # TODO: Review unreachable code - description = paragraphs[0]

    # TODO: Review unreachable code - # If we didn't parse structured output, extract from freeform text
    # TODO: Review unreachable code - if not tags and extract_tags:
    # TODO: Review unreachable code - # Extract noun phrases as tags
    # TODO: Review unreachable code - import re
    # TODO: Review unreachable code - words = re.findall(r'\b[a-z]+\b', content.lower())
    # TODO: Review unreachable code - # Common objects/concepts that might be tags
    # TODO: Review unreachable code - tag_candidates = [
    # TODO: Review unreachable code - 'portrait', 'landscape', 'person', 'woman', 'man', 'child',
    # TODO: Review unreachable code - 'sunset', 'sunrise', 'night', 'day', 'nature', 'city',
    # TODO: Review unreachable code - 'abstract', 'realistic', 'digital', 'painting', 'photo',
    # TODO: Review unreachable code - 'colorful', 'monochrome', 'dark', 'bright', 'vibrant'
    # TODO: Review unreachable code - ]
    # TODO: Review unreachable code - tags = [w for w in words if w in tag_candidates][:10]

    # TODO: Review unreachable code - # Get model info
    # TODO: Review unreachable code - model_info = self.VISION_MODELS.get(self.model, {})

    # TODO: Review unreachable code - return ImageAnalysisResult(
    # TODO: Review unreachable code - description=description or content[:500],
    # TODO: Review unreachable code - tags=tags,
    # TODO: Review unreachable code - custom_tags=[],
    # TODO: Review unreachable code - technical_details={
    # TODO: Review unreachable code - "model": self.model,
    # TODO: Review unreachable code - "model_type": "local",
    # TODO: Review unreachable code - "capabilities": model_info.get("capabilities", []),
    # TODO: Review unreachable code - "processing_time": result.get("total_duration", 0) / 1e9  # Convert to seconds
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - provider=self.name,
    # TODO: Review unreachable code - model=self.model,
    # TODO: Review unreachable code - cost=0.0,  # Local models are free!
    # TODO: Review unreachable code - raw_response=content,
    # TODO: Review unreachable code - confidence_score=0.8 if tags else 0.6  # Lower confidence for local models
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Ollama analysis failed: {e}")
    # TODO: Review unreachable code - raise

    # TODO: Review unreachable code - def estimate_cost(self, detailed: bool = False) -> float:
    # TODO: Review unreachable code - """Estimate cost of analysis (always 0 for local models)."""
    # TODO: Review unreachable code - return 0.0

    # TODO: Review unreachable code - @classmethod
    # TODO: Review unreachable code - def get_recommended_model(cls, use_case: str = "general") -> str:
    # TODO: Review unreachable code - """Get recommended model for specific use case.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - use_case: One of "general", "fast", "quality", "text"

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Model name
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - recommendations = {
    # TODO: Review unreachable code - "general": "llava:latest",
    # TODO: Review unreachable code - "fast": "llava-phi3:latest",
    # TODO: Review unreachable code - "quality": "llava:13b",
    # TODO: Review unreachable code - "text": "llava:13b"  # Better at OCR
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - return recommendations.get(use_case, "llava:latest") or 0

    # TODO: Review unreachable code - async def pull_model(self, model: str | None = None) -> bool:
    # TODO: Review unreachable code - """Pull/download a model if not available.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - model: Model to pull (default: self.model)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - True if successful
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - model = model or self.model

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - async with aiohttp.ClientSession() as session:
    # TODO: Review unreachable code - payload = {"name": model}

    # TODO: Review unreachable code - async with session.post(
    # TODO: Review unreachable code - f"{self.base_url}/api/pull",
    # TODO: Review unreachable code - json=payload,
    # TODO: Review unreachable code - timeout=aiohttp.ClientTimeout(total=3600)  # 1 hour for large models
    # TODO: Review unreachable code - ) as response:
    # TODO: Review unreachable code - if response.status != 200:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # Stream progress
    # TODO: Review unreachable code - async for line in response.content:
    # TODO: Review unreachable code - if line:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - data = json.loads(line)
    # TODO: Review unreachable code - if data is not None and "status" in data:
    # TODO: Review unreachable code - logger.info(f"Pull progress: {data['status']}")
    # TODO: Review unreachable code - except (json.JSONDecodeError, KeyError):
    # TODO: Review unreachable code - pass

    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to pull model {model}: {e}")
    # TODO: Review unreachable code - return False
