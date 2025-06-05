"""Optimized batch analyzer with similarity detection and smart grouping.

This module implements cost-saving optimizations:
1. Groups similar images using perceptual hashing
2. Analyzes one representative per group
3. Applies results to similar images
4. Uses progressive provider strategy (cheap → expensive)
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

import numpy as np
from tqdm import tqdm

from ..assets.perceptual_hashing import (
    calculate_perceptual_hash,
    calculate_difference_hash,
    hamming_distance
)
from ..core.cost_tracker import get_cost_tracker
from .analyzer import ImageAnalyzer
from .batch_analyzer import BatchAnalysisRequest, BatchProgress
from .base import ImageAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class ImageGroup:
    """Group of similar images."""
    representative: Path
    members: List[Path] = field(default_factory=list)
    representative_hash: Optional[str] = None
    analysis_result: Optional[ImageAnalysisResult] = None
    confidence_scores: Dict[Path, float] = field(default_factory=dict)


@dataclass
class OptimizationStats:
    """Statistics for batch optimization."""
    total_images: int = 0
    unique_groups: int = 0
    images_analyzed: int = 0
    images_reused: int = 0
    api_calls_saved: int = 0
    cost_saved: float = 0.0
    total_cost: float = 0.0


class OptimizedBatchAnalyzer:
    """Batch analyzer with similarity detection and cost optimization."""
    
    def __init__(
        self,
        analyzer: ImageAnalyzer,
        similarity_threshold: float = 0.9,
        min_group_size: int = 2,
        use_progressive_providers: bool = True
    ):
        """Initialize optimized batch analyzer.
        
        Args:
            analyzer: Image analyzer instance
            similarity_threshold: Threshold for considering images similar (0-1)
            min_group_size: Minimum images to form a group
            use_progressive_providers: Use cheap providers first
        """
        self.analyzer = analyzer
        self.similarity_threshold = similarity_threshold
        self.min_group_size = min_group_size
        self.use_progressive_providers = use_progressive_providers
        self.cost_tracker = get_cost_tracker()
        
    async def analyze_batch_optimized(
        self,
        request: BatchAnalysisRequest
    ) -> Tuple[List[Tuple[Path, Optional[ImageAnalysisResult]]], OptimizationStats]:
        """Analyze batch with optimization.
        
        Returns:
            Tuple of (results, optimization_stats)
        """
        # Get images to process
        images = await self._get_images_to_process(request)
        logger.info(f"Starting optimized batch analysis for {len(images)} images")
        
        # Initialize stats
        stats = OptimizationStats(total_images=len(images))
        
        # Group similar images
        groups = await self._group_similar_images(images, request.show_progress)
        stats.unique_groups = len(groups)
        logger.info(f"Grouped {len(images)} images into {len(groups)} similarity groups")
        
        # Analyze representatives
        results = []
        
        if request.show_progress:
            pbar = tqdm(total=len(groups), desc="Analyzing image groups")
        
        for group in groups:
            # Analyze representative
            if len(group.members) >= self.min_group_size:
                # Worth optimizing - analyze representative and apply to group
                result = await self._analyze_with_progressive_providers(
                    group.representative,
                    request
                )
                
                if result:
                    group.analysis_result = result
                    stats.images_analyzed += 1
                    stats.total_cost += result.cost
                    
                    # Apply to all members
                    for member in group.members:
                        confidence = group.confidence_scores.get(member, 1.0)
                        member_result = self._apply_result_to_similar(
                            result, member, confidence
                        )
                        results.append((member, member_result))
                        
                        if member != group.representative:
                            stats.images_reused += 1
                            stats.api_calls_saved += 1
                            # Estimate cost saved
                            stats.cost_saved += self._estimate_cost_saved(request)
                else:
                    # Analysis failed, mark all as failed
                    for member in group.members:
                        results.append((member, None))
            else:
                # Small group - analyze individually
                for member in group.members:
                    result = await self._analyze_with_progressive_providers(
                        member, request
                    )
                    results.append((member, result))
                    if result:
                        stats.images_analyzed += 1
                        stats.total_cost += result.cost
            
            if request.show_progress:
                pbar.update(1)
                pbar.set_postfix({
                    "analyzed": stats.images_analyzed,
                    "reused": stats.images_reused,
                    "saved": f"${stats.cost_saved:.2f}"
                })
        
        if request.show_progress:
            pbar.close()
        
        # Log optimization summary
        logger.info(f"Optimization complete: {stats.images_analyzed} analyzed, "
                   f"{stats.images_reused} reused, ${stats.cost_saved:.2f} saved")
        
        return results, stats
    
    async def _group_similar_images(
        self,
        images: List[Path],
        show_progress: bool = False
    ) -> List[ImageGroup]:
        """Group similar images using perceptual hashing."""
        groups = []
        processed = set()
        
        # Calculate hashes for all images
        image_hashes = {}
        
        if show_progress:
            pbar = tqdm(total=len(images), desc="Computing image hashes")
        
        for img_path in images:
            phash = calculate_perceptual_hash(img_path)
            dhash = calculate_difference_hash(img_path)
            if phash and dhash:
                image_hashes[img_path] = (phash, dhash)
            if show_progress:
                pbar.update(1)
        
        if show_progress:
            pbar.close()
        
        # Group by similarity
        for img_path, (phash, dhash) in image_hashes.items():
            if img_path in processed:
                continue
                
            # Create new group
            group = ImageGroup(
                representative=img_path,
                members=[img_path],
                representative_hash=phash
            )
            group.confidence_scores[img_path] = 1.0  # Representative has full confidence
            processed.add(img_path)
            
            # Find similar images
            for other_path, (other_phash, other_dhash) in image_hashes.items():
                if other_path in processed:
                    continue
                    
                # Calculate similarity
                similarity = self._calculate_similarity(
                    phash, dhash, other_phash, other_dhash
                )
                
                if similarity >= self.similarity_threshold:
                    group.members.append(other_path)
                    group.confidence_scores[other_path] = similarity
                    processed.add(other_path)
            
            groups.append(group)
        
        # Add any images that couldn't be hashed as single-member groups
        for img_path in images:
            if img_path not in processed:
                groups.append(ImageGroup(
                    representative=img_path,
                    members=[img_path]
                ))
        
        return groups
    
    def _calculate_similarity(
        self,
        phash1: str,
        dhash1: str,
        phash2: str,
        dhash2: str
    ) -> float:
        """Calculate similarity between two images using their hashes."""
        # Convert hex strings to binary
        phash1_bin = bin(int(phash1, 16))[2:].zfill(64)
        phash2_bin = bin(int(phash2, 16))[2:].zfill(64)
        dhash1_bin = bin(int(dhash1, 16))[2:].zfill(64)
        dhash2_bin = bin(int(dhash2, 16))[2:].zfill(64)
        
        # Calculate Hamming distances
        phash_distance = hamming_distance(phash1_bin, phash2_bin)
        dhash_distance = hamming_distance(dhash1_bin, dhash2_bin)
        
        # Convert to similarity (0-1)
        phash_similarity = 1 - (phash_distance / 64)
        dhash_similarity = 1 - (dhash_distance / 64)
        
        # Weighted average (perceptual hash is more important)
        return 0.7 * phash_similarity + 0.3 * dhash_similarity
    
    async def _analyze_with_progressive_providers(
        self,
        image_path: Path,
        request: BatchAnalysisRequest
    ) -> Optional[ImageAnalysisResult]:
        """Analyze image with progressive provider strategy."""
        if not self.use_progressive_providers or request.provider:
            # Use standard analysis
            return await self.analyzer.analyze(
                image_path,
                provider=request.provider,
                generate_prompt=request.generate_prompt,
                extract_tags=request.extract_tags,
                detailed=request.detailed,
                custom_instructions=request.custom_instructions
            )
        
        # Progressive strategy: cheap → expensive
        provider_tiers = [
            ["google-ai"],  # Free tier
            ["deepseek"],   # Very cheap
            ["anthropic", "openai"]  # Premium
        ]
        
        last_result = None
        
        for tier in provider_tiers:
            available_providers = [
                p for p in tier 
                if p in self.analyzer.get_available_providers()
            ]
            
            if not available_providers:
                continue
            
            # Try providers in this tier
            for provider in available_providers:
                try:
                    result = await self.analyzer.analyze(
                        image_path,
                        provider=provider,
                        generate_prompt=request.generate_prompt,
                        extract_tags=request.extract_tags,
                        detailed=request.detailed,
                        custom_instructions=request.custom_instructions
                    )
                    
                    # Check if result is good enough
                    if self._is_result_sufficient(result, tier == provider_tiers[-1]):
                        return result
                    
                    last_result = result
                    
                except Exception as e:
                    logger.debug(f"Provider {provider} failed: {e}")
                    continue
        
        # Return best result we got
        return last_result
    
    def _is_result_sufficient(
        self,
        result: ImageAnalysisResult,
        is_final_tier: bool
    ) -> bool:
        """Check if analysis result is sufficient."""
        if is_final_tier:
            return True  # Accept any result from premium tier
        
        # Check quality indicators
        if not result.tags or len(result.tags) < 5:
            return False  # Too few tags
        
        if result.description and len(result.description) < 50:
            return False  # Description too short
        
        # Check for specific tag categories
        tag_categories = defaultdict(int)
        for tag in result.tags:
            if any(color in tag.lower() for color in ["red", "blue", "green", "color"]):
                tag_categories["color"] += 1
            elif any(style in tag.lower() for style in ["style", "art", "design"]):
                tag_categories["style"] += 1
            elif any(obj in tag.lower() for obj in ["person", "object", "thing"]):
                tag_categories["object"] += 1
        
        # Need at least 2 categories
        return len(tag_categories) >= 2
    
    def _apply_result_to_similar(
        self,
        original_result: ImageAnalysisResult,
        target_path: Path,
        confidence: float
    ) -> ImageAnalysisResult:
        """Apply analysis result to a similar image."""
        # Create a new result with adjusted confidence
        return ImageAnalysisResult(
            description=f"{original_result.description} (Similar image, {confidence:.0%} confidence)",
            tags=original_result.tags.copy(),
            custom_tags=original_result.custom_tags.copy() if original_result.custom_tags else [],
            technical_details=original_result.technical_details.copy() if original_result.technical_details else {},
            provider=f"{original_result.provider} (reused)",
            model=original_result.model,
            cost=0.0,  # No additional cost
            raw_response=original_result.raw_response,
            confidence_score=original_result.confidence_score * confidence if original_result.confidence_score else confidence
        )
    
    def _estimate_cost_saved(self, request: BatchAnalysisRequest) -> float:
        """Estimate cost saved by reusing analysis."""
        # Get typical cost for the selected or cheapest provider
        if request.provider:
            providers = [request.provider]
        else:
            providers = self.analyzer.get_available_providers()
        
        costs = []
        for provider in providers:
            if provider in self.analyzer.analyzers:
                cost = self.analyzer.analyzers[provider].estimate_cost(request.detailed)
                costs.append(cost)
        
        return min(costs) if costs else 0.0
    
    async def _get_images_to_process(self, request: BatchAnalysisRequest) -> List[Path]:
        """Get list of images to process based on request."""
        # Reuse the existing method from batch analyzer
        from .batch_analyzer import BatchAnalyzer
        temp_analyzer = BatchAnalyzer(self.analyzer)
        return await temp_analyzer._get_images_to_process(request)