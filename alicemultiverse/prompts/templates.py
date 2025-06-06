"""Template system for creating and managing prompt templates."""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import json
from dataclasses import dataclass

from ..core.logging import get_logger
from .models import Prompt, PromptCategory, ProviderType

logger = get_logger(__name__)


@dataclass
class PromptTemplate:
    """A reusable prompt template with variable substitution."""
    
    name: str
    template_text: str
    category: PromptCategory
    providers: List[ProviderType]
    variables: Dict[str, str]  # variable_name -> description
    default_values: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    style: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    
    def render(self, **kwargs) -> str:
        """Render the template with provided variables.
        
        Args:
            **kwargs: Variable values to substitute
            
        Returns:
            Rendered prompt text
        """
        text = self.template_text
        
        # Apply default values for missing variables
        if self.default_values:
            for var, default in self.default_values.items():
                if var not in kwargs:
                    kwargs[var] = default
        
        # Check for missing required variables
        missing = []
        for var in self.variables:
            if var not in kwargs and (not self.default_values or var not in self.default_values):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
        
        # Substitute variables
        for var, value in kwargs.items():
            pattern = f"{{{var}}}"
            text = text.replace(pattern, str(value))
        
        return text
    
    def to_prompt(self, **kwargs) -> Prompt:
        """Create a Prompt instance from this template.
        
        Args:
            **kwargs: Variable values and additional prompt fields
            
        Returns:
            Prompt instance
        """
        import uuid
        
        # Extract non-variable kwargs
        prompt_kwargs = {}
        variable_kwargs = {}
        
        for key, value in kwargs.items():
            if key in self.variables:
                variable_kwargs[key] = value
            else:
                prompt_kwargs[key] = value
        
        # Render the text
        text = self.render(**variable_kwargs)
        
        # Create prompt
        return Prompt(
            id=prompt_kwargs.get("id", str(uuid.uuid4())),
            text=text,
            category=self.category,
            providers=self.providers,
            tags=prompt_kwargs.get("tags", self.tags or []),
            style=prompt_kwargs.get("style", self.style),
            context={
                **(self.context or {}),
                "from_template": self.name,
                "template_variables": variable_kwargs
            },
            notes=prompt_kwargs.get("notes", self.notes),
            **{k: v for k, v in prompt_kwargs.items() 
               if k not in ["id", "tags", "style", "notes"]}
        )


