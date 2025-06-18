"""Image understanding provider implementations."""

import base64
import json
import logging
import os
from pathlib import Path

import aiohttp

from .base import ImageAnalysisResult, ImageAnalyzer

logger = logging.getLogger(__name__)


class AnthropicImageAnalyzer(ImageAnalyzer):
    """Anthropic Claude-based image analyzer."""

    BASE_URL = "https://api.anthropic.com/v1/messages"

    # Model pricing (per million tokens)
    PRICING = {
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Anthropic analyzer."""
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key required")
        super().__init__(api_key, model)

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def supports_batch(self) -> bool:
        return False

    async def analyze(
        self,
        image_path: Path,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        detailed: bool = False,
        custom_instructions: str | None = None
    ) -> ImageAnalysisResult:
        """Analyze image using Claude."""
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        # Determine media type
        suffix = image_path.suffix.lower()
        media_type = "image/jpeg"
        if suffix == ".png":
            media_type = "image/png"
        elif suffix == ".webp":
            media_type = "image/webp"
        elif suffix == ".gif":
            media_type = "image/gif"

        # Build the prompt
        prompt_parts = []

        if detailed:
            prompt_parts.append("Provide a detailed analysis of this image.")
        else:
            prompt_parts.append("Analyze this image.")

        if extract_tags:
            prompt_parts.append("""
Extract semantic tags in the following categories:
- style: artistic style, rendering style, visual style
- mood: emotional tone, atmosphere, feeling
- subject: main subjects, people, objects
- color: color palette, color mood, dominant colors
- technical: camera settings, composition, lighting
- fashion: clothing, accessories, style
- hair: hair color, style, length
- pose: body position, expression
- setting: location, environment, time of day
- action: what's happening, activities
- genre: type of image (portrait, landscape, etc)

Format tags as JSON: {"category": ["tag1", "tag2"]}
""")

        if generate_prompt:
            prompt_parts.append("""
Generate a detailed prompt that could recreate this image.
Also suggest a negative prompt for what to avoid.
Format as:
PROMPT: <positive prompt>
NEGATIVE: <negative prompt>
""")

        if custom_instructions:
            prompt_parts.append(f"\nAdditional instructions: {custom_instructions}")

        prompt = "\n\n".join(prompt_parts)

        # Make API request
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            payload = {
                "model": self.model,
                "max_tokens": 2000 if detailed else 1000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            }

            async with session.post(
                self.BASE_URL,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error: {response.status} - {error_text}")

                data = await response.json()
                content = data["content"][0]["text"]
                usage = data.get("usage", {})

        # Parse the response
        result = ImageAnalysisResult(
            description=content.split("\n")[0] if not detailed else content,
            provider=self.name,
            model=self.model,
            raw_response=data,
            tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        )

        # Extract structured data from response
        if extract_tags:
            # Look for JSON in response
            import re
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                try:
                    result.tags = json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Failed to parse tags JSON")

        if generate_prompt:
            # Extract prompts
            prompt_match = re.search(r'PROMPT:\s*(.+?)(?=NEGATIVE:|$)', content, re.DOTALL)
            negative_match = re.search(r'NEGATIVE:\s*(.+?)$', content, re.DOTALL)

            if prompt_match:
                result.generated_prompt = prompt_match.group(1).strip()
            if negative_match:
                result.negative_prompt = negative_match.group(1).strip()

        # Calculate cost
        if self.model in self.PRICING:
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            pricing = self.PRICING[self.model]
            result.cost = (
                (input_tokens * pricing["input"] / 1_000_000) +
                (output_tokens * pricing["output"] / 1_000_000)
            )

        return result

    def estimate_cost(self, detailed: bool = False) -> float:
        """Estimate cost based on average tokens."""
        # Rough estimates
        avg_input_tokens = 1500  # Image + prompt
        avg_output_tokens = 500 if detailed else 300

        if self.model in self.PRICING:
            pricing = self.PRICING[self.model]
            return (
                (avg_input_tokens * pricing["input"] / 1_000_000) +
                (avg_output_tokens * pricing["output"] / 1_000_000)
            )
        return 0.01  # Default estimate


class OpenAIImageAnalyzer(ImageAnalyzer):
    """OpenAI GPT-4 Vision-based image analyzer."""

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    # Pricing (per million tokens)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    }

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        """Initialize OpenAI analyzer."""
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        super().__init__(api_key, model)

    @property
    def name(self) -> str:
        return "openai"

    @property
    def supports_batch(self) -> bool:
        return True  # Via batch API

    async def analyze(
        self,
        image_path: Path,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        detailed: bool = False,
        custom_instructions: str | None = None
    ) -> ImageAnalysisResult:
        """Analyze image using GPT-4 Vision."""
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        # Build the prompt
        system_prompt = "You are an expert at analyzing images and extracting detailed information."

        user_prompt_parts = []
        if detailed:
            user_prompt_parts.append("Provide a comprehensive analysis of this image.")
        else:
            user_prompt_parts.append("Analyze this image concisely.")

        if extract_tags:
            user_prompt_parts.append("""
Extract semantic tags and return them as a JSON object with these categories:
style, mood, subject, color, technical, fashion, hair, pose, setting,
camera, art_movement, emotion, composition, texture, weather, action,
gender, age_group, accessories, time_period, genre

Only include relevant categories. Format: {"category": ["tag1", "tag2"]}
""")

        if generate_prompt:
            user_prompt_parts.append("""
Generate:
1. A detailed prompt to recreate this image
2. A negative prompt for things to avoid

Format:
PROMPT: <detailed positive prompt>
NEGATIVE: <negative prompt>
""")

        if custom_instructions:
            user_prompt_parts.append(custom_instructions)

        user_prompt = "\n\n".join(user_prompt_parts)

        # Make API request
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high" if detailed else "low"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000 if detailed else 1000,
            }

            async with session.post(
                self.BASE_URL,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")

                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

        # Parse response
        result = ImageAnalysisResult(
            description=content.split("\n")[0] if not detailed else content,
            provider=self.name,
            model=self.model,
            raw_response=data,
            tokens_used=usage.get("total_tokens", 0)
        )

        # Extract structured data
        if extract_tags:
            import re
            # Find JSON block
            json_match = re.search(r'\{[^{}]+\}', content, re.DOTALL)
            if json_match:
                try:
                    result.tags = json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Failed to parse tags JSON from OpenAI")

        if generate_prompt:
            # Extract prompts
            import re
            prompt_match = re.search(r'PROMPT:\s*(.+?)(?=NEGATIVE:|$)', content, re.DOTALL | re.IGNORECASE)
            negative_match = re.search(r'NEGATIVE:\s*(.+?)$', content, re.DOTALL | re.IGNORECASE)

            if prompt_match:
                result.generated_prompt = prompt_match.group(1).strip()
            if negative_match:
                result.negative_prompt = negative_match.group(1).strip()

        # Calculate cost
        if self.model in self.PRICING:
            tokens = usage.get("total_tokens", 0)
            # Rough split between input/output
            input_tokens = int(tokens * 0.7)
            output_tokens = tokens - input_tokens
            pricing = self.PRICING[self.model]
            result.cost = (
                (input_tokens * pricing["input"] / 1_000_000) +
                (output_tokens * pricing["output"] / 1_000_000)
            )

        return result

    def estimate_cost(self, detailed: bool = False) -> float:
        """Estimate cost."""
        avg_tokens = 2000 if detailed else 1000

        if self.model in self.PRICING:
            # Assume 70% input, 30% output
            pricing = self.PRICING[self.model]
            return (
                (avg_tokens * 0.7 * pricing["input"] / 1_000_000) +
                (avg_tokens * 0.3 * pricing["output"] / 1_000_000)
            )
        return 0.001


class GoogleAIImageAnalyzer(ImageAnalyzer):
    """Google AI (Gemini) image analyzer."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    # Free tier limits, then pricing
    PRICING = {
        "gemini-1.5-flash": {"free_rpm": 15, "free_tpd": 1_500_000, "cost_per_million": 0.075},
        "gemini-1.5-flash-8b": {"free_rpm": 15, "free_tpd": 1_500_000, "cost_per_million": 0.0375},
        "gemini-1.5-pro": {"free_rpm": 2, "free_tpd": 50_000, "cost_per_million": 1.25},
    }

    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        """Initialize Google AI analyzer."""
        api_key = api_key or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Google AI API key required")
        super().__init__(api_key, model)

    @property
    def name(self) -> str:
        return "google"

    @property
    def supports_batch(self) -> bool:
        return False

    async def analyze(
        self,
        image_path: Path,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        detailed: bool = False,
        custom_instructions: str | None = None
    ) -> ImageAnalysisResult:
        """Analyze image using Gemini."""
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        # Determine MIME type
        suffix = image_path.suffix.lower()
        mime_type = "image/jpeg"
        if suffix == ".png":
            mime_type = "image/png"
        elif suffix == ".webp":
            mime_type = "image/webp"

        # Build prompt
        prompt_parts = []
        if detailed:
            prompt_parts.append("Provide a detailed, comprehensive analysis of this image.")
        else:
            prompt_parts.append("Analyze this image.")

        if extract_tags:
            prompt_parts.append("""
Extract semantic tags in JSON format with these categories:
{
  "style": ["artistic style tags"],
  "mood": ["emotional/atmosphere tags"],
  "subject": ["main subjects"],
  "color": ["color-related tags"],
  "technical": ["photography/technical tags"],
  "fashion": ["clothing/fashion tags"],
  "setting": ["location/environment tags"],
  "composition": ["compositional elements"],
  "genre": ["image genre/type"]
}
Include only relevant categories.""")

        if generate_prompt:
            prompt_parts.append("""
Generate:
PROMPT: A detailed prompt to recreate this image
NEGATIVE: Things to avoid""")

        if custom_instructions:
            prompt_parts.append(custom_instructions)

        prompt = "\n\n".join(prompt_parts)

        # Make API request
        url = self.BASE_URL.format(model=self.model)

        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
            }

            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 2048 if detailed else 1024,
                }
            }

            async with session.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Google AI API error: {response.status} - {error_text}")

                data = await response.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                usage_metadata = data.get("usageMetadata", {})

        # Parse response
        result = ImageAnalysisResult(
            description=content.split("\n")[0] if not detailed else content,
            provider=self.name,
            model=self.model,
            raw_response=data,
            tokens_used=usage_metadata.get("totalTokenCount", 0)
        )

        # Extract structured data
        if extract_tags:
            import re
            # Find JSON block
            json_match = re.search(r'\{[^{}]+\}', content, re.DOTALL)
            if json_match:
                try:
                    result.tags = json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Failed to parse tags JSON from Gemini")

        if generate_prompt:
            # Extract prompts
            import re
            prompt_match = re.search(r'PROMPT:\s*(.+?)(?=NEGATIVE:|$)', content, re.DOTALL | re.IGNORECASE)
            negative_match = re.search(r'NEGATIVE:\s*(.+?)$', content, re.DOTALL | re.IGNORECASE)

            if prompt_match:
                result.generated_prompt = prompt_match.group(1).strip()
            if negative_match:
                result.negative_prompt = negative_match.group(1).strip()

        # Calculate cost (after free tier)
        if self.model in self.PRICING:
            tokens = usage_metadata.get("totalTokenCount", 0)
            pricing = self.PRICING[self.model]
            # Simplified - doesn't account for free tier
            result.cost = tokens * pricing["cost_per_million"] / 1_000_000

        return result

    def estimate_cost(self, detailed: bool = False) -> float:
        """Estimate cost."""
        avg_tokens = 2000 if detailed else 1000

        if self.model in self.PRICING:
            pricing = self.PRICING[self.model]
            # Note: This doesn't account for free tier
            return avg_tokens * pricing["cost_per_million"] / 1_000_000
        return 0.0001


