"""MCP tools for prompt management through AI assistants."""

from pathlib import Path
from typing import Any

from ..core.logging import get_logger
from .integration import PromptProviderIntegration
from .models import PromptCategory, ProviderType
from .project_storage import ProjectPromptStorage
from .service import PromptService
from .templates import TemplateManager

logger = get_logger(__name__)


class PromptMCPTools:
    """MCP tools for managing prompts through AI assistants."""

    def __init__(self):
        self.service = PromptService()
        self.storage = ProjectPromptStorage()
        self.templates = TemplateManager()
        self.integration = PromptProviderIntegration(self.service)

    async def find_effective_prompts(self,
                                   category: str | None = None,
                                   style: str | None = None,
                                   min_success_rate: float = 0.7) -> dict[str, Any]:
        """Find effective prompts for a given use case.

        Args:
            category: Type of generation (image_generation, video_generation, etc.)
            style: Visual style (cyberpunk, photorealistic, etc.)
            min_success_rate: Minimum success rate threshold

        Returns:
            Dictionary with found prompts and recommendations
        """
        try:
            # Parse category if provided
            category_enum = None
            if category:
                try:
                    category_enum = PromptCategory(category)
                except ValueError:
                    return {
                        "error": f"Unknown category: {category}",
                        "valid_categories": [c.value for c in PromptCategory]
                    }

            # Search for effective prompts
            prompts = self.service.get_effective_prompts(
                category=category_enum,
                min_success_rate=min_success_rate,
                min_uses=3
            )

            # Filter by style if specified
            if style:
                prompts = [p for p in prompts if p.style == style]

            # Format results
            results = []
            for prompt in prompts[:10]:  # Top 10
                results.append({
                    "id": prompt.id,
                    "text": prompt.text,
                    "providers": [p.value for p in prompt.providers],
                    "success_rate": f"{prompt.success_rate() * 100:.1f}%",
                    "uses": prompt.use_count,
                    "rating": prompt.effectiveness_rating,
                    "tags": prompt.tags,
                    "style": prompt.style,
                    "best_for": prompt.description
                })

            return {
                "found": len(results),
                "prompts": results,
                "recommendation": self._generate_recommendation(prompts, category, style)
            }

        except Exception as e:
            logger.error(f"Error finding effective prompts: {e}")
            return {"error": str(e)}

    # TODO: Review unreachable code - async def search_prompts(self,
    # TODO: Review unreachable code - query: str,
    # TODO: Review unreachable code - project: str | None = None,
    # TODO: Review unreachable code - limit: int = 20) -> dict[str, Any]:
    # TODO: Review unreachable code - """Search for prompts containing specific terms or concepts.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - query: Search query
    # TODO: Review unreachable code - project: Filter by project name
    # TODO: Review unreachable code - limit: Maximum results

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Search results with prompts
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - prompts = self.service.search_prompts(
    # TODO: Review unreachable code - query=query,
    # TODO: Review unreachable code - project=project
    # TODO: Review unreachable code - )[:limit]

    # TODO: Review unreachable code - results = []
    # TODO: Review unreachable code - for prompt in prompts:
    # TODO: Review unreachable code - results.append({
    # TODO: Review unreachable code - "id": prompt.id,
    # TODO: Review unreachable code - "text": prompt.text,
    # TODO: Review unreachable code - "category": prompt.category.value,
    # TODO: Review unreachable code - "providers": [p.value for p in prompt.providers],
    # TODO: Review unreachable code - "project": prompt.project,
    # TODO: Review unreachable code - "tags": prompt.tags,
    # TODO: Review unreachable code - "uses": prompt.use_count,
    # TODO: Review unreachable code - "success_rate": f"{prompt.success_rate() * 100:.1f}%" if prompt.use_count > 0 else "N/A"
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "query": query,
    # TODO: Review unreachable code - "found": len(results),
    # TODO: Review unreachable code - "prompts": results
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error searching prompts: {e}")
    # TODO: Review unreachable code - return {"error": str(e)}

    # TODO: Review unreachable code - async def create_prompt(self,
    # TODO: Review unreachable code - text: str,
    # TODO: Review unreachable code - category: str,
    # TODO: Review unreachable code - providers: list[str],
    # TODO: Review unreachable code - project: str | None = None,
    # TODO: Review unreachable code - tags: list[str] | None = None,
    # TODO: Review unreachable code - style: str | None = None,
    # TODO: Review unreachable code - description: str | None = None) -> dict[str, Any]:
    # TODO: Review unreachable code - """Create a new prompt with metadata.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - text: The prompt text
    # TODO: Review unreachable code - category: Category (image_generation, etc.)
    # TODO: Review unreachable code - providers: List of provider names
    # TODO: Review unreachable code - project: Project name
    # TODO: Review unreachable code - tags: List of tags
    # TODO: Review unreachable code - style: Visual style
    # TODO: Review unreachable code - description: What this prompt is good for

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Created prompt information
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Parse enums
    # TODO: Review unreachable code - category_enum = PromptCategory(category)
    # TODO: Review unreachable code - provider_enums = []
    # TODO: Review unreachable code - for p in providers:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - provider_enums.append(ProviderType(p))
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - logger.warning(f"Unknown provider: {p}")

    # TODO: Review unreachable code - if not provider_enums:
    # TODO: Review unreachable code - return {"error": "No valid providers specified"}

    # TODO: Review unreachable code - # Create prompt
    # TODO: Review unreachable code - prompt = self.service.create_prompt(
    # TODO: Review unreachable code - text=text,
    # TODO: Review unreachable code - category=category_enum,
    # TODO: Review unreachable code - providers=provider_enums,
    # TODO: Review unreachable code - project=project,
    # TODO: Review unreachable code - tags=tags or [],
    # TODO: Review unreachable code - style=style,
    # TODO: Review unreachable code - description=description
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Save to project if specified
    # TODO: Review unreachable code - if project:
    # TODO: Review unreachable code - project_path = self._find_project_path(project)
    # TODO: Review unreachable code - if project_path:
    # TODO: Review unreachable code - self.storage.save_to_project(prompt, project_path)

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "success": True,
    # TODO: Review unreachable code - "prompt": {
    # TODO: Review unreachable code - "id": prompt.id,
    # TODO: Review unreachable code - "text": prompt.text,
    # TODO: Review unreachable code - "category": prompt.category.value,
    # TODO: Review unreachable code - "providers": [p.value for p in prompt.providers],
    # TODO: Review unreachable code - "project": prompt.project,
    # TODO: Review unreachable code - "tags": prompt.tags
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - "message": f"Created prompt {prompt.id}"
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error creating prompt: {e}")
    # TODO: Review unreachable code - return {"error": str(e)}

    # TODO: Review unreachable code - async def get_project_prompts(self, project_name: str) -> dict[str, Any]:
    # TODO: Review unreachable code - """Get all prompts for a specific project with insights.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_name: Name of the project

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project prompts and statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - data = self.integration.find_prompts_for_project(project_name)

    # TODO: Review unreachable code - # Format prompts
    # TODO: Review unreachable code - prompts = []
    # TODO: Review unreachable code - for prompt in data["prompts"][:20]:  # Limit to 20 for readability
    # TODO: Review unreachable code - prompts.append({
    # TODO: Review unreachable code - "id": prompt.id,
    # TODO: Review unreachable code - "text": prompt.text[:100] + "..." if len(prompt.text) > 100 else prompt.text,
    # TODO: Review unreachable code - "category": prompt.category.value,
    # TODO: Review unreachable code - "effectiveness": prompt.effectiveness_rating,
    # TODO: Review unreachable code - "success_rate": f"{prompt.success_rate() * 100:.1f}%" if prompt.use_count > 0 else "N/A",
    # TODO: Review unreachable code - "uses": prompt.use_count
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "project": project_name,
    # TODO: Review unreachable code - "statistics": data["statistics"],
    # TODO: Review unreachable code - "prompts": prompts,
    # TODO: Review unreachable code - "total_prompts": len(data["prompts"])
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error getting project prompts: {e}")
    # TODO: Review unreachable code - return {"error": str(e)}

    # TODO: Review unreachable code - async def render_template(self,
    # TODO: Review unreachable code - template_name: str,
    # TODO: Review unreachable code - variables: dict[str, str],
    # TODO: Review unreachable code - save_as_prompt: bool = False,
    # TODO: Review unreachable code - project: str | None = None) -> dict[str, Any]:
    # TODO: Review unreachable code - """Render a prompt template with variables.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - template_name: Name of the template
    # TODO: Review unreachable code - variables: Variable values
    # TODO: Review unreachable code - save_as_prompt: Whether to save the result
    # TODO: Review unreachable code - project: Project to save to

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Rendered prompt
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - template = self.templates.get_template(template_name)
    # TODO: Review unreachable code - if not template:
    # TODO: Review unreachable code - available = self.templates.list_templates()
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "error": f"Template '{template_name}' not found",
    # TODO: Review unreachable code - "available_templates": available
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Check for missing variables
    # TODO: Review unreachable code - missing = [v for v in template.variables if v not in variables
    # TODO: Review unreachable code - and (not template.default_values or v not in template.default_values)]
    # TODO: Review unreachable code - if missing:
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "error": "Missing required variables",
    # TODO: Review unreachable code - "missing": missing,
    # TODO: Review unreachable code - "template_variables": template.variables
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Render
    # TODO: Review unreachable code - rendered = template.render(**variables)

    # TODO: Review unreachable code - result = {
    # TODO: Review unreachable code - "template": template_name,
    # TODO: Review unreachable code - "rendered": rendered,
    # TODO: Review unreachable code - "category": template.category.value,
    # TODO: Review unreachable code - "providers": [p.value for p in template.providers]
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Save if requested
    # TODO: Review unreachable code - if save_as_prompt:
    # TODO: Review unreachable code - prompt = template.to_prompt(**variables, project=project)
    # TODO: Review unreachable code - self.service.db.add_prompt(prompt)
    # TODO: Review unreachable code - result["saved_prompt_id"] = prompt.id
    # TODO: Review unreachable code - result["message"] = f"Saved as prompt {prompt.id}"

    # TODO: Review unreachable code - return result

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error rendering template: {e}")
    # TODO: Review unreachable code - return {"error": str(e)}

    # TODO: Review unreachable code - async def track_prompt_usage(self,
    # TODO: Review unreachable code - prompt_id: str,
    # TODO: Review unreachable code - provider: str,
    # TODO: Review unreachable code - success: bool,
    # TODO: Review unreachable code - cost: float | None = None,
    # TODO: Review unreachable code - notes: str | None = None) -> dict[str, Any]:
    # TODO: Review unreachable code - """Track usage of a prompt.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - prompt_id: Prompt ID or partial ID
    # TODO: Review unreachable code - provider: Provider used
    # TODO: Review unreachable code - success: Whether generation was successful
    # TODO: Review unreachable code - cost: Cost of generation
    # TODO: Review unreachable code - notes: Additional notes

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Usage tracking result
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Find prompt by partial ID
    # TODO: Review unreachable code - prompt = self._find_prompt_by_partial_id(prompt_id)
    # TODO: Review unreachable code - if not prompt:
    # TODO: Review unreachable code - return {"error": f"Prompt not found: {prompt_id}"}

    # TODO: Review unreachable code - # Parse provider
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - provider_enum = ProviderType(provider)
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "error": f"Unknown provider: {provider}",
    # TODO: Review unreachable code - "valid_providers": [p.value for p in ProviderType]
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Record usage
    # TODO: Review unreachable code - usage = self.service.record_usage(
    # TODO: Review unreachable code - prompt_id=prompt.id,
    # TODO: Review unreachable code - provider=provider_enum,
    # TODO: Review unreachable code - success=success,
    # TODO: Review unreachable code - cost=cost,
    # TODO: Review unreachable code - notes=notes
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Get updated stats
    # TODO: Review unreachable code - updated_prompt = self.service.get_prompt(prompt.id)

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "success": True,
    # TODO: Review unreachable code - "usage_id": usage.id,
    # TODO: Review unreachable code - "prompt_stats": {
    # TODO: Review unreachable code - "total_uses": updated_prompt.use_count,
    # TODO: Review unreachable code - "success_rate": f"{updated_prompt.success_rate() * 100:.1f}%",
    # TODO: Review unreachable code - "total_successes": updated_prompt.success_count
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error tracking usage: {e}")
    # TODO: Review unreachable code - return {"error": str(e)}

    # TODO: Review unreachable code - async def suggest_improvements(self, prompt_id: str) -> dict[str, Any]:
    # TODO: Review unreachable code - """Suggest improvements for a prompt based on its performance.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - prompt_id: Prompt ID or partial ID

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Improvement suggestions
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - prompt = self._find_prompt_by_partial_id(prompt_id)
    # TODO: Review unreachable code - if not prompt:
    # TODO: Review unreachable code - return {"error": f"Prompt not found: {prompt_id}"}

    # TODO: Review unreachable code - suggestions = []

    # TODO: Review unreachable code - # Analyze performance
    # TODO: Review unreachable code - if prompt.use_count < 3:
    # TODO: Review unreachable code - suggestions.append({
    # TODO: Review unreachable code - "type": "needs_more_data",
    # TODO: Review unreachable code - "message": "This prompt needs more usage data for accurate analysis"
    # TODO: Review unreachable code - })
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - success_rate = prompt.success_rate()

    # TODO: Review unreachable code - if success_rate < 0.5:
    # TODO: Review unreachable code - suggestions.append({
    # TODO: Review unreachable code - "type": "low_success_rate",
    # TODO: Review unreachable code - "message": f"Success rate is only {success_rate*100:.1f}%",
    # TODO: Review unreachable code - "recommendation": "Consider revising the prompt or trying different providers"
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - # Find similar successful prompts
    # TODO: Review unreachable code - similar = self.service.find_similar(prompt.id, limit=5)
    # TODO: Review unreachable code - successful_similar = [p for p in similar if p.success_rate() > 0.8 and p.use_count >= 5]

    # TODO: Review unreachable code - if successful_similar:
    # TODO: Review unreachable code - suggestions.append({
    # TODO: Review unreachable code - "type": "successful_similar",
    # TODO: Review unreachable code - "message": "Found similar prompts with better performance",
    # TODO: Review unreachable code - "examples": [
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "id": p.id,
    # TODO: Review unreachable code - "text": p.text[:100] + "..." if len(p.text) > 100 else p.text,
    # TODO: Review unreachable code - "success_rate": f"{p.success_rate() * 100:.1f}%"
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - for p in successful_similar[:3]
    # TODO: Review unreachable code - ]
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - # Style suggestions
    # TODO: Review unreachable code - if not prompt.style and success_rate < 0.7:
    # TODO: Review unreachable code - suggestions.append({
    # TODO: Review unreachable code - "type": "missing_style",
    # TODO: Review unreachable code - "message": "Adding a specific style might improve results",
    # TODO: Review unreachable code - "recommendation": "Try adding style tags like 'photorealistic', 'artistic', etc."
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - # Provider suggestions
    # TODO: Review unreachable code - if len(prompt.providers) == 1:
    # TODO: Review unreachable code - suggestions.append({
    # TODO: Review unreachable code - "type": "single_provider",
    # TODO: Review unreachable code - "message": "This prompt is only tested with one provider",
    # TODO: Review unreachable code - "recommendation": "Try testing with other providers to find the best match"
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "prompt_id": prompt.id,
    # TODO: Review unreachable code - "current_performance": {
    # TODO: Review unreachable code - "uses": prompt.use_count,
    # TODO: Review unreachable code - "success_rate": f"{prompt.success_rate() * 100:.1f}%",
    # TODO: Review unreachable code - "rating": prompt.effectiveness_rating
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - "suggestions": suggestions
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error generating suggestions: {e}")
    # TODO: Review unreachable code - return {"error": str(e)}

    # TODO: Review unreachable code - def _find_prompt_by_partial_id(self, partial_id: str) -> Any | None:
    # TODO: Review unreachable code - """Find a prompt by partial ID match."""
    # TODO: Review unreachable code - if len(partial_id) == 36:  # Full UUID
    # TODO: Review unreachable code - return self.service.get_prompt(partial_id)

    # TODO: Review unreachable code - # Search for partial match
    # TODO: Review unreachable code - all_prompts = self.service.search_prompts()
    # TODO: Review unreachable code - matches = [p for p in all_prompts if p.id.startswith(partial_id)]

    # TODO: Review unreachable code - if len(matches) == 1:
    # TODO: Review unreachable code - return matches[0]
    # TODO: Review unreachable code - elif len(matches) > 1:
    # TODO: Review unreachable code - logger.warning(f"Multiple prompts match '{partial_id}'")
    # TODO: Review unreachable code - return matches[0]  # Return first match

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def _find_project_path(self, project_name: str) -> Path | None:
    # TODO: Review unreachable code - """Find project path by name."""
    # TODO: Review unreachable code - # Check common project locations
    # TODO: Review unreachable code - possible_paths = [
    # TODO: Review unreachable code - Path.home() / "Projects" / project_name,
    # TODO: Review unreachable code - Path.home() / "Documents" / "Projects" / project_name,
    # TODO: Review unreachable code - Path.home() / "AI" / project_name,
    # TODO: Review unreachable code - Path.cwd() / project_name
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - for path in possible_paths:
    # TODO: Review unreachable code - if path.exists() and path.is_dir():
    # TODO: Review unreachable code - return path

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def _generate_recommendation(self, prompts: list[Any],
    # TODO: Review unreachable code - category: str | None,
    # TODO: Review unreachable code - style: str | None) -> str:
    # TODO: Review unreachable code - """Generate recommendation based on found prompts."""
    # TODO: Review unreachable code - if not prompts:
    # TODO: Review unreachable code - return "No effective prompts found. Consider creating new ones for this use case."

    # TODO: Review unreachable code - # Analyze patterns
    # TODO: Review unreachable code - providers_count = {}
    # TODO: Review unreachable code - avg_success = sum(p.success_rate() for p in prompts) / len(prompts)

    # TODO: Review unreachable code - for prompt in prompts:
    # TODO: Review unreachable code - for provider in prompt.providers:
    # TODO: Review unreachable code - providers_count[provider.value] = providers_count.get(provider.value, 0) + 1

    # TODO: Review unreachable code - best_provider = max(providers_count, key=providers_count.get)

    # TODO: Review unreachable code - recommendation = f"Based on {len(prompts)} effective prompts"
    # TODO: Review unreachable code - if category:
    # TODO: Review unreachable code - recommendation += f" for {category}"
    # TODO: Review unreachable code - if style:
    # TODO: Review unreachable code - recommendation += f" in {style} style"
    # TODO: Review unreachable code - recommendation += f": Average success rate is {avg_success*100:.1f}%. "
    # TODO: Review unreachable code - recommendation += f"{best_provider} appears to work best for this type of content."

    # TODO: Review unreachable code - return recommendation


# MCP tool definitions for registration
MCP_TOOLS = [
    {
        "name": "prompt_find_effective",
        "description": "Find effective prompts for a specific use case",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Type of generation (image_generation, video_generation, etc.)",
                    "enum": ["image_generation", "video_generation", "music_generation", "text_generation", "style_transfer", "enhancement", "analysis"]
                },
                "style": {
                    "type": "string",
                    "description": "Visual style (cyberpunk, photorealistic, anime, etc.)"
                },
                "min_success_rate": {
                    "type": "number",
                    "description": "Minimum success rate (0-1)",
                    "default": 0.7
                }
            }
        }
    },
    {
        "name": "prompt_search",
        "description": "Search for prompts containing specific terms or concepts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "project": {
                    "type": "string",
                    "description": "Filter by project name"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 20
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "prompt_create",
        "description": "Create a new prompt with metadata",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The prompt text"
                },
                "category": {
                    "type": "string",
                    "description": "Category",
                    "enum": ["image_generation", "video_generation", "music_generation", "text_generation", "style_transfer", "enhancement", "analysis"]
                },
                "providers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of provider names"
                },
                "project": {
                    "type": "string",
                    "description": "Project name"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags"
                },
                "style": {
                    "type": "string",
                    "description": "Visual style"
                },
                "description": {
                    "type": "string",
                    "description": "What this prompt is good for"
                }
            },
            "required": ["text", "category", "providers"]
        }
    },
    {
        "name": "prompt_track_usage",
        "description": "Track usage of a prompt",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt_id": {
                    "type": "string",
                    "description": "Prompt ID (supports partial matching)"
                },
                "provider": {
                    "type": "string",
                    "description": "Provider used"
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether generation was successful"
                },
                "cost": {
                    "type": "number",
                    "description": "Cost of generation"
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes"
                }
            },
            "required": ["prompt_id", "provider", "success"]
        }
    },
    {
        "name": "prompt_suggest_improvements",
        "description": "Get improvement suggestions for a prompt",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt_id": {
                    "type": "string",
                    "description": "Prompt ID (supports partial matching)"
                }
            },
            "required": ["prompt_id"]
        }
    }
]