class TemplateManager:
    """Manages prompt templates."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            templates_dir = Path.home() / ".alice" / "templates"
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in templates."""
        # Character Portrait Template
        self._templates["character_portrait"] = PromptTemplate(
            name="character_portrait",
            template_text="Portrait of {character_type} with {expression} expression, {style} art style, {lighting} lighting",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY, ProviderType.FLUX, ProviderType.STABLE_DIFFUSION],
            variables={
                "character_type": "Type of character (e.g., warrior, mage, cyberpunk hacker)",
                "expression": "Facial expression (e.g., determined, mysterious, friendly)",
                "style": "Art style (e.g., realistic, anime, oil painting)",
                "lighting": "Lighting style (e.g., dramatic, soft, neon)"
            },
            default_values={
                "lighting": "dramatic"
            },
            tags=["portrait", "character", "template"],
            examples=[{
                "variables": {
                    "character_type": "cyberpunk hacker",
                    "expression": "focused",
                    "style": "neon noir",
                    "lighting": "neon"
                },
                "result": "Portrait of cyberpunk hacker with focused expression, neon noir art style, neon lighting"
            }]
        )
        
        # Landscape Template
        self._templates["landscape"] = PromptTemplate(
            name="landscape",
            template_text="{location} landscape at {time_of_day}, {weather} weather, {style} style, {mood} mood",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY, ProviderType.FLUX],
            variables={
                "location": "Location type (e.g., mountain, forest, desert, city)",
                "time_of_day": "Time (e.g., dawn, sunset, night, golden hour)",
                "weather": "Weather condition (e.g., clear, foggy, rainy, stormy)",
                "style": "Visual style (e.g., photorealistic, painted, stylized)",
                "mood": "Atmosphere (e.g., serene, dramatic, mysterious)"
            },
            tags=["landscape", "nature", "scenery", "template"]
        )
        
        # Product Shot Template
        self._templates["product_shot"] = PromptTemplate(
            name="product_shot",
            template_text="{product} on {surface}, {background} background, {lighting} lighting, product photography, {angle} angle",
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY, ProviderType.FIREFLY],
            variables={
                "product": "Product description",
                "surface": "Surface type (e.g., white table, wooden desk, marble)",
                "background": "Background style (e.g., gradient, solid color, blurred)",
                "lighting": "Lighting setup (e.g., studio, natural, dramatic)",
                "angle": "Camera angle (e.g., 45-degree, top-down, eye-level)"
            },
            default_values={
                "surface": "white table",
                "background": "gradient",
                "lighting": "studio",
                "angle": "45-degree"
            },
            style="commercial",
            tags=["product", "photography", "commercial", "template"]
        )
        
        # Video Generation Template
        self._templates["video_scene"] = PromptTemplate(
            name="video_scene",
            template_text="{action} in {location}, {camera_movement} camera movement, {duration} seconds, {style} style",
            category=PromptCategory.VIDEO_GENERATION,
            providers=[ProviderType.RUNWAY, ProviderType.KLING],
            variables={
                "action": "Main action or movement",
                "location": "Scene location",
                "camera_movement": "Camera motion (e.g., static, pan, zoom, tracking)",
                "duration": "Video duration",
                "style": "Visual style"
            },
            default_values={
                "camera_movement": "smooth pan",
                "duration": "5"
            },
            tags=["video", "animation", "motion", "template"]
        )
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        # Check loaded templates first
        if name in self._templates:
            return self._templates[name]
        
        # Try loading from file
        template_file = self.templates_dir / f"{name}.yaml"
        if template_file.exists():
            return self.load_template(template_file)
        
        return None
    
    def list_templates(self) -> List[str]:
        """List all available template names."""
        # Built-in templates
        templates = list(self._templates.keys())
        
        # File-based templates
        for file in self.templates_dir.glob("*.yaml"):
            name = file.stem
            if name not in templates:
                templates.append(name)
        
        return sorted(templates)
    
    def save_template(self, template: PromptTemplate, overwrite: bool = False) -> Path:
        """Save a template to file."""
        file_path = self.templates_dir / f"{template.name}.yaml"
        
        if file_path.exists() and not overwrite:
            raise ValueError(f"Template '{template.name}' already exists")
        
        data = {
            "name": template.name,
            "template": template.template_text,
            "category": template.category.value,
            "providers": [p.value for p in template.providers],
            "variables": template.variables,
            "default_values": template.default_values,
            "tags": template.tags,
            "style": template.style,
            "context": template.context,
            "examples": template.examples,
            "notes": template.notes
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        # Cache it
        self._templates[template.name] = template
        
        logger.info(f"Saved template '{template.name}' to {file_path}")
        return file_path
    
    def load_template(self, file_path: Path) -> PromptTemplate:
        """Load a template from file."""
        with open(file_path) as f:
            data = yaml.safe_load(f)
        
        # Convert string values to enums
        category = PromptCategory(data["category"])
        providers = [ProviderType(p) for p in data["providers"]]
        
        template = PromptTemplate(
            name=data["name"],
            template_text=data["template"],
            category=category,
            providers=providers,
            variables=data["variables"],
            default_values=data.get("default_values"),
            tags=data.get("tags"),
            style=data.get("style"),
            context=data.get("context"),
            examples=data.get("examples"),
            notes=data.get("notes")
        )
        
        # Cache it
        self._templates[template.name] = template
        
        return template
    
    def create_from_prompt(self, prompt: Prompt, template_name: str,
                          variables: Optional[List[str]] = None) -> PromptTemplate:
        """Create a template from an existing prompt.
        
        Args:
            prompt: Source prompt
            template_name: Name for the template
            variables: List of variable names to extract
            
        Returns:
            Created template
        """
        text = prompt.text
        
        if variables is None:
            # Try to auto-detect variables (words in curly braces)
            variables = re.findall(r'\{(\w+)\}', text)
            if not variables:
                # Create generic variables
                variables = ["subject", "style", "mood"]
                text = f"{{{variables[0]}}} in {{{variables[1]}}} style with {{{variables[2]}}} mood"
        
        # Create variable descriptions
        variable_desc = {var: f"Description for {var}" for var in variables}
        
        template = PromptTemplate(
            name=template_name,
            template_text=text,
            category=prompt.category,
            providers=prompt.providers,
            variables=variable_desc,
            tags=prompt.tags,
            style=prompt.style,
            context=prompt.context,
            notes=f"Template created from prompt: {prompt.id}"
        )
        
        return template
    
    def render_all_examples(self, template_name: str) -> List[str]:
        """Render all examples for a template."""
        template = self.get_template(template_name)
        if not template or not template.examples:
            return []
        
        results = []
        for example in template.examples:
            if "variables" in example:
                try:
                    rendered = template.render(**example["variables"])
                    results.append(rendered)
                except Exception as e:
                    logger.warning(f"Failed to render example: {e}")
        
        return results


def create_template_from_variations(prompts: List[Prompt], 
                                  template_name: str) -> PromptTemplate:
    """Create a template by analyzing prompt variations.
    
    This function attempts to identify common patterns and variable parts
    in a set of related prompts.
    
    Args:
        prompts: List of related prompts
        template_name: Name for the template
        
    Returns:
        Created template
    """
    if not prompts:
        raise ValueError("No prompts provided")
    
    # Find common tokens
    tokenized = [p.text.split() for p in prompts]
    common_tokens = set(tokenized[0])
    
    for tokens in tokenized[1:]:
        common_tokens &= set(tokens)
    
    # TODO: Implement more sophisticated pattern detection
    # For now, create a simple template
    base_prompt = prompts[0]
    
    template = PromptTemplate(
        name=template_name,
        template_text="{subject} with {variation}",
        category=base_prompt.category,
        providers=list(set(p for prompt in prompts for p in prompt.providers)),
        variables={
            "subject": "Main subject or concept",
            "variation": "Variation or modification"
        },
        tags=list(set(tag for prompt in prompts for tag in prompt.tags)),
        notes=f"Template created from {len(prompts)} prompt variations"
    )
    
    return template