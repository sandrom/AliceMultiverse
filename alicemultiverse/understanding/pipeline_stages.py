"""Pipeline stages for image understanding."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.types import MediaType
from ..pipeline.stages import PipelineStage
from .analyzer import ImageAnalyzer

logger = logging.getLogger(__name__)


class ImageUnderstandingStage(PipelineStage):
    """Pipeline stage for AI-powered image understanding and tagging."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        detailed: bool = False,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        custom_instructions: Optional[str] = None,
        min_confidence: float = 0.0,
    ):
        """Initialize image understanding stage.
        
        Args:
            provider: Specific provider to use (None = cheapest)
            detailed: Whether to do detailed analysis
            generate_prompt: Whether to generate prompts
            extract_tags: Whether to extract semantic tags
            custom_instructions: Additional analysis instructions
            min_confidence: Minimum confidence to process (reserved for future)
        """
        self.provider = provider
        self.detailed = detailed
        self.generate_prompt = generate_prompt
        self.extract_tags = extract_tags
        self.custom_instructions = custom_instructions
        self.min_confidence = min_confidence
        
        # Initialize analyzer
        self.analyzer = ImageAnalyzer()
        
        # Check if we have any providers
        if not self.analyzer.get_available_providers():
            logger.warning("No image understanding providers available. Please set API keys.")
            self.analyzer = None
    
    def name(self) -> str:
        """Return stage name."""
        if self.provider:
            return f"understanding_{self.provider}"
        return "understanding"
    
    def process(self, image_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process image through understanding/analysis."""
        if not self.analyzer:
            logger.warning("No image analyzer available, skipping understanding")
            return metadata
        
        try:
            # Run async analyzer in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.analyzer.analyze(
                    image_path,
                    provider=self.provider,
                    generate_prompt=self.generate_prompt,
                    extract_tags=self.extract_tags,
                    detailed=self.detailed,
                    custom_instructions=self.custom_instructions
                )
            )
            
            # Store analysis results
            metadata["image_description"] = result.description
            if result.detailed_description:
                metadata["detailed_description"] = result.detailed_description
            
            # Store generated prompts
            if result.generated_prompt:
                metadata["generated_prompt"] = result.generated_prompt
            if result.negative_prompt:
                metadata["generated_negative_prompt"] = result.negative_prompt
            
            # Process and store tags
            if result.tags:
                # Merge with existing tags if any
                existing_tags = metadata.get("tags", {})
                
                # Convert to our tag format
                for category, tag_list in result.tags.items():
                    if category not in existing_tags:
                        existing_tags[category] = []
                    # Add new tags, avoiding duplicates
                    for tag in tag_list:
                        if tag not in existing_tags[category]:
                            existing_tags[category].append(tag)
                
                metadata["tags"] = existing_tags
                
                # Also store flat tag list for compatibility
                metadata["all_tags"] = result.get_all_tags()
            
            # Store technical details if available
            if result.technical_details:
                metadata["technical_analysis"] = result.technical_details
            
            # Store provider info
            metadata["understanding_provider"] = result.provider
            metadata["understanding_model"] = result.model
            metadata["understanding_cost"] = result.cost
            
            # Store in pipeline stages format
            if "pipeline_stages" not in metadata:
                metadata["pipeline_stages"] = {}
            
            metadata["pipeline_stages"][self.name()] = {
                "provider": result.provider,
                "model": result.model,
                "cost": result.cost,
                "tokens": result.tokens_used,
                "has_tags": bool(result.tags),
                "has_prompt": bool(result.generated_prompt),
                "timestamp": time.time(),
            }
            
            logger.info(
                f"Understood {image_path.name} with {result.provider} "
                f"(${result.cost:.4f}, {len(result.get_all_tags())} tags)"
            )
            
        except Exception as e:
            logger.error(f"Image understanding failed for {image_path.name}: {e}")
            
        return metadata
    
    def should_process(self, metadata: Dict[str, Any]) -> bool:
        """Check if this stage should process the image."""
        # Only process images
        if metadata.get("media_type") != MediaType.IMAGE:
            return False
        
        # Skip if already processed by same provider
        if "pipeline_stages" in metadata:
            stage_name = self.name()
            if stage_name in metadata["pipeline_stages"]:
                logger.debug(f"Already processed by {stage_name}")
                return False
        
        return True
    
    def get_cost(self) -> float:
        """Get estimated cost per image."""
        if not self.analyzer:
            return 0.0
        
        # Get cost for selected or cheapest provider
        if self.provider and self.provider in self.analyzer.analyzers:
            return self.analyzer.analyzers[self.provider].estimate_cost(self.detailed)
        else:
            # Return cheapest available
            costs = self.analyzer.estimate_costs(self.detailed)
            return min(costs.values()) if costs else 0.0


class MultiProviderUnderstandingStage(PipelineStage):
    """Pipeline stage that uses multiple providers for comprehensive analysis."""
    
    def __init__(
        self,
        providers: List[str],
        merge_tags: bool = True,
        merge_prompts: bool = False,
        detailed: bool = False,
    ):
        """Initialize multi-provider understanding stage.
        
        Args:
            providers: List of providers to use
            merge_tags: Whether to merge tags from all providers
            merge_prompts: Whether to combine prompts
            detailed: Whether to do detailed analysis
        """
        self.providers = providers
        self.merge_tags = merge_tags
        self.merge_prompts = merge_prompts
        self.detailed = detailed
        
        # Initialize analyzer
        self.analyzer = ImageAnalyzer()
        
        # Filter to available providers
        available = self.analyzer.get_available_providers()
        self.providers = [p for p in providers if p in available]
        
        if not self.providers:
            logger.warning(f"No requested providers available. Requested: {providers}")
            self.analyzer = None
    
    def name(self) -> str:
        """Return stage name."""
        return f"understanding_multi_{'_'.join(self.providers)}"
    
    def process(self, image_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process image through multiple providers."""
        if not self.analyzer or not self.providers:
            logger.warning("No providers available for multi-provider understanding")
            return metadata
        
        try:
            # Run async analyzer in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Analyze with all providers
            results = loop.run_until_complete(
                self.analyzer.compare_providers(
                    image_path,
                    providers=self.providers,
                    generate_prompt=True,
                    extract_tags=True,
                    detailed=self.detailed
                )
            )
            
            # Process results
            all_tags = {}
            all_prompts = []
            all_descriptions = []
            total_cost = 0.0
            
            for provider, result in results.items():
                # Collect descriptions
                all_descriptions.append(f"[{provider}] {result.description}")
                
                # Merge tags
                if self.merge_tags and result.tags:
                    for category, tag_list in result.tags.items():
                        if category not in all_tags:
                            all_tags[category] = []
                        all_tags[category].extend(tag_list)
                
                # Collect prompts
                if result.generated_prompt:
                    all_prompts.append(f"[{provider}] {result.generated_prompt}")
                
                total_cost += result.cost
            
            # Store merged results
            metadata["image_descriptions"] = all_descriptions
            metadata["image_description"] = all_descriptions[0] if all_descriptions else ""
            
            # Deduplicate and store tags
            if all_tags:
                # Remove duplicates from each category
                for category in all_tags:
                    all_tags[category] = list(set(all_tags[category]))
                
                metadata["tags"] = all_tags
                
                # Flat list
                flat_tags = []
                for tags in all_tags.values():
                    flat_tags.extend(tags)
                metadata["all_tags"] = list(set(flat_tags))
            
            # Store prompts
            if all_prompts:
                if self.merge_prompts:
                    # Combine prompts intelligently
                    metadata["generated_prompt"] = self._merge_prompts(all_prompts)
                else:
                    metadata["generated_prompts"] = all_prompts
                    metadata["generated_prompt"] = all_prompts[0]
            
            # Store analysis metadata
            metadata["understanding_providers"] = list(results.keys())
            metadata["understanding_total_cost"] = total_cost
            
            # Pipeline stages format
            if "pipeline_stages" not in metadata:
                metadata["pipeline_stages"] = {}
            
            metadata["pipeline_stages"][self.name()] = {
                "providers": list(results.keys()),
                "total_cost": total_cost,
                "tag_count": len(metadata.get("all_tags", [])),
                "timestamp": time.time(),
            }
            
            logger.info(
                f"Multi-provider analysis of {image_path.name} complete "
                f"({len(results)} providers, ${total_cost:.4f} total)"
            )
            
        except Exception as e:
            logger.error(f"Multi-provider understanding failed: {e}")
            
        return metadata
    
    def should_process(self, metadata: Dict[str, Any]) -> bool:
        """Check if this stage should process the image."""
        return metadata.get("media_type") == MediaType.IMAGE
    
    def get_cost(self) -> float:
        """Get total estimated cost."""
        if not self.analyzer:
            return 0.0
        
        total = 0.0
        for provider in self.providers:
            if provider in self.analyzer.analyzers:
                total += self.analyzer.analyzers[provider].estimate_cost(self.detailed)
        
        return total
    
    def _merge_prompts(self, prompts: List[str]) -> str:
        """Intelligently merge multiple prompts."""
        # Simple implementation - can be enhanced
        # Remove provider tags
        clean_prompts = []
        for prompt in prompts:
            if "]" in prompt:
                prompt = prompt.split("]", 1)[1].strip()
            clean_prompts.append(prompt)
        
        # For now, just take the longest one
        return max(clean_prompts, key=len)