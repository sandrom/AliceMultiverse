"""Batch operations for prompt management."""

from typing import List, Dict, Any, Optional, Callable, Tuple
from pathlib import Path
import csv
import json
from datetime import datetime

from ..core.logging import get_logger
from ..providers.types import GenerationResult
from .service import PromptService
from .models import Prompt, PromptCategory, ProviderType
from .templates import TemplateManager

logger = get_logger(__name__)


class PromptBatchProcessor:
    """Process multiple prompts in batch operations."""
    
    def __init__(self, service: Optional[PromptService] = None):
        self.service = service or PromptService()
        self.template_manager = TemplateManager()
    
    def batch_create_from_csv(self, csv_path: Path) -> List[Prompt]:
        """Create multiple prompts from a CSV file.
        
        Expected CSV columns:
        - text: Prompt text (required)
        - category: Category name (required)
        - providers: Comma-separated provider names (required)
        - tags: Comma-separated tags
        - project: Project name
        - style: Style name
        - description: Description
        - notes: Notes
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of created prompts
        """
        created_prompts = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse required fields
                    if not all(k in row for k in ['text', 'category', 'providers']):
                        logger.warning(f"Skipping row - missing required fields: {row}")
                        continue
                    
                    # Parse providers
                    providers = []
                    for p in row['providers'].split(','):
                        p = p.strip()
                        try:
                            providers.append(ProviderType(p))
                        except ValueError:
                            logger.warning(f"Unknown provider: {p}")
                    
                    if not providers:
                        logger.warning(f"No valid providers for prompt: {row['text'][:50]}")
                        continue
                    
                    # Parse optional fields
                    tags = [t.strip() for t in row.get('tags', '').split(',')] if row.get('tags') else []
                    
                    # Create prompt
                    prompt = self.service.create_prompt(
                        text=row['text'],
                        category=PromptCategory(row['category']),
                        providers=providers,
                        tags=tags,
                        project=row.get('project'),
                        style=row.get('style'),
                        description=row.get('description'),
                        notes=row.get('notes')
                    )
                    
                    created_prompts.append(prompt)
                    logger.info(f"Created prompt {prompt.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to create prompt from row: {e}")
                    logger.debug(f"Row data: {row}")
        
        logger.info(f"Created {len(created_prompts)} prompts from CSV")
        return created_prompts
    
    def batch_update_ratings(self, 
                           prompt_ids: List[str],
                           rating_function: Callable[[Prompt], Optional[float]]) -> int:
        """Update ratings for multiple prompts using a custom function.
        
        Args:
            prompt_ids: List of prompt IDs to update
            rating_function: Function that takes a Prompt and returns a rating
            
        Returns:
            Number of prompts updated
        """
        updated = 0
        
        for prompt_id in prompt_ids:
            prompt = self.service.get_prompt(prompt_id)
            if not prompt:
                logger.warning(f"Prompt not found: {prompt_id}")
                continue
            
            new_rating = rating_function(prompt)
            if new_rating is not None:
                prompt.effectiveness_rating = new_rating
                self.service.update_prompt(prompt)
                updated += 1
                logger.debug(f"Updated rating for {prompt_id} to {new_rating}")
        
        logger.info(f"Updated ratings for {updated} prompts")
        return updated
    
    def batch_tag_prompts(self,
                         prompts: List[Prompt],
                         tag_function: Callable[[Prompt], List[str]]) -> int:
        """Add tags to multiple prompts using a custom function.
        
        Args:
            prompts: List of prompts to tag
            tag_function: Function that takes a Prompt and returns tags to add
            
        Returns:
            Number of prompts tagged
        """
        tagged = 0
        
        for prompt in prompts:
            new_tags = tag_function(prompt)
            if new_tags:
                # Add unique tags
                existing = set(prompt.tags)
                for tag in new_tags:
                    if tag not in existing:
                        prompt.tags.append(tag)
                
                self.service.update_prompt(prompt)
                tagged += 1
                logger.debug(f"Added tags to {prompt.id}: {new_tags}")
        
        logger.info(f"Tagged {tagged} prompts")
        return tagged
    
    def batch_analyze_effectiveness(self, 
                                  category: Optional[PromptCategory] = None,
                                  min_uses: int = 3) -> Dict[str, Any]:
        """Analyze effectiveness across multiple prompts.
        
        Args:
            category: Filter by category
            min_uses: Minimum uses to include in analysis
            
        Returns:
            Analysis results
        """
        prompts = self.service.search_prompts(category=category)
        
        # Filter by minimum uses
        analyzed_prompts = [p for p in prompts if p.use_count >= min_uses]
        
        if not analyzed_prompts:
            return {"error": "No prompts with sufficient usage data"}
        
        # Calculate statistics
        success_rates = [p.success_rate() for p in analyzed_prompts]
        ratings = [p.effectiveness_rating for p in analyzed_prompts if p.effectiveness_rating]
        
        # Group by provider
        by_provider = {}
        for prompt in analyzed_prompts:
            for provider in prompt.providers:
                prov = provider.value
                if prov not in by_provider:
                    by_provider[prov] = {
                        "count": 0,
                        "total_uses": 0,
                        "total_successes": 0,
                        "ratings": []
                    }
                
                by_provider[prov]["count"] += 1
                by_provider[prov]["total_uses"] += prompt.use_count
                by_provider[prov]["total_successes"] += prompt.success_count
                if prompt.effectiveness_rating:
                    by_provider[prov]["ratings"].append(prompt.effectiveness_rating)
        
        # Calculate provider stats
        for prov, data in by_provider.items():
            data["success_rate"] = data["total_successes"] / data["total_uses"] if data["total_uses"] > 0 else 0
            data["avg_rating"] = sum(data["ratings"]) / len(data["ratings"]) if data["ratings"] else None
            del data["ratings"]  # Remove raw data
        
        return {
            "total_analyzed": len(analyzed_prompts),
            "average_success_rate": sum(success_rates) / len(success_rates),
            "average_rating": sum(ratings) / len(ratings) if ratings else None,
            "by_provider": by_provider,
            "top_performers": [
                {
                    "id": p.id,
                    "text": p.text[:100] + "..." if len(p.text) > 100 else p.text,
                    "success_rate": p.success_rate(),
                    "uses": p.use_count,
                    "rating": p.effectiveness_rating
                }
                for p in sorted(analyzed_prompts, 
                              key=lambda x: (x.success_rate(), x.use_count), 
                              reverse=True)[:10]
            ]
        }
    
    def batch_generate_variations(self,
                                base_prompt: Prompt,
                                variation_specs: List[Dict[str, str]]) -> List[Prompt]:
        """Generate multiple variations of a base prompt.
        
        Args:
            base_prompt: The base prompt to vary
            variation_specs: List of dicts with 'modification' and 'purpose' keys
            
        Returns:
            List of created variation prompts
        """
        variations = []
        
        for spec in variation_specs:
            modification = spec.get('modification', '')
            purpose = spec.get('purpose', '')
            
            # Apply modification to base text
            # This is a simple implementation - could be made more sophisticated
            if "{BASE}" in modification:
                new_text = modification.replace("{BASE}", base_prompt.text)
            else:
                new_text = f"{base_prompt.text}, {modification}"
            
            # Create variation
            variation = self.service.create_prompt(
                text=new_text,
                category=base_prompt.category,
                providers=base_prompt.providers,
                tags=base_prompt.tags + ["variation"],
                project=base_prompt.project,
                style=base_prompt.style,
                parent_id=base_prompt.id,
                notes=f"Variation: {modification}\nPurpose: {purpose}"
            )
            
            variations.append(variation)
            logger.info(f"Created variation {variation.id}")
            
            # Update base prompt's related IDs
            if variation.id not in base_prompt.related_ids:
                base_prompt.related_ids.append(variation.id)
        
        # Update base prompt
        self.service.update_prompt(base_prompt)
        
        return variations
    
    async def batch_test_prompts(self,
                               prompts: List[Prompt],
                               provider_instance: Any,
                               test_params: Optional[Dict[str, Any]] = None) -> List[Tuple[Prompt, GenerationResult]]:
        """Test multiple prompts with a provider.
        
        Args:
            prompts: List of prompts to test
            provider_instance: Provider instance with generate method
            test_params: Additional parameters for generation
            
        Returns:
            List of (prompt, result) tuples
        """
        results = []
        test_params = test_params or {}
        
        # Run generations concurrently
        tasks = []
        for prompt in prompts:
            task = provider_instance.generate(prompt.text, **test_params)
            tasks.append((prompt, task))
        
        for prompt, task in tasks:
            try:
                result = await task
                results.append((prompt, result))
                
                # Record usage
                if hasattr(provider_instance, "__class__"):
                    provider_name = provider_instance.__class__.__name__.replace("Provider", "").lower()
                    self.service.record_usage(
                        prompt_id=prompt.id,
                        provider=ProviderType(provider_name),
                        success=result.success,
                        cost=result.cost
                    )
                
            except Exception as e:
                logger.error(f"Failed to test prompt {prompt.id}: {e}")
                # Create failed result
                failed_result = GenerationResult(
                    success=False,
                    error_message=str(e)
                )
                results.append((prompt, failed_result))
        
        return results
    
    def export_batch_results(self,
                           prompts: List[Prompt],
                           output_path: Path,
                           format: str = "json") -> None:
        """Export batch of prompts with full details.
        
        Args:
            prompts: List of prompts to export
            output_path: Output file path
            format: Export format (json, csv)
        """
        if format == "json":
            data = {
                "exported_at": datetime.now().isoformat(),
                "total_prompts": len(prompts),
                "prompts": []
            }
            
            for prompt in prompts:
                prompt_data = {
                    "id": prompt.id,
                    "text": prompt.text,
                    "category": prompt.category.value,
                    "providers": [p.value for p in prompt.providers],
                    "tags": prompt.tags,
                    "project": prompt.project,
                    "style": prompt.style,
                    "effectiveness_rating": prompt.effectiveness_rating,
                    "use_count": prompt.use_count,
                    "success_rate": prompt.success_rate(),
                    "created_at": prompt.created_at.isoformat(),
                    "updated_at": prompt.updated_at.isoformat()
                }
                
                # Add usage history
                usage_history = self.service.get_usage_history(prompt.id, limit=10)
                prompt_data["recent_usage"] = [
                    {
                        "timestamp": u.timestamp.isoformat(),
                        "provider": u.provider.value,
                        "success": u.success,
                        "cost": u.cost
                    }
                    for u in usage_history
                ]
                
                data["prompts"].append(prompt_data)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif format == "csv":
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    "ID", "Text", "Category", "Providers", "Tags",
                    "Project", "Style", "Rating", "Uses", "Success Rate",
                    "Created", "Updated"
                ])
                
                # Data
                for prompt in prompts:
                    writer.writerow([
                        prompt.id,
                        prompt.text,
                        prompt.category.value,
                        ",".join([p.value for p in prompt.providers]),
                        ",".join(prompt.tags),
                        prompt.project or "",
                        prompt.style or "",
                        prompt.effectiveness_rating or "",
                        prompt.use_count,
                        f"{prompt.success_rate()*100:.1f}%",
                        prompt.created_at.strftime("%Y-%m-%d %H:%M"),
                        prompt.updated_at.strftime("%Y-%m-%d %H:%M")
                    ])
        
        logger.info(f"Exported {len(prompts)} prompts to {output_path}")