class DeepSeekImageAnalyzer(ImageAnalyzer):
    """DeepSeek R1 image analyzer - very cost effective."""

    BASE_URL = "https://api.deepseek.com/v1/chat/completions"

    # DeepSeek pricing is very competitive
    PRICING = {
        "deepseek-reasoner": {"input": 0.55, "output": 2.19},  # Per million tokens
        "deepseek-chat": {"input": 0.27, "output": 1.10},
    }

    def __init__(self, api_key: str | None = None, model: str = "deepseek-reasoner"):
        """Initialize DeepSeek analyzer."""
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DeepSeek API key required")
        super().__init__(api_key, model)

    @property
    def name(self) -> str:
        return "deepseek"

    @property
    def supports_batch(self) -> bool:
        return False

    async def analyze(
        self,
        image_path: Path,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        detailed: bool = False,
        custom_instructions: str | None = None
    ) -> ImageAnalysisResult:
        """Analyze image using DeepSeek."""
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        # Build prompt
        prompt_parts = []
        if detailed:
            prompt_parts.append("Analyze this image in detail, describing all important aspects.")
        else:
            prompt_parts.append("Analyze this image concisely.")

        if extract_tags:
            prompt_parts.append("""
Extract semantic tags as a JSON object:
{
  "style": ["visual/artistic style"],
  "mood": ["emotional tone"],
  "subject": ["main subjects"],
  "color": ["color descriptors"],
  "technical": ["camera/technical aspects"],
  "fashion": ["clothing/accessories"],
  "setting": ["location/environment"],
  "action": ["activities/poses"],
  "composition": ["compositional elements"]
}
""")

        if generate_prompt:
            prompt_parts.append("""
Create:
PROMPT: Detailed prompt to recreate this image
NEGATIVE: Elements to avoid""")

        if custom_instructions:
            prompt_parts.append(custom_instructions)

        prompt = "\n\n".join(prompt_parts)

        # Make API request
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000 if detailed else 1000,
                "temperature": 0.7,
            }

            async with session.post(
                self.BASE_URL,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"DeepSeek API error: {response.status} - {error_text}")

                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

        # Parse response
        result = ImageAnalysisResult(
            description=content.split("\n")[0] if not detailed else content,
            provider=self.name,
            model=self.model,
            raw_response=data,
            tokens_used=usage.get("total_tokens", 0)
        )

        # Extract structured data
        if extract_tags:
            import re
            json_match = re.search(r'\{[^{}]+\}', content, re.DOTALL)
            if json_match:
                try:
                    result.tags = json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Failed to parse tags JSON from DeepSeek")

        if generate_prompt:
            import re
            prompt_match = re.search(r'PROMPT:\s*(.+?)(?=NEGATIVE:|$)', content, re.DOTALL | re.IGNORECASE)
            negative_match = re.search(r'NEGATIVE:\s*(.+?)$', content, re.DOTALL | re.IGNORECASE)

            if prompt_match:
                result.generated_prompt = prompt_match.group(1).strip()
            if negative_match:
                result.negative_prompt = negative_match.group(1).strip()

        # Calculate cost
        if self.model in self.PRICING:
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            pricing = self.PRICING[self.model]
            result.cost = (
                (input_tokens * pricing["input"] / 1_000_000) +
                (output_tokens * pricing["output"] / 1_000_000)
            )

        return result

    def estimate_cost(self, detailed: bool = False) -> float:
        """Estimate cost - DeepSeek is very affordable."""
        avg_input_tokens = 1000  # Image + prompt
        avg_output_tokens = 500 if detailed else 300

        if self.model in self.PRICING:
            pricing = self.PRICING[self.model]
            return (
                (avg_input_tokens * pricing["input"] / 1_000_000) +
                (avg_output_tokens * pricing["output"] / 1_000_000)
            )
        return 0.0005  # Very low default
