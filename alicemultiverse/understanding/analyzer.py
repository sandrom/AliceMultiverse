"""Main image analyzer that coordinates between providers."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.cost_tracker import get_cost_tracker, CostCategory
from .base import ImageAnalysisResult
from .providers import (
    AnthropicImageAnalyzer,
    OpenAIImageAnalyzer,
    GoogleAIImageAnalyzer,
    DeepSeekImageAnalyzer,
)
from .ollama_provider import OllamaImageAnalyzer

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
    
    def add_analyzer(self, name: str, api_key: str, model: Optional[str] = None):
        """Add a specific analyzer.
        
        Args:
            name: Provider name
            api_key: API key for the provider
            model: Optional model override
        """
        if name not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {name}")
        
        analyzer_class = self.PROVIDERS[name]
        self.analyzers[name] = analyzer_class(api_key=api_key, model=model)
        logger.info(f"Added {name} analyzer")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.analyzers.keys())
    
    async def analyze(
        self,
        image_path: Union[Path, str],
        provider: Optional[str] = None,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        detailed: bool = False,
        custom_instructions: Optional[str] = None
    ) -> ImageAnalysisResult:
        """Analyze an image using specified or cheapest provider.
        
        Args:
            image_path: Path to the image
            provider: Specific provider to use (None = use cheapest)
            generate_prompt: Whether to generate a prompt from the image
            extract_tags: Whether to extract semantic tags
            detailed: Whether to include detailed descriptions
            custom_instructions: Additional instructions for analysis
            
        Returns:
            ImageAnalysisResult with extracted information
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Select provider
        if provider:
            if provider not in self.analyzers:
                raise ValueError(f"Provider {provider} not available. Available: {self.get_available_providers()}")
            analyzer = self.analyzers[provider]
        else:
            # Use cheapest available provider
            analyzer = self._get_cheapest_analyzer(detailed)
            if not analyzer:
                raise RuntimeError("No image analyzers available. Please set API keys.")
        
        # Analyze
        try:
            result = await analyzer.analyze(
                image_path,
                generate_prompt=generate_prompt,
                extract_tags=extract_tags,
                detailed=detailed,
                custom_instructions=custom_instructions
            )
            
            logger.info(
                f"Analyzed {image_path.name} with {analyzer.name} "
                f"(cost: ${result.cost:.4f}, tokens: {result.tokens_used})"
            )
            
            # Record actual cost
            cost_tracker = get_cost_tracker()
            cost_tracker.record_cost(
                provider=analyzer.name,
                operation="image_analysis",
                cost=result.cost,
                category=CostCategory.UNDERSTANDING,
                details={
                    "detailed": detailed,
                    "tokens_used": result.tokens_used,
                    "image_path": str(image_path)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze {image_path.name} with {analyzer.name}: {e}")
            raise
    
    async def analyze_batch(
        self,
        image_paths: List[Union[Path, str]],
        provider: Optional[str] = None,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        detailed: bool = False,
        custom_instructions: Optional[str] = None,
        max_concurrent: int = 5
    ) -> List[ImageAnalysisResult]:
        """Analyze multiple images concurrently.
        
        Args:
            image_paths: List of image paths
            provider: Specific provider to use
            generate_prompt: Whether to generate prompts
            extract_tags: Whether to extract tags
            detailed: Whether to include detailed descriptions
            custom_instructions: Additional instructions
            max_concurrent: Maximum concurrent analyses
            
        Returns:
            List of ImageAnalysisResult objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(path):
            async with semaphore:
                try:
                    return await self.analyze(
                        path,
                        provider=provider,
                        generate_prompt=generate_prompt,
                        extract_tags=extract_tags,
                        detailed=detailed,
                        custom_instructions=custom_instructions
                    )
                except Exception as e:
                    logger.error(f"Failed to analyze {path}: {e}")
                    return None
        
        tasks = [analyze_with_semaphore(path) for path in image_paths]
        results = await asyncio.gather(*tasks)
        
        # Filter out failed analyses
        return [r for r in results if r is not None]
    
    async def compare_providers(
        self,
        image_path: Union[Path, str],
        providers: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, ImageAnalysisResult]:
        """Compare analysis results from multiple providers.
        
        Args:
            image_path: Path to the image
            providers: List of providers to compare (None = all available)
            **kwargs: Arguments passed to analyze()
            
        Returns:
            Dictionary mapping provider name to result
        """
        if providers is None:
            providers = self.get_available_providers()
        else:
            providers = [p for p in providers if p in self.analyzers]
        
        results = {}
        
        for provider in providers:
            try:
                result = await self.analyze(image_path, provider=provider, **kwargs)
                results[provider] = result
            except Exception as e:
                logger.error(f"Failed to analyze with {provider}: {e}")
        
        return results
    
    async def estimate_batch_cost(self, image_count: int, providers: Optional[List[str]] = None, detailed: bool = False) -> Dict[str, Any]:
        """Estimate cost for analyzing a batch of images.
        
        Args:
            image_count: Number of images to analyze
            providers: List of providers to use (None = all available)
            detailed: Whether detailed analysis is requested
            
        Returns:
            Cost estimate with breakdown
        """
        if not providers:
            providers = list(self.analyzers.keys())
        
        cost_tracker = get_cost_tracker()
        return cost_tracker.estimate_batch_cost(
            file_count=image_count,
            providers=providers,
            operation="image_analysis",
            detailed=detailed
        )
    
    def _get_cheapest_analyzer(self, detailed: bool = False):
        """Get the cheapest available analyzer."""
        if not self.analyzers:
            return None
        
        # Sort by estimated cost
        analyzers_by_cost = sorted(
            self.analyzers.items(),
            key=lambda x: x[1].estimate_cost(detailed)
        )
        
        return analyzers_by_cost[0][1] if analyzers_by_cost else None
    
    def estimate_costs(self, detailed: bool = False) -> Dict[str, float]:
        """Get cost estimates for all available providers.
        
        Args:
            detailed: Whether estimating for detailed analysis
            
        Returns:
            Dictionary mapping provider name to estimated cost
        """
        costs = {}
        for name, analyzer in self.analyzers.items():
            costs[name] = analyzer.estimate_cost(detailed)
        return costs
    
    async def find_best_provider_for_budget(
        self,
        budget: float,
        num_images: int,
        detailed: bool = False
    ) -> Optional[str]:
        """Find the best provider that fits within budget.
        
        Args:
            budget: Total budget in USD
            num_images: Number of images to analyze
            detailed: Whether using detailed analysis
            
        Returns:
            Best provider name or None if budget too low
        """
        cost_per_image = budget / num_images
        
        # Get providers sorted by quality (assumed order)
        provider_order = ["anthropic", "openai", "google", "deepseek", "ollama"]
        
        for provider in provider_order:
            if provider in self.analyzers:
                estimated_cost = self.analyzers[provider].estimate_cost(detailed)
                if estimated_cost <= cost_per_image:
                    return provider
        
        return None