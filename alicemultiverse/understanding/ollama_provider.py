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

    @property
    def supports_batch(self) -> bool:
        return False  # Process one at a time for local models

    async def check_availability(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if Ollama is running
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        logger.warning("Ollama not running or not accessible")
                        return False

                    data = await response.json()
                    available_models = [m["name"] for m in data.get("models", [])]

                    if self.model not in available_models:
                        logger.warning(f"Model {self.model} not found. Available: {available_models}")
                        return False

                    return True

        except Exception as e:
            logger.error(f"Failed to check Ollama availability: {e}")
            return False

    async def analyze(
        self,
        image_path: Path,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        detailed: bool = False,
        custom_instructions: str | None = None
    ) -> ImageAnalysisResult:
        """Analyze image using local Ollama model."""
        # Check availability first
        if not await self.check_availability():
            raise RuntimeError(f"Ollama not available or model {self.model} not found")

        # Read and encode image
        image_base64 = self._encode_image(image_path)

        # Build prompt based on requirements
        prompt_parts = []

        if extract_tags:
            prompt_parts.append(
                "Analyze this image and provide tags describing:\n"
                "- Objects and subjects\n"
                "- Scene and setting\n"
                "- Colors and lighting\n"
                "- Style and mood\n"
                "- Any text visible\n"
                "Format: Provide comma-separated tags."
            )

        if generate_prompt:
            prompt_parts.append(
                "\nAlso provide a detailed description suitable for image generation."
            )

        if detailed:
            prompt_parts.append(
                "\nInclude technical details about composition, lighting, and artistic style."
            )

        if custom_instructions:
            prompt_parts.append(f"\nAdditional instructions: {custom_instructions}")

        prompt = "\n".join(prompt_parts)

        try:
            async with aiohttp.ClientSession() as session:
                # Prepare request
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_base64],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent results
                        "top_p": 0.9
                    }
                }

                # Make request
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama API error: {response.status} - {error_text}")

                    result = await response.json()

            # Parse response
            content = result.get("response", "")

            # Extract tags
            tags = []
            description = ""

            if extract_tags and "tags" in content.lower():
                # Look for tags section
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'tags' in line.lower() and ':' in line:
                        # Get the tags from this line or the next
                        tag_text = line.split(':', 1)[1].strip()
                        if not tag_text and i + 1 < len(lines):
                            tag_text = lines[i + 1].strip()

                        # Parse comma-separated tags
                        if tag_text:
                            tags = [t.strip().lower() for t in tag_text.split(',') if t.strip()]
                        break

            # Extract description
            if generate_prompt:
                # Look for description section or use full content
                if "description" in content.lower():
                    desc_start = content.lower().find("description")
                    desc_text = content[desc_start:].split('\n', 2)
                    if len(desc_text) > 1:
                        description = desc_text[1].strip()
                else:
                    # Use first substantial paragraph as description
                    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                    if paragraphs:
                        description = paragraphs[0]

            # If we didn't parse structured output, extract from freeform text
            if not tags and extract_tags:
                # Extract noun phrases as tags
                import re
                words = re.findall(r'\b[a-z]+\b', content.lower())
                # Common objects/concepts that might be tags
                tag_candidates = [
                    'portrait', 'landscape', 'person', 'woman', 'man', 'child',
                    'sunset', 'sunrise', 'night', 'day', 'nature', 'city',
                    'abstract', 'realistic', 'digital', 'painting', 'photo',
                    'colorful', 'monochrome', 'dark', 'bright', 'vibrant'
                ]
                tags = [w for w in words if w in tag_candidates][:10]

            # Get model info
            model_info = self.VISION_MODELS.get(self.model, {})

            return ImageAnalysisResult(
                description=description or content[:500],
                tags=tags,
                custom_tags=[],
                technical_details={
                    "model": self.model,
                    "model_type": "local",
                    "capabilities": model_info.get("capabilities", []),
                    "processing_time": result.get("total_duration", 0) / 1e9  # Convert to seconds
                },
                provider=self.name,
                model=self.model,
                cost=0.0,  # Local models are free!
                raw_response=content,
                confidence_score=0.8 if tags else 0.6  # Lower confidence for local models
            )

        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            raise

    def estimate_cost(self, detailed: bool = False) -> float:
        """Estimate cost of analysis (always 0 for local models)."""
        return 0.0

    @classmethod
    def get_recommended_model(cls, use_case: str = "general") -> str:
        """Get recommended model for specific use case.
        
        Args:
            use_case: One of "general", "fast", "quality", "text"
            
        Returns:
            Model name
        """
        recommendations = {
            "general": "llava:latest",
            "fast": "llava-phi3:latest",
            "quality": "llava:13b",
            "text": "llava:13b"  # Better at OCR
        }
        return recommendations.get(use_case, "llava:latest")

    async def pull_model(self, model: str | None = None) -> bool:
        """Pull/download a model if not available.
        
        Args:
            model: Model to pull (default: self.model)
            
        Returns:
            True if successful
        """
        model = model or self.model

        try:
            async with aiohttp.ClientSession() as session:
                payload = {"name": model}

                async with session.post(
                    f"{self.base_url}/api/pull",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=3600)  # 1 hour for large models
                ) as response:
                    if response.status != 200:
                        return False

                    # Stream progress
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "status" in data:
                                    logger.info(f"Pull progress: {data['status']}")
                            except (json.JSONDecodeError, KeyError):
                                pass

                    return True

        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False
