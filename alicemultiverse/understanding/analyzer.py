"""Main image analyzer that coordinates between providers."""

import asyncio
import logging
from pathlib import Path
from typing import Any

# Complex cost tracking removed - simple cost tracking in results is sufficient
from .base import ImageAnalysisResult
from .ollama_provider import OllamaImageAnalyzer
from .providers import (
    AnthropicImageAnalyzer,
    DeepSeekImageAnalyzer,
    GoogleAIImageAnalyzer,
    OpenAIImageAnalyzer,
)

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """Unified image analyzer supporting multiple providers."""

    PROVIDERS = {
        "anthropic": AnthropicImageAnalyzer,
        "openai": OpenAIImageAnalyzer,
        "google": GoogleAIImageAnalyzer,
        "deepseek": DeepSeekImageAnalyzer,
        "ollama": OllamaImageAnalyzer,
    }

    def __init__(self):
        """Initialize the analyzer."""
        self.analyzers = {}
        self._initialize_available_analyzers()

    def _initialize_available_analyzers(self):
        """Initialize analyzers for which we have API keys."""
        import os

        from ..core.keys.manager import APIKeyManager

        # Initialize key manager
        key_manager = APIKeyManager()

        # Try to load API keys from keychain/config and set in environment
        anthropic_key = key_manager.get_api_key("anthropic_api_key")
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key

        openai_key = key_manager.get_api_key("openai")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key

        google_key = key_manager.get_api_key("google")
        if google_key:
            os.environ["GOOGLE_AI_API_KEY"] = google_key
            os.environ["GEMINI_API_KEY"] = google_key

        deepseek_key = key_manager.get_api_key("deepseek")
        if deepseek_key:
            os.environ["DEEPSEEK_API_KEY"] = deepseek_key

        # Check for API keys and initialize available analyzers
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.analyzers["anthropic"] = AnthropicImageAnalyzer()
                logger.info("Initialized Anthropic image analyzer")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic analyzer: {e}")

        if os.getenv("OPENAI_API_KEY"):
            try:
                self.analyzers["openai"] = OpenAIImageAnalyzer()
                logger.info("Initialized OpenAI image analyzer")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI analyzer: {e}")

        if os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY"):
            try:
                self.analyzers["google"] = GoogleAIImageAnalyzer()
                logger.info("Initialized Google AI image analyzer")
            except Exception as e:
                logger.warning(f"Failed to initialize Google AI analyzer: {e}")

        if os.getenv("DEEPSEEK_API_KEY"):
            try:
                self.analyzers["deepseek"] = DeepSeekImageAnalyzer()
                logger.info("Initialized DeepSeek image analyzer")
            except Exception as e:
                logger.warning(f"Failed to initialize DeepSeek analyzer: {e}")

        # Always try to initialize Ollama (no API key needed)
        try:
            self.analyzers["ollama"] = OllamaImageAnalyzer()
            logger.info("Initialized Ollama local image analyzer")
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")

    def add_analyzer(self, name: str, api_key: str, model: str | None = None):
        """Add a specific analyzer.

        Args:
            name: Provider name
            api_key: API key for the provider
            model: Optional model override
        """
        if name not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {name}")

        # TODO: Review unreachable code - analyzer_class = self.PROVIDERS[name]
        # TODO: Review unreachable code - self.analyzers[name] = analyzer_class(api_key=api_key, model=model)
        # TODO: Review unreachable code - logger.info(f"Added {name} analyzer")

    def get_available_providers(self) -> list[str]:
        """Get list of available providers."""
        return list(self.analyzers.keys())

    # TODO: Review unreachable code - async def analyze(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - image_path: Path | str,
    # TODO: Review unreachable code - provider: str | None = None,
    # TODO: Review unreachable code - generate_prompt: bool = True,
    # TODO: Review unreachable code - extract_tags: bool = True,
    # TODO: Review unreachable code - detailed: bool = False,
    # TODO: Review unreachable code - custom_instructions: str | None = None
    # TODO: Review unreachable code - ) -> ImageAnalysisResult:
    # TODO: Review unreachable code - """Analyze an image using specified or cheapest provider.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - image_path: Path to the image
    # TODO: Review unreachable code - provider: Specific provider to use (None = use cheapest)
    # TODO: Review unreachable code - generate_prompt: Whether to generate a prompt from the image
    # TODO: Review unreachable code - extract_tags: Whether to extract semantic tags
    # TODO: Review unreachable code - detailed: Whether to include detailed descriptions
    # TODO: Review unreachable code - custom_instructions: Additional instructions for analysis

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - ImageAnalysisResult with extracted information
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - image_path = Path(image_path)
    # TODO: Review unreachable code - if not image_path.exists():
    # TODO: Review unreachable code - raise FileNotFoundError(f"Image not found: {image_path}")

    # TODO: Review unreachable code - # Select provider
    # TODO: Review unreachable code - if provider:
    # TODO: Review unreachable code - if provider not in self.analyzers:
    # TODO: Review unreachable code - raise ValueError(f"Provider {provider} not available. Available: {self.get_available_providers()}")
    # TODO: Review unreachable code - analyzer = self.analyzers[provider]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Use cheapest available provider
    # TODO: Review unreachable code - analyzer = self._get_cheapest_analyzer(detailed)
    # TODO: Review unreachable code - if not analyzer:
    # TODO: Review unreachable code - raise RuntimeError("No image analyzers available. Please set API keys.")

    # TODO: Review unreachable code - # Analyze
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - result = await analyzer.analyze(
    # TODO: Review unreachable code - image_path,
    # TODO: Review unreachable code - generate_prompt=generate_prompt,
    # TODO: Review unreachable code - extract_tags=extract_tags,
    # TODO: Review unreachable code - detailed=detailed,
    # TODO: Review unreachable code - custom_instructions=custom_instructions
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Analyzed {image_path.name} with {analyzer.name} "
    # TODO: Review unreachable code - f"(cost: ${result.cost:.4f}, tokens: {result.tokens_used})"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Cost is already tracked in the result object

    # TODO: Review unreachable code - return result

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to analyze {image_path.name} with {analyzer.name}: {e}")
    # TODO: Review unreachable code - raise

    # TODO: Review unreachable code - async def analyze_batch(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - image_paths: list[Path | str],
    # TODO: Review unreachable code - provider: str | None = None,
    # TODO: Review unreachable code - generate_prompt: bool = True,
    # TODO: Review unreachable code - extract_tags: bool = True,
    # TODO: Review unreachable code - detailed: bool = False,
    # TODO: Review unreachable code - custom_instructions: str | None = None,
    # TODO: Review unreachable code - max_concurrent: int = 5
    # TODO: Review unreachable code - ) -> list[ImageAnalysisResult]:
    # TODO: Review unreachable code - """Analyze multiple images concurrently.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - image_paths: List of image paths
    # TODO: Review unreachable code - provider: Specific provider to use
    # TODO: Review unreachable code - generate_prompt: Whether to generate prompts
    # TODO: Review unreachable code - extract_tags: Whether to extract tags
    # TODO: Review unreachable code - detailed: Whether to include detailed descriptions
    # TODO: Review unreachable code - custom_instructions: Additional instructions
    # TODO: Review unreachable code - max_concurrent: Maximum concurrent analyses

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of ImageAnalysisResult objects
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - semaphore = asyncio.Semaphore(max_concurrent)

    # TODO: Review unreachable code - async def analyze_with_semaphore(path):
    # TODO: Review unreachable code - async with semaphore:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - return await self.analyze(
    # TODO: Review unreachable code - path,
    # TODO: Review unreachable code - provider=provider,
    # TODO: Review unreachable code - generate_prompt=generate_prompt,
    # TODO: Review unreachable code - extract_tags=extract_tags,
    # TODO: Review unreachable code - detailed=detailed,
    # TODO: Review unreachable code - custom_instructions=custom_instructions
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to analyze {path}: {e}")
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - tasks = [analyze_with_semaphore(path) for path in image_paths]
    # TODO: Review unreachable code - results = await asyncio.gather(*tasks)

    # TODO: Review unreachable code - # Filter out failed analyses
    # TODO: Review unreachable code - return [r for r in results if r is not None]

    # TODO: Review unreachable code - async def compare_providers(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - image_path: Path | str,
    # TODO: Review unreachable code - providers: list[str] | None = None,
    # TODO: Review unreachable code - **kwargs
    # TODO: Review unreachable code - ) -> dict[str, ImageAnalysisResult]:
    # TODO: Review unreachable code - """Compare analysis results from multiple providers.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - image_path: Path to the image
    # TODO: Review unreachable code - providers: List of providers to compare (None = all available)
    # TODO: Review unreachable code - **kwargs: Arguments passed to analyze()

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary mapping provider name to result
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if providers is None:
    # TODO: Review unreachable code - providers = self.get_available_providers()
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - providers = [p for p in providers if p in self.analyzers]

    # TODO: Review unreachable code - results = {}

    # TODO: Review unreachable code - for provider in providers:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - result = await self.analyze(image_path, provider=provider, **kwargs)
    # TODO: Review unreachable code - results[provider] = result
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to analyze with {provider}: {e}")

    # TODO: Review unreachable code - return results

    # TODO: Review unreachable code - async def estimate_batch_cost(self, image_count: int, providers: list[str] | None = None, detailed: bool = False) -> dict[str, Any]:
    # TODO: Review unreachable code - """Estimate cost for analyzing a batch of images.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - image_count: Number of images to analyze
    # TODO: Review unreachable code - providers: List of providers to use (None = all available)
    # TODO: Review unreachable code - detailed: Whether detailed analysis is requested

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Cost estimate with breakdown
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not providers:
    # TODO: Review unreachable code - providers = list(self.analyzers.keys())

    # TODO: Review unreachable code - # Simple cost estimation
    # TODO: Review unreachable code - estimates = {}
    # TODO: Review unreachable code - for provider_name in providers:
    # TODO: Review unreachable code - if provider_name in self.analyzers:
    # TODO: Review unreachable code - analyzer = self.analyzers[provider_name]
    # TODO: Review unreachable code - cost_per_image = analyzer.estimate_cost(detailed)
    # TODO: Review unreachable code - estimates[provider_name] = {
    # TODO: Review unreachable code - "per_image": cost_per_image,
    # TODO: Review unreachable code - "total": cost_per_image * image_count
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Find cheapest provider
    # TODO: Review unreachable code - if estimates:
    # TODO: Review unreachable code - cheapest = min(estimates.items(), key=lambda x: x[1]["total"])
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "estimates": estimates,
    # TODO: Review unreachable code - "cheapest_provider": cheapest[0],
    # TODO: Review unreachable code - "cheapest_total": cheapest[1]["total"],
    # TODO: Review unreachable code - "image_count": image_count
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - return {"error": "No providers available", "image_count": image_count}

    # TODO: Review unreachable code - def _get_cheapest_analyzer(self, detailed: bool = False):
    # TODO: Review unreachable code - """Get the cheapest available analyzer."""
    # TODO: Review unreachable code - if not self.analyzers:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - # Sort by estimated cost
    # TODO: Review unreachable code - analyzers_by_cost = sorted(
    # TODO: Review unreachable code - self.analyzers.items(),
    # TODO: Review unreachable code - key=lambda x: x[1].estimate_cost(detailed)
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return analyzers_by_cost[0][1] if analyzers_by_cost else None

    # TODO: Review unreachable code - def estimate_costs(self, detailed: bool = False) -> dict[str, float]:
    # TODO: Review unreachable code - """Get cost estimates for all available providers.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - detailed: Whether estimating for detailed analysis

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary mapping provider name to estimated cost
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - costs = {}
    # TODO: Review unreachable code - for name, analyzer in self.analyzers.items():
    # TODO: Review unreachable code - costs[name] = analyzer.estimate_cost(detailed)
    # TODO: Review unreachable code - return costs

    # TODO: Review unreachable code - async def find_best_provider_for_budget(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - budget: float,
    # TODO: Review unreachable code - num_images: int,
    # TODO: Review unreachable code - detailed: bool = False
    # TODO: Review unreachable code - ) -> str | None:
    # TODO: Review unreachable code - """Find the best provider that fits within budget.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - budget: Total budget in USD
    # TODO: Review unreachable code - num_images: Number of images to analyze
    # TODO: Review unreachable code - detailed: Whether using detailed analysis

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Best provider name or None if budget too low
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - cost_per_image = budget / num_images

    # TODO: Review unreachable code - # Get providers sorted by quality (assumed order)
    # TODO: Review unreachable code - provider_order = ["anthropic", "openai", "google", "deepseek", "ollama"]

    # TODO: Review unreachable code - for provider in provider_order:
    # TODO: Review unreachable code - if provider in self.analyzers:
    # TODO: Review unreachable code - estimated_cost = self.analyzers[provider].estimate_cost(detailed)
    # TODO: Review unreachable code - if estimated_cost <= cost_per_image:
    # TODO: Review unreachable code - return provider

    # TODO: Review unreachable code - return None
