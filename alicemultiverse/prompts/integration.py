"""Integration between prompt management and provider systems."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.logging import get_logger
from ..providers.provider_types import GenerationResult
from .models import PromptCategory, ProviderType
from .service import PromptService

logger = get_logger(__name__)


class PromptProviderIntegration:
    """Integrates prompt tracking with provider generation."""

    def __init__(self, prompt_service: PromptService | None = None):
        self.prompt_service = prompt_service or PromptService()

    def extract_prompt_from_metadata(self, metadata: dict[str, Any]) -> str | None:
        """Extract prompt text from generation metadata."""
        # Common fields where prompts are stored
        prompt_fields = ["prompt", "text", "input", "description", "query"]

        for field in prompt_fields:
            if field in metadata:
                value = metadata[field]
                if isinstance(value, str) and value:
                    return value
                elif isinstance(value, dict) and "text" in value:
                    return value["text"]

        return None

    def map_provider_to_enum(self, provider_name: str) -> ProviderType | None:
        """Map provider name to ProviderType enum."""
        mapping = {
            "midjourney": ProviderType.MIDJOURNEY,
            "dalle": ProviderType.DALLE,
            "openai": ProviderType.OPENAI,
            "stable_diffusion": ProviderType.STABLE_DIFFUSION,
            "stability": ProviderType.STABLE_DIFFUSION,
            "flux": ProviderType.FLUX,
            "ideogram": ProviderType.IDEOGRAM,
            "leonardo": ProviderType.LEONARDO,
            "firefly": ProviderType.FIREFLY,
            "adobe": ProviderType.FIREFLY,
            "kling": ProviderType.KLING,
            "runway": ProviderType.RUNWAY,
            "anthropic": ProviderType.ANTHROPIC,
            "claude": ProviderType.ANTHROPIC,
            "google": ProviderType.GOOGLE,
            "gemini": ProviderType.GOOGLE,
            "elevenlabs": ProviderType.ELEVENLABS,
        }

        provider_lower = provider_name.lower()
        return mapping.get(provider_lower, ProviderType.OTHER)

    def determine_category(self, provider_type: ProviderType, metadata: dict[str, Any]) -> PromptCategory:
        """Determine prompt category based on provider and metadata."""
        # Audio providers
        if provider_type == ProviderType.ELEVENLABS:
            return PromptCategory.MUSIC_GENERATION

        # Video providers
        if provider_type in [ProviderType.RUNWAY, ProviderType.KLING]:
            return PromptCategory.VIDEO_GENERATION

        # Check metadata for hints
        if "video" in str(metadata).lower():
            return PromptCategory.VIDEO_GENERATION
        elif "music" in str(metadata).lower() or "audio" in str(metadata).lower():
            return PromptCategory.MUSIC_GENERATION
        elif "enhance" in str(metadata).lower():
            return PromptCategory.ENHANCEMENT
        elif "style" in str(metadata).lower() and "transfer" in str(metadata).lower():
            return PromptCategory.STYLE_TRANSFER

        # Default to image generation for most providers
        return PromptCategory.IMAGE_GENERATION

    def track_generation(self,
                        provider: str,
                        prompt_text: str,
                        result: GenerationResult,
                        cost: float | None = None,
                        duration: float | None = None,
                        project: str | None = None) -> str | None:
        """Track a generation and potentially create/update a prompt.
        
        Args:
            provider: Provider name
            prompt_text: The prompt used
            result: Generation result
            cost: Cost of generation
            duration: Time taken
            project: Project name
            
        Returns:
            Prompt ID if tracked, None otherwise
        """
        try:
            provider_type = self.map_provider_to_enum(provider)
            if not provider_type:
                logger.warning(f"Unknown provider: {provider}")
                return None

            # Search for existing prompt
            existing_prompts = self.prompt_service.search_prompts(
                query=prompt_text,
                providers=[provider_type]
            )

            prompt = None
            if existing_prompts:
                # Find exact match
                for p in existing_prompts:
                    if p.text == prompt_text:
                        prompt = p
                        break

            if not prompt:
                # Create new prompt
                category = self.determine_category(provider_type, result.metadata)
                prompt = self.prompt_service.create_prompt(
                    text=prompt_text,
                    category=category,
                    providers=[provider_type],
                    project=project,
                    context={"auto_created": True, "first_result": result.asset_id}
                )
                logger.info(f"Created new prompt {prompt.id} for {provider}")

            # Record usage
            output_path = str(result.file_path) if result.file_path else None
            self.prompt_service.record_usage(
                prompt_id=prompt.id,
                provider=provider_type,
                success=result.success,
                output_path=output_path,
                cost=cost or result.cost,
                duration_seconds=duration,
                metadata={
                    "asset_id": result.asset_id,
                    "generation_id": result.generation_id,
                    "model": result.metadata.get("model"),
                    "parameters": result.metadata.get("parameters", {})
                }
            )

            return prompt.id

        except Exception as e:
            logger.error(f"Failed to track generation: {e}")
            return None

    def find_prompts_for_project(self, project_name: str) -> dict[str, Any]:
        """Find all prompts used in a project with statistics."""
        prompts = self.prompt_service.search_prompts(project=project_name)

        stats = {
            "total_prompts": len(prompts),
            "by_category": {},
            "by_provider": {},
            "total_uses": 0,
            "total_cost": 0.0,
            "most_effective": [],
            "most_used": []
        }

        for prompt in prompts:
            # Category stats
            cat = prompt.category.value
            if cat not in stats["by_category"]:
                stats["by_category"][cat] = 0
            stats["by_category"][cat] += 1

            # Provider stats
            for provider in prompt.providers:
                prov = provider.value
                if prov not in stats["by_provider"]:
                    stats["by_provider"][prov] = 0
                stats["by_provider"][prov] += 1

            # Usage stats
            stats["total_uses"] += prompt.use_count

            # Get detailed usage for cost
            usage_history = self.prompt_service.get_usage_history(prompt.id)
            for usage in usage_history:
                if usage.cost:
                    stats["total_cost"] += usage.cost

        # Find most effective and used
        sorted_by_effectiveness = sorted(
            [p for p in prompts if p.effectiveness_rating],
            key=lambda x: x.effectiveness_rating,
            reverse=True
        )
        stats["most_effective"] = [
            {
                "id": p.id,
                "text": p.text[:100] + "..." if len(p.text) > 100 else p.text,
                "rating": p.effectiveness_rating,
                "success_rate": p.success_rate()
            }
            for p in sorted_by_effectiveness[:5]
        ]

        sorted_by_uses = sorted(prompts, key=lambda x: x.use_count, reverse=True)
        stats["most_used"] = [
            {
                "id": p.id,
                "text": p.text[:100] + "..." if len(p.text) > 100 else p.text,
                "uses": p.use_count,
                "success_rate": p.success_rate()
            }
            for p in sorted_by_uses[:5]
        ]

        return {
            "prompts": prompts,
            "statistics": stats
        }

    def export_project_insights(self, project_name: str, output_path: Path) -> None:
        """Export detailed insights about prompts used in a project."""
        data = self.find_prompts_for_project(project_name)

        insights = {
            "project": project_name,
            "generated_at": datetime.now().isoformat(),
            "statistics": data["statistics"],
            "prompts": []
        }

        # Add detailed prompt info
        for prompt in data["prompts"]:
            usage_history = self.prompt_service.get_usage_history(prompt.id, limit=10)

            prompt_info = {
                "id": prompt.id,
                "text": prompt.text,
                "category": prompt.category.value,
                "providers": [p.value for p in prompt.providers],
                "effectiveness_rating": prompt.effectiveness_rating,
                "use_count": prompt.use_count,
                "success_rate": prompt.success_rate(),
                "tags": prompt.tags,
                "recent_uses": [
                    {
                        "timestamp": usage.timestamp.isoformat(),
                        "provider": usage.provider.value,
                        "success": usage.success,
                        "cost": usage.cost
                    }
                    for usage in usage_history[:5]
                ]
            }

            insights["prompts"].append(prompt_info)

        # Save insights
        with open(output_path, 'w') as f:
            json.dump(insights, f, indent=2)

        logger.info(f"Exported project insights to {output_path}")
