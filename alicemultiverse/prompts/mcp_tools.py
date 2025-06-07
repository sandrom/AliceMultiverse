"""MCP tools for prompt management through AI assistants."""

from typing import Dict, Any, List, Optional
from pathlib import Path

from ..core.logging import get_logger
from .service import PromptService
from .project_storage import ProjectPromptStorage
from .models import PromptCategory, ProviderType
from .templates import TemplateManager
from .integration import PromptProviderIntegration

logger = get_logger(__name__)


class PromptMCPTools:
    """MCP tools for managing prompts through AI assistants."""
    
    def __init__(self):
        self.service = PromptService()
        self.storage = ProjectPromptStorage()
        self.templates = TemplateManager()
        self.integration = PromptProviderIntegration(self.service)
    
    async def find_effective_prompts(self, 
                                   category: Optional[str] = None,
                                   style: Optional[str] = None,
                                   min_success_rate: float = 0.7) -> Dict[str, Any]:
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
    
    async def search_prompts(self, 
                           query: str,
                           project: Optional[str] = None,
                           limit: int = 20) -> Dict[str, Any]:
        """Search for prompts containing specific terms or concepts.
        
        Args:
            query: Search query
            project: Filter by project name
            limit: Maximum results
            
        Returns:
            Search results with prompts
        """
        try:
            prompts = self.service.search_prompts(
                query=query,
                project=project
            )[:limit]
            
            results = []
            for prompt in prompts:
                results.append({
                    "id": prompt.id,
                    "text": prompt.text,
                    "category": prompt.category.value,
                    "providers": [p.value for p in prompt.providers],
                    "project": prompt.project,
                    "tags": prompt.tags,
                    "uses": prompt.use_count,
                    "success_rate": f"{prompt.success_rate() * 100:.1f}%" if prompt.use_count > 0 else "N/A"
                })
            
            return {
                "query": query,
                "found": len(results),
                "prompts": results
            }
            
        except Exception as e:
            logger.error(f"Error searching prompts: {e}")
            return {"error": str(e)}
    
    async def create_prompt(self,
                          text: str,
                          category: str,
                          providers: List[str],
                          project: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          style: Optional[str] = None,
                          description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new prompt with metadata.
        
        Args:
            text: The prompt text
            category: Category (image_generation, etc.)
            providers: List of provider names
            project: Project name
            tags: List of tags
            style: Visual style
            description: What this prompt is good for
            
        Returns:
            Created prompt information
        """
        try:
            # Parse enums
            category_enum = PromptCategory(category)
            provider_enums = []
            for p in providers:
                try:
                    provider_enums.append(ProviderType(p))
                except ValueError:
                    logger.warning(f"Unknown provider: {p}")
            
            if not provider_enums:
                return {"error": "No valid providers specified"}
            
            # Create prompt
            prompt = self.service.create_prompt(
                text=text,
                category=category_enum,
                providers=provider_enums,
                project=project,
                tags=tags or [],
                style=style,
                description=description
            )
            
            # Save to project if specified
            if project:
                project_path = self._find_project_path(project)
                if project_path:
                    self.storage.save_to_project(prompt, project_path)
            
            return {
                "success": True,
                "prompt": {
                    "id": prompt.id,
                    "text": prompt.text,
                    "category": prompt.category.value,
                    "providers": [p.value for p in prompt.providers],
                    "project": prompt.project,
                    "tags": prompt.tags
                },
                "message": f"Created prompt {prompt.id}"
            }
            
        except Exception as e:
            logger.error(f"Error creating prompt: {e}")
            return {"error": str(e)}
    
    async def get_project_prompts(self, project_name: str) -> Dict[str, Any]:
        """Get all prompts for a specific project with insights.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project prompts and statistics
        """
        try:
            data = self.integration.find_prompts_for_project(project_name)
            
            # Format prompts
            prompts = []
            for prompt in data["prompts"][:20]:  # Limit to 20 for readability
                prompts.append({
                    "id": prompt.id,
                    "text": prompt.text[:100] + "..." if len(prompt.text) > 100 else prompt.text,
                    "category": prompt.category.value,
                    "effectiveness": prompt.effectiveness_rating,
                    "success_rate": f"{prompt.success_rate() * 100:.1f}%" if prompt.use_count > 0 else "N/A",
                    "uses": prompt.use_count
                })
            
            return {
                "project": project_name,
                "statistics": data["statistics"],
                "prompts": prompts,
                "total_prompts": len(data["prompts"])
            }
            
        except Exception as e:
            logger.error(f"Error getting project prompts: {e}")
            return {"error": str(e)}
    
    async def render_template(self,
                            template_name: str,
                            variables: Dict[str, str],
                            save_as_prompt: bool = False,
                            project: Optional[str] = None) -> Dict[str, Any]:
        """Render a prompt template with variables.
        
        Args:
            template_name: Name of the template
            variables: Variable values
            save_as_prompt: Whether to save the result
            project: Project to save to
            
        Returns:
            Rendered prompt
        """
        try:
            template = self.templates.get_template(template_name)
            if not template:
                available = self.templates.list_templates()
                return {
                    "error": f"Template '{template_name}' not found",
                    "available_templates": available
                }
            
            # Check for missing variables
            missing = [v for v in template.variables if v not in variables 
                      and (not template.default_values or v not in template.default_values)]
            if missing:
                return {
                    "error": "Missing required variables",
                    "missing": missing,
                    "template_variables": template.variables
                }
            
            # Render
            rendered = template.render(**variables)
            
            result = {
                "template": template_name,
                "rendered": rendered,
                "category": template.category.value,
                "providers": [p.value for p in template.providers]
            }
            
            # Save if requested
            if save_as_prompt:
                prompt = template.to_prompt(**variables, project=project)
                self.service.db.add_prompt(prompt)
                result["saved_prompt_id"] = prompt.id
                result["message"] = f"Saved as prompt {prompt.id}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return {"error": str(e)}
    
    async def track_prompt_usage(self,
                                prompt_id: str,
                                provider: str,
                                success: bool,
                                cost: Optional[float] = None,
                                notes: Optional[str] = None) -> Dict[str, Any]:
        """Track usage of a prompt.
        
        Args:
            prompt_id: Prompt ID or partial ID
            provider: Provider used
            success: Whether generation was successful
            cost: Cost of generation
            notes: Additional notes
            
        Returns:
            Usage tracking result
        """
        try:
            # Find prompt by partial ID
            prompt = self._find_prompt_by_partial_id(prompt_id)
            if not prompt:
                return {"error": f"Prompt not found: {prompt_id}"}
            
            # Parse provider
            try:
                provider_enum = ProviderType(provider)
            except ValueError:
                return {
                    "error": f"Unknown provider: {provider}",
                    "valid_providers": [p.value for p in ProviderType]
                }
            
            # Record usage
            usage = self.service.record_usage(
                prompt_id=prompt.id,
                provider=provider_enum,
                success=success,
                cost=cost,
                notes=notes
            )
            
            # Get updated stats
            updated_prompt = self.service.get_prompt(prompt.id)
            
            return {
                "success": True,
                "usage_id": usage.id,
                "prompt_stats": {
                    "total_uses": updated_prompt.use_count,
                    "success_rate": f"{updated_prompt.success_rate() * 100:.1f}%",
                    "total_successes": updated_prompt.success_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
            return {"error": str(e)}
    
    async def suggest_improvements(self, prompt_id: str) -> Dict[str, Any]:
        """Suggest improvements for a prompt based on its performance.
        
        Args:
            prompt_id: Prompt ID or partial ID
            
        Returns:
            Improvement suggestions
        """
        try:
            prompt = self._find_prompt_by_partial_id(prompt_id)
            if not prompt:
                return {"error": f"Prompt not found: {prompt_id}"}
            
            suggestions = []
            
            # Analyze performance
            if prompt.use_count < 3:
                suggestions.append({
                    "type": "needs_more_data",
                    "message": "This prompt needs more usage data for accurate analysis"
                })
            else:
                success_rate = prompt.success_rate()
                
                if success_rate < 0.5:
                    suggestions.append({
                        "type": "low_success_rate",
                        "message": f"Success rate is only {success_rate*100:.1f}%",
                        "recommendation": "Consider revising the prompt or trying different providers"
                    })
                
                # Find similar successful prompts
                similar = self.service.find_similar(prompt.id, limit=5)
                successful_similar = [p for p in similar if p.success_rate() > 0.8 and p.use_count >= 5]
                
                if successful_similar:
                    suggestions.append({
                        "type": "successful_similar",
                        "message": "Found similar prompts with better performance",
                        "examples": [
                            {
                                "id": p.id,
                                "text": p.text[:100] + "..." if len(p.text) > 100 else p.text,
                                "success_rate": f"{p.success_rate() * 100:.1f}%"
                            }
                            for p in successful_similar[:3]
                        ]
                    })
                
                # Style suggestions
                if not prompt.style and success_rate < 0.7:
                    suggestions.append({
                        "type": "missing_style",
                        "message": "Adding a specific style might improve results",
                        "recommendation": "Try adding style tags like 'photorealistic', 'artistic', etc."
                    })
                
                # Provider suggestions
                if len(prompt.providers) == 1:
                    suggestions.append({
                        "type": "single_provider",
                        "message": "This prompt is only tested with one provider",
                        "recommendation": "Try testing with other providers to find the best match"
                    })
            
            return {
                "prompt_id": prompt.id,
                "current_performance": {
                    "uses": prompt.use_count,
                    "success_rate": f"{prompt.success_rate() * 100:.1f}%",
                    "rating": prompt.effectiveness_rating
                },
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return {"error": str(e)}
    
    def _find_prompt_by_partial_id(self, partial_id: str) -> Optional[Any]:
        """Find a prompt by partial ID match."""
        if len(partial_id) == 36:  # Full UUID
            return self.service.get_prompt(partial_id)
        
        # Search for partial match
        all_prompts = self.service.search_prompts()
        matches = [p for p in all_prompts if p.id.startswith(partial_id)]
        
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            logger.warning(f"Multiple prompts match '{partial_id}'")
            return matches[0]  # Return first match
        
        return None
    
    def _find_project_path(self, project_name: str) -> Optional[Path]:
        """Find project path by name."""
        # Check common project locations
        possible_paths = [
            Path.home() / "Projects" / project_name,
            Path.home() / "Documents" / "Projects" / project_name,
            Path.home() / "AI" / project_name,
            Path.cwd() / project_name
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path
        
        return None
    
    def _generate_recommendation(self, prompts: List[Any], 
                               category: Optional[str], 
                               style: Optional[str]) -> str:
        """Generate recommendation based on found prompts."""
        if not prompts:
            return "No effective prompts found. Consider creating new ones for this use case."
        
        # Analyze patterns
        providers_count = {}
        avg_success = sum(p.success_rate() for p in prompts) / len(prompts)
        
        for prompt in prompts:
            for provider in prompt.providers:
                providers_count[provider.value] = providers_count.get(provider.value, 0) + 1
        
        best_provider = max(providers_count, key=providers_count.get)
        
        recommendation = f"Based on {len(prompts)} effective prompts"
        if category:
            recommendation += f" for {category}"
        if style:
            recommendation += f" in {style} style"
        recommendation += f": Average success rate is {avg_success*100:.1f}%. "
        recommendation += f"{best_provider} appears to work best for this type of content."
        
        return recommendation


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