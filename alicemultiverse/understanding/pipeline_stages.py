"""Pipeline stages for image understanding with advanced capabilities."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.types import MediaType
from ..database.repository import AssetRepository
from ..pipeline.stages import PipelineStage
from .advanced_tagger import AdvancedTagger
from .analyzer import ImageAnalyzer
from .batch_analyzer import BatchAnalyzer, BatchAnalysisRequest
from .custom_instructions import CustomInstructionManager
from .provider_optimizer import ProviderOptimizer

logger = logging.getLogger(__name__)


class ImageUnderstandingStage(PipelineStage):
    """Advanced pipeline stage for AI-powered image understanding and tagging."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        detailed: bool = False,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        custom_instructions: Optional[str] = None,
        min_confidence: float = 0.0,
        # Advanced features
        use_hierarchical_tags: bool = True,
        use_custom_vocabulary: bool = True,
        use_provider_optimization: bool = False,
        budget_limit: Optional[float] = None,
        project_id: Optional[str] = None,
        repository: Optional[AssetRepository] = None,
    ):
        """Initialize advanced image understanding stage.
        
        Args:
            provider: Specific provider to use (None = auto-select)
            detailed: Whether to do detailed analysis
            generate_prompt: Whether to generate prompts
            extract_tags: Whether to extract semantic tags
            custom_instructions: Additional analysis instructions
            min_confidence: Minimum confidence to process
            use_hierarchical_tags: Whether to expand tags hierarchically
            use_custom_vocabulary: Whether to apply project-specific vocabulary
            use_provider_optimization: Whether to use provider optimization
            budget_limit: Optional budget limit per analysis
            project_id: Project ID for custom instructions/vocabulary
            repository: Asset repository for database operations
        """
        self.provider = provider
        self.detailed = detailed
        self.generate_prompt = generate_prompt
        self.extract_tags = extract_tags
        self.custom_instructions = custom_instructions
        self.min_confidence = min_confidence
        self.use_hierarchical_tags = use_hierarchical_tags
        self.use_custom_vocabulary = use_custom_vocabulary
        self.use_provider_optimization = use_provider_optimization
        self.budget_limit = budget_limit
        self.project_id = project_id
        self.repository = repository
        
        # Initialize core analyzer
        self.analyzer = ImageAnalyzer()
        
        # Initialize advanced components
        self.advanced_tagger = None
        self.instruction_manager = None
        self.provider_optimizer = None
        
        if self.repository and (use_hierarchical_tags or use_custom_vocabulary):
            self.advanced_tagger = AdvancedTagger(self.repository)
        
        if project_id or custom_instructions:
            self.instruction_manager = CustomInstructionManager()
        
        if use_provider_optimization:
            self.provider_optimizer = ProviderOptimizer(self.analyzer)
            if budget_limit:
                self.provider_optimizer.set_budget(budget_limit)
        
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
        """Process image through advanced understanding/analysis."""
        if not self.analyzer:
            logger.warning("No image analyzer available, skipping understanding")
            return metadata
        
        try:
            # Build custom instructions if needed
            instructions = self.custom_instructions
            if self.instruction_manager and self.project_id:
                project_instructions = self.instruction_manager.build_analysis_instructions(
                    self.project_id,
                    category="general"
                )
                if project_instructions:
                    instructions = project_instructions
            
            # Run async analysis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Use provider optimization if enabled
            if self.provider_optimizer:
                result = loop.run_until_complete(
                    self.provider_optimizer.analyze_with_optimization(
                        image_path,
                        provider=self.provider,
                        generate_prompt=self.generate_prompt,
                        extract_tags=self.extract_tags,
                        detailed=self.detailed,
                        custom_instructions=instructions
                    )
                )
            else:
                result = loop.run_until_complete(
                    self.analyzer.analyze(
                        image_path,
                        provider=self.provider,
                        generate_prompt=self.generate_prompt,
                        extract_tags=self.extract_tags,
                        detailed=self.detailed,
                        custom_instructions=instructions
                    )
                )
            
            if not result:
                logger.warning(f"No analysis result for {image_path.name}")
                return metadata
            
            # Apply advanced tagging if enabled
            if self.advanced_tagger and result.tags:
                # Add specialized categories
                self.advanced_tagger.add_specialized_categories(result, image_path)
                
                # Expand with hierarchical tags
                if self.use_hierarchical_tags:
                    expanded_tags = self.advanced_tagger.expand_tags(result, self.project_id)
                    result.tags = expanded_tags
                
                # Apply custom vocabulary
                if self.use_custom_vocabulary and self.project_id:
                    self.advanced_tagger.apply_custom_vocabulary(result, self.project_id)
                
                # Save tags to database if we have content hash
                content_hash = metadata.get("content_hash")
                if content_hash and self.repository:
                    self.advanced_tagger.save_tags_to_database(
                        content_hash, result.tags, source="ai"
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
            
            # Process and store enhanced tags
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
                
                # Store enhanced tag list
                metadata["all_tags"] = result.get_all_tags()
                metadata["tag_categories"] = list(result.tags.keys())
                metadata["hierarchical_tags"] = self.use_hierarchical_tags
            
            # Store technical details if available
            if result.technical_details:
                metadata["technical_analysis"] = result.technical_details
            
            # Store provider info
            metadata["understanding_provider"] = result.provider
            metadata["understanding_model"] = result.model
            metadata["understanding_cost"] = result.cost
            
            # Store advanced features info
            metadata["advanced_understanding"] = {
                "hierarchical_tags": self.use_hierarchical_tags,
                "custom_vocabulary": self.use_custom_vocabulary,
                "provider_optimization": self.use_provider_optimization,
                "project_id": self.project_id,
                "custom_instructions": bool(instructions != self.custom_instructions)
            }
            
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
                "tag_count": len(result.get_all_tags()) if result.tags else 0,
                "categories": len(result.tags) if result.tags else 0,
                "advanced_features": metadata["advanced_understanding"],
                "timestamp": time.time(),
            }
            
            logger.info(
                f"Advanced understanding of {image_path.name} with {result.provider} "
                f"(${result.cost:.4f}, {len(result.get_all_tags())} tags, "
                f"{len(result.tags) if result.tags else 0} categories)"
            )
            
        except Exception as e:
            logger.error(f"Advanced image understanding failed for {image_path.name}: {e}")
            
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


class AdvancedBatchUnderstandingStage(PipelineStage):
    """Advanced batch processing stage for efficient multi-image analysis."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        detailed: bool = False,
        generate_prompt: bool = True,
        extract_tags: bool = True,
        max_concurrent: int = 5,
        budget_limit: Optional[float] = None,
        project_id: Optional[str] = None,
        repository: Optional[AssetRepository] = None,
        use_optimization: bool = True,
        checkpoint_interval: int = 10,
    ):
        """Initialize advanced batch understanding stage.
        
        Args:
            provider: Specific provider to use (None = auto-select)
            detailed: Whether to do detailed analysis
            generate_prompt: Whether to generate prompts
            extract_tags: Whether to extract tags
            max_concurrent: Maximum concurrent analyses
            budget_limit: Budget limit for the batch
            project_id: Project ID for custom instructions
            repository: Asset repository for database operations
            use_optimization: Whether to use provider optimization
            checkpoint_interval: Save progress every N images
        """
        self.provider = provider
        self.detailed = detailed
        self.generate_prompt = generate_prompt
        self.extract_tags = extract_tags
        self.max_concurrent = max_concurrent
        self.budget_limit = budget_limit
        self.project_id = project_id
        self.repository = repository
        self.use_optimization = use_optimization
        self.checkpoint_interval = checkpoint_interval
        
        # Initialize components
        self.analyzer = ImageAnalyzer()
        self.batch_analyzer = BatchAnalyzer(self.analyzer, self.repository)
        self.advanced_tagger = None
        self.instruction_manager = None
        
        if self.repository:
            self.advanced_tagger = AdvancedTagger(self.repository)
        
        if project_id:
            self.instruction_manager = CustomInstructionManager()
    
    def name(self) -> str:
        """Return stage name."""
        return "advanced_batch_understanding"
    
    async def process_batch(self, image_paths: List[Path], 
                          metadata_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of images efficiently.
        
        Args:
            image_paths: List of image paths to process
            metadata_list: List of metadata dictionaries
            
        Returns:
            Updated metadata list
        """
        if not self.analyzer or not image_paths:
            return metadata_list
        
        try:
            # Build custom instructions if needed
            instructions = None
            if self.instruction_manager and self.project_id:
                instructions = self.instruction_manager.build_analysis_instructions(
                    self.project_id,
                    category="general"
                )
            
            # Create batch request
            request = BatchAnalysisRequest(
                image_paths=image_paths,
                project_id=self.project_id,
                provider=self.provider,
                generate_prompt=self.generate_prompt,
                extract_tags=self.extract_tags,
                detailed=self.detailed,
                custom_instructions=instructions,
                max_concurrent=self.max_concurrent,
                max_cost=self.budget_limit,
                checkpoint_interval=self.checkpoint_interval,
                skip_existing=True,
                show_progress=True
            )
            
            # Estimate cost first
            estimated_cost, cost_details = await self.batch_analyzer.estimate_cost(request)
            logger.info(f"Batch analysis estimated cost: ${estimated_cost:.2f}")
            
            if self.budget_limit and estimated_cost > self.budget_limit:
                logger.warning(f"Estimated cost exceeds budget limit: ${estimated_cost:.2f} > ${self.budget_limit:.2f}")
                return metadata_list
            
            # Process batch
            results = await self.batch_analyzer.analyze_batch(request)
            
            # Update metadata with results
            result_dict = {str(path): result for path, result in results if result}
            
            for i, (image_path, metadata) in enumerate(zip(image_paths, metadata_list)):
                result = result_dict.get(str(image_path))
                if not result:
                    continue
                
                # Apply advanced tagging
                if self.advanced_tagger and result.tags:
                    # Add specialized categories
                    self.advanced_tagger.add_specialized_categories(result, image_path)
                    
                    # Expand with hierarchical tags
                    expanded_tags = self.advanced_tagger.expand_tags(result, self.project_id)
                    result.tags = expanded_tags
                    
                    # Apply custom vocabulary
                    if self.project_id:
                        self.advanced_tagger.apply_custom_vocabulary(result, self.project_id)
                
                # Update metadata
                metadata["image_description"] = result.description
                if result.detailed_description:
                    metadata["detailed_description"] = result.detailed_description
                
                if result.generated_prompt:
                    metadata["generated_prompt"] = result.generated_prompt
                if result.negative_prompt:
                    metadata["generated_negative_prompt"] = result.negative_prompt
                
                if result.tags:
                    existing_tags = metadata.get("tags", {})
                    for category, tag_list in result.tags.items():
                        if category not in existing_tags:
                            existing_tags[category] = []
                        for tag in tag_list:
                            if tag not in existing_tags[category]:
                                existing_tags[category].append(tag)
                    
                    metadata["tags"] = existing_tags
                    metadata["all_tags"] = result.get_all_tags()
                    metadata["tag_categories"] = list(result.tags.keys())
                
                # Store provider info
                metadata["understanding_provider"] = result.provider
                metadata["understanding_model"] = result.model
                metadata["understanding_cost"] = result.cost
                
                # Store batch processing info
                metadata["batch_processing"] = {
                    "batch_size": len(image_paths),
                    "estimated_cost": estimated_cost,
                    "actual_cost": result.cost,
                    "provider_optimization": self.use_optimization,
                    "concurrent_limit": self.max_concurrent
                }
                
                # Pipeline stages format
                if "pipeline_stages" not in metadata:
                    metadata["pipeline_stages"] = {}
                
                metadata["pipeline_stages"][self.name()] = {
                    "provider": result.provider,
                    "model": result.model,
                    "cost": result.cost,
                    "tokens": result.tokens_used,
                    "has_tags": bool(result.tags),
                    "has_prompt": bool(result.generated_prompt),
                    "tag_count": len(result.get_all_tags()) if result.tags else 0,
                    "batch_info": metadata["batch_processing"],
                    "timestamp": time.time(),
                }
            
            total_cost = sum(r.cost for _, r in results if r)
            logger.info(f"Batch understanding complete: {len(results)} images, ${total_cost:.2f} total cost")
            
        except Exception as e:
            logger.error(f"Advanced batch understanding failed: {e}")
        
        return metadata_list
    
    def process(self, image_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Single image processing (for compatibility)."""
        # For single images, use regular understanding stage
        stage = ImageUnderstandingStage(
            provider=self.provider,
            detailed=self.detailed,
            generate_prompt=self.generate_prompt,
            extract_tags=self.extract_tags,
            project_id=self.project_id,
            repository=self.repository,
            use_hierarchical_tags=True,
            use_custom_vocabulary=True,
            use_provider_optimization=self.use_optimization,
            budget_limit=self.budget_limit
        )
        return stage.process(image_path, metadata)
    
    def should_process(self, metadata: Dict[str, Any]) -> bool:
        """Check if this stage should process the image."""
        return metadata.get("media_type") == MediaType.IMAGE
    
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