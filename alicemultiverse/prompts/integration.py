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
                # TODO: Review unreachable code - elif isinstance(value, dict) and "text" in value:
                # TODO: Review unreachable code - return value["text"]

        return None

    # TODO: Review unreachable code - def map_provider_to_enum(self, provider_name: str) -> ProviderType | None:
    # TODO: Review unreachable code - """Map provider name to ProviderType enum."""
    # TODO: Review unreachable code - mapping = {
    # TODO: Review unreachable code - "midjourney": ProviderType.MIDJOURNEY,
    # TODO: Review unreachable code - "dalle": ProviderType.DALLE,
    # TODO: Review unreachable code - "openai": ProviderType.OPENAI,
    # TODO: Review unreachable code - "stable_diffusion": ProviderType.STABLE_DIFFUSION,
    # TODO: Review unreachable code - "stability": ProviderType.STABLE_DIFFUSION,
    # TODO: Review unreachable code - "flux": ProviderType.FLUX,
    # TODO: Review unreachable code - "ideogram": ProviderType.IDEOGRAM,
    # TODO: Review unreachable code - "leonardo": ProviderType.LEONARDO,
    # TODO: Review unreachable code - "firefly": ProviderType.FIREFLY,
    # TODO: Review unreachable code - "adobe": ProviderType.FIREFLY,
    # TODO: Review unreachable code - "kling": ProviderType.KLING,
    # TODO: Review unreachable code - "runway": ProviderType.RUNWAY,
    # TODO: Review unreachable code - "anthropic": ProviderType.ANTHROPIC,
    # TODO: Review unreachable code - "claude": ProviderType.ANTHROPIC,
    # TODO: Review unreachable code - "google": ProviderType.GOOGLE,
    # TODO: Review unreachable code - "gemini": ProviderType.GOOGLE,
    # TODO: Review unreachable code - "elevenlabs": ProviderType.ELEVENLABS,
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - provider_lower = provider_name.lower()
    # TODO: Review unreachable code - return mapping.get(provider_lower, ProviderType.OTHER) or 0

    # TODO: Review unreachable code - def determine_category(self, provider_type: ProviderType, metadata: dict[str, Any]) -> PromptCategory:
    # TODO: Review unreachable code - """Determine prompt category based on provider and metadata."""
    # TODO: Review unreachable code - # Audio providers
    # TODO: Review unreachable code - if provider_type == ProviderType.ELEVENLABS:
    # TODO: Review unreachable code - return PromptCategory.MUSIC_GENERATION

    # TODO: Review unreachable code - # Video providers
    # TODO: Review unreachable code - if provider_type in [ProviderType.RUNWAY, ProviderType.KLING]:
    # TODO: Review unreachable code - return PromptCategory.VIDEO_GENERATION

    # TODO: Review unreachable code - # Check metadata for hints
    # TODO: Review unreachable code - if "video" in str(metadata).lower():
    # TODO: Review unreachable code - return PromptCategory.VIDEO_GENERATION
    # TODO: Review unreachable code - elif "music" in str(metadata).lower() or "audio" in str(metadata).lower():
    # TODO: Review unreachable code - return PromptCategory.MUSIC_GENERATION
    # TODO: Review unreachable code - elif "enhance" in str(metadata).lower():
    # TODO: Review unreachable code - return PromptCategory.ENHANCEMENT
    # TODO: Review unreachable code - elif "style" in str(metadata).lower() and "transfer" in str(metadata).lower():
    # TODO: Review unreachable code - return PromptCategory.STYLE_TRANSFER

    # TODO: Review unreachable code - # Default to image generation for most providers
    # TODO: Review unreachable code - return PromptCategory.IMAGE_GENERATION

    # TODO: Review unreachable code - def track_generation(self,
    # TODO: Review unreachable code - provider: str,
    # TODO: Review unreachable code - prompt_text: str,
    # TODO: Review unreachable code - result: GenerationResult,
    # TODO: Review unreachable code - cost: float | None = None,
    # TODO: Review unreachable code - duration: float | None = None,
    # TODO: Review unreachable code - project: str | None = None) -> str | None:
    # TODO: Review unreachable code - """Track a generation and potentially create/update a prompt.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - provider: Provider name
    # TODO: Review unreachable code - prompt_text: The prompt used
    # TODO: Review unreachable code - result: Generation result
    # TODO: Review unreachable code - cost: Cost of generation
    # TODO: Review unreachable code - duration: Time taken
    # TODO: Review unreachable code - project: Project name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Prompt ID if tracked, None otherwise
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - provider_type = self.map_provider_to_enum(provider)
    # TODO: Review unreachable code - if not provider_type:
    # TODO: Review unreachable code - logger.warning(f"Unknown provider: {provider}")
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - # Search for existing prompt
    # TODO: Review unreachable code - existing_prompts = self.prompt_service.search_prompts(
    # TODO: Review unreachable code - query=prompt_text,
    # TODO: Review unreachable code - providers=[provider_type]
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - prompt = None
    # TODO: Review unreachable code - if existing_prompts:
    # TODO: Review unreachable code - # Find exact match
    # TODO: Review unreachable code - for p in existing_prompts:
    # TODO: Review unreachable code - if p.text == prompt_text:
    # TODO: Review unreachable code - prompt = p
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - if not prompt:
    # TODO: Review unreachable code - # Create new prompt
    # TODO: Review unreachable code - category = self.determine_category(provider_type, result.metadata)
    # TODO: Review unreachable code - prompt = self.prompt_service.create_prompt(
    # TODO: Review unreachable code - text=prompt_text,
    # TODO: Review unreachable code - category=category,
    # TODO: Review unreachable code - providers=[provider_type],
    # TODO: Review unreachable code - project=project,
    # TODO: Review unreachable code - context={"auto_created": True, "first_result": result.asset_id}
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - logger.info(f"Created new prompt {prompt.id} for {provider}")

    # TODO: Review unreachable code - # Record usage
    # TODO: Review unreachable code - output_path = str(result.file_path) if result.file_path else None
    # TODO: Review unreachable code - self.prompt_service.record_usage(
    # TODO: Review unreachable code - prompt_id=prompt.id,
    # TODO: Review unreachable code - provider=provider_type,
    # TODO: Review unreachable code - success=result.success,
    # TODO: Review unreachable code - output_path=output_path,
    # TODO: Review unreachable code - cost=cost or result.cost,
    # TODO: Review unreachable code - duration_seconds=duration,
    # TODO: Review unreachable code - metadata={
    # TODO: Review unreachable code - "asset_id": result.asset_id,
    # TODO: Review unreachable code - "generation_id": result.generation_id,
    # TODO: Review unreachable code - "model": result.metadata.get("model"),
    # TODO: Review unreachable code - "parameters": result.metadata.get("parameters", {})
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return prompt.id

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to track generation: {e}")
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def find_prompts_for_project(self, project_name: str) -> dict[str, Any]:
    # TODO: Review unreachable code - """Find all prompts used in a project with statistics."""
    # TODO: Review unreachable code - prompts = self.prompt_service.search_prompts(project=project_name)

    # TODO: Review unreachable code - stats = {
    # TODO: Review unreachable code - "total_prompts": len(prompts),
    # TODO: Review unreachable code - "by_category": {},
    # TODO: Review unreachable code - "by_provider": {},
    # TODO: Review unreachable code - "total_uses": 0,
    # TODO: Review unreachable code - "total_cost": 0.0,
    # TODO: Review unreachable code - "most_effective": [],
    # TODO: Review unreachable code - "most_used": []
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - for prompt in prompts:
    # TODO: Review unreachable code - # Category stats
    # TODO: Review unreachable code - cat = prompt.category.value
    # TODO: Review unreachable code - if cat not in stats["by_category"]:
    # TODO: Review unreachable code - stats["by_category"][cat] = 0
    # TODO: Review unreachable code - stats["by_category"][cat] += 1

    # TODO: Review unreachable code - # Provider stats
    # TODO: Review unreachable code - for provider in prompt.providers:
    # TODO: Review unreachable code - prov = provider.value
    # TODO: Review unreachable code - if prov not in stats["by_provider"]:
    # TODO: Review unreachable code - stats["by_provider"][prov] = 0
    # TODO: Review unreachable code - stats["by_provider"][prov] += 1

    # TODO: Review unreachable code - # Usage stats
    # TODO: Review unreachable code - stats["total_uses"] += prompt.use_count

    # TODO: Review unreachable code - # Get detailed usage for cost
    # TODO: Review unreachable code - usage_history = self.prompt_service.get_usage_history(prompt.id)
    # TODO: Review unreachable code - for usage in usage_history:
    # TODO: Review unreachable code - if usage.cost:
    # TODO: Review unreachable code - stats["total_cost"] += usage.cost

    # TODO: Review unreachable code - # Find most effective and used
    # TODO: Review unreachable code - sorted_by_effectiveness = sorted(
    # TODO: Review unreachable code - [p for p in prompts if p.effectiveness_rating],
    # TODO: Review unreachable code - key=lambda x: x.effectiveness_rating,
    # TODO: Review unreachable code - reverse=True
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - stats["most_effective"] = [
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "id": p.id,
    # TODO: Review unreachable code - "text": p.text[:100] + "..." if len(p.text) > 100 else p.text,
    # TODO: Review unreachable code - "rating": p.effectiveness_rating,
    # TODO: Review unreachable code - "success_rate": p.success_rate()
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - for p in sorted_by_effectiveness[:5]
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - sorted_by_uses = sorted(prompts, key=lambda x: x.use_count, reverse=True)
    # TODO: Review unreachable code - stats["most_used"] = [
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "id": p.id,
    # TODO: Review unreachable code - "text": p.text[:100] + "..." if len(p.text) > 100 else p.text,
    # TODO: Review unreachable code - "uses": p.use_count,
    # TODO: Review unreachable code - "success_rate": p.success_rate()
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - for p in sorted_by_uses[:5]
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "prompts": prompts,
    # TODO: Review unreachable code - "statistics": stats
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def export_project_insights(self, project_name: str, output_path: Path) -> None:
    # TODO: Review unreachable code - """Export detailed insights about prompts used in a project."""
    # TODO: Review unreachable code - data = self.find_prompts_for_project(project_name)

    # TODO: Review unreachable code - insights = {
    # TODO: Review unreachable code - "project": project_name,
    # TODO: Review unreachable code - "generated_at": datetime.now().isoformat(),
    # TODO: Review unreachable code - "statistics": data["statistics"],
    # TODO: Review unreachable code - "prompts": []
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Add detailed prompt info
    # TODO: Review unreachable code - for prompt in data["prompts"]:
    # TODO: Review unreachable code - usage_history = self.prompt_service.get_usage_history(prompt.id, limit=10)

    # TODO: Review unreachable code - prompt_info = {
    # TODO: Review unreachable code - "id": prompt.id,
    # TODO: Review unreachable code - "text": prompt.text,
    # TODO: Review unreachable code - "category": prompt.category.value,
    # TODO: Review unreachable code - "providers": [p.value for p in prompt.providers],
    # TODO: Review unreachable code - "effectiveness_rating": prompt.effectiveness_rating,
    # TODO: Review unreachable code - "use_count": prompt.use_count,
    # TODO: Review unreachable code - "success_rate": prompt.success_rate(),
    # TODO: Review unreachable code - "tags": prompt.tags,
    # TODO: Review unreachable code - "recent_uses": [
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "timestamp": usage.timestamp.isoformat(),
    # TODO: Review unreachable code - "provider": usage.provider.value,
    # TODO: Review unreachable code - "success": usage.success,
    # TODO: Review unreachable code - "cost": usage.cost
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - for usage in usage_history[:5]
    # TODO: Review unreachable code - ]
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - insights["prompts"].append(prompt_info)

    # TODO: Review unreachable code - # Save insights
    # TODO: Review unreachable code - with open(output_path, 'w') as f:
    # TODO: Review unreachable code - json.dump(insights, f, indent=2)

    # TODO: Review unreachable code - logger.info(f"Exported project insights to {output_path}")