def auto_rate_by_success(prompt: Prompt) -> Optional[float]:
    """Auto-rate prompt based on success rate."""
    if prompt.use_count < 3:
        return None
    
    success_rate = prompt.success_rate()
    
    # Map success rate to 0-10 rating
    if success_rate >= 0.95:
        return 9.5
    elif success_rate >= 0.90:
        return 8.5
    elif success_rate >= 0.80:
        return 7.5
    elif success_rate >= 0.70:
        return 6.5
    elif success_rate >= 0.60:
        return 5.5
    else:
        return 4.0


def auto_tag_by_content(prompt: Prompt) -> List[str]:
    """Auto-generate tags based on prompt content."""
    tags = []
    text_lower = prompt.text.lower()
    
    # Style tags
    style_keywords = {
        "photorealistic": ["photorealistic", "realistic", "photo"],
        "anime": ["anime", "manga"],
        "cyberpunk": ["cyberpunk", "neon", "futuristic"],
        "fantasy": ["fantasy", "magical", "medieval"],
        "abstract": ["abstract", "geometric"],
        "minimalist": ["minimalist", "minimal", "simple"]
    }
    
    for tag, keywords in style_keywords.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    
    # Content tags
    content_keywords = {
        "portrait": ["portrait", "face", "person"],
        "landscape": ["landscape", "scenery", "nature"],
        "architecture": ["building", "architecture", "structure"],
        "character": ["character", "hero", "warrior"],
        "animal": ["animal", "creature", "beast"]
    }
    
    for tag, keywords in content_keywords.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    
    # Technical tags
    if any(kw in text_lower for kw in ["8k", "4k", "hd", "high resolution"]):
        tags.append("high-res")
    
    if any(kw in text_lower for kw in ["detailed", "intricate", "complex"]):
        tags.append("detailed")
    
    return tags