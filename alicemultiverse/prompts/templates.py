"""Template system for creating and managing prompt templates."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..core.logging import get_logger
from .models import Prompt, PromptCategory, ProviderType

logger = get_logger(__name__)


@dataclass
class PromptTemplate:
    """A reusable prompt template with variable substitution."""

    name: str
    template_text: str
    category: PromptCategory
    providers: list[ProviderType]
    variables: dict[str, str]  # variable_name -> description
    default_values: dict[str, str] | None = None
    tags: list[str] | None = None
    style: str | None = None
    context: dict[str, Any] | None = None
    examples: list[dict[str, Any]] | None = None
    notes: str | None = None

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

        # TODO: Review unreachable code - # Substitute variables
        # TODO: Review unreachable code - for var, value in kwargs.items():
        # TODO: Review unreachable code - pattern = f"{{{var}}}"
        # TODO: Review unreachable code - text = text.replace(pattern, str(value))

        # TODO: Review unreachable code - return text

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

    def __init__(self, templates_dir: Path | None = None):
        if templates_dir is None:
            templates_dir = Path.home() / ".alice" / "templates"
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._templates: dict[str, PromptTemplate] = {}
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

    def get_template(self, name: str) -> PromptTemplate | None:
        """Get a template by name."""
        # Check loaded templates first
        if name in self._templates:
            return self._templates[name]

        # TODO: Review unreachable code - # Try loading from file
        # TODO: Review unreachable code - template_file = self.templates_dir / f"{name}.yaml"
        # TODO: Review unreachable code - if template_file.exists():
        # TODO: Review unreachable code - return self.load_template(template_file)

        # TODO: Review unreachable code - return None

    def list_templates(self) -> list[str]:
        """List all available template names."""
        # Built-in templates
        templates = list(self._templates.keys())

        # File-based templates
        for file in self.templates_dir.glob("*.yaml"):
            name = file.stem
            if name not in templates:
                templates.append(name)

        return sorted(templates)

    # TODO: Review unreachable code - def save_template(self, template: PromptTemplate, overwrite: bool = False) -> Path:
    # TODO: Review unreachable code - """Save a template to file."""
    # TODO: Review unreachable code - file_path = self.templates_dir / f"{template.name}.yaml"

    # TODO: Review unreachable code - if file_path.exists() and not overwrite:
    # TODO: Review unreachable code - raise ValueError(f"Template '{template.name}' already exists")

    # TODO: Review unreachable code - data = {
    # TODO: Review unreachable code - "name": template.name,
    # TODO: Review unreachable code - "template": template.template_text,
    # TODO: Review unreachable code - "category": template.category.value,
    # TODO: Review unreachable code - "providers": [p.value for p in template.providers],
    # TODO: Review unreachable code - "variables": template.variables,
    # TODO: Review unreachable code - "default_values": template.default_values,
    # TODO: Review unreachable code - "tags": template.tags,
    # TODO: Review unreachable code - "style": template.style,
    # TODO: Review unreachable code - "context": template.context,
    # TODO: Review unreachable code - "examples": template.examples,
    # TODO: Review unreachable code - "notes": template.notes
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Remove None values
    # TODO: Review unreachable code - data = {k: v for k, v in data.items() if v is not None}

    # TODO: Review unreachable code - with open(file_path, 'w') as f:
    # TODO: Review unreachable code - yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    # TODO: Review unreachable code - # Cache it
    # TODO: Review unreachable code - self._templates[template.name] = template

    # TODO: Review unreachable code - logger.info(f"Saved template '{template.name}' to {file_path}")
    # TODO: Review unreachable code - return file_path

    # TODO: Review unreachable code - def load_template(self, file_path: Path) -> PromptTemplate:
    # TODO: Review unreachable code - """Load a template from file."""
    # TODO: Review unreachable code - with open(file_path) as f:
    # TODO: Review unreachable code - data = yaml.safe_load(f)

    # TODO: Review unreachable code - # Convert string values to enums
    # TODO: Review unreachable code - category = PromptCategory(data["category"])
    # TODO: Review unreachable code - providers = [ProviderType(p) for p in data["providers"]]

    # TODO: Review unreachable code - template = PromptTemplate(
    # TODO: Review unreachable code - name=data["name"],
    # TODO: Review unreachable code - template_text=data["template"],
    # TODO: Review unreachable code - category=category,
    # TODO: Review unreachable code - providers=providers,
    # TODO: Review unreachable code - variables=data["variables"],
    # TODO: Review unreachable code - default_values=data.get("default_values"),
    # TODO: Review unreachable code - tags=data.get("tags"),
    # TODO: Review unreachable code - style=data.get("style"),
    # TODO: Review unreachable code - context=data.get("context"),
    # TODO: Review unreachable code - examples=data.get("examples"),
    # TODO: Review unreachable code - notes=data.get("notes")
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Cache it
    # TODO: Review unreachable code - self._templates[template.name] = template

    # TODO: Review unreachable code - return template

    # TODO: Review unreachable code - def create_from_prompt(self, prompt: Prompt, template_name: str,
    # TODO: Review unreachable code - variables: list[str] | None = None) -> PromptTemplate:
    # TODO: Review unreachable code - """Create a template from an existing prompt.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - prompt: Source prompt
    # TODO: Review unreachable code - template_name: Name for the template
    # TODO: Review unreachable code - variables: List of variable names to extract

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Created template
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - text = prompt.text

    # TODO: Review unreachable code - if variables is None:
    # TODO: Review unreachable code - # Try to auto-detect variables (words in curly braces)
    # TODO: Review unreachable code - variables = re.findall(r'\{(\w+)\}', text)
    # TODO: Review unreachable code - if not variables:
    # TODO: Review unreachable code - # Create generic variables
    # TODO: Review unreachable code - variables = ["subject", "style", "mood"]
    # TODO: Review unreachable code - text = f"{{{variables[0]}}} in {{{variables[1]}}} style with {{{variables[2]}}} mood"

    # TODO: Review unreachable code - # Create variable descriptions
    # TODO: Review unreachable code - variable_desc = {var: f"Description for {var}" for var in variables}

    # TODO: Review unreachable code - template = PromptTemplate(
    # TODO: Review unreachable code - name=template_name,
    # TODO: Review unreachable code - template_text=text,
    # TODO: Review unreachable code - category=prompt.category,
    # TODO: Review unreachable code - providers=prompt.providers,
    # TODO: Review unreachable code - variables=variable_desc,
    # TODO: Review unreachable code - tags=prompt.tags,
    # TODO: Review unreachable code - style=prompt.style,
    # TODO: Review unreachable code - context=prompt.context,
    # TODO: Review unreachable code - notes=f"Template created from prompt: {prompt.id}"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return template

    # TODO: Review unreachable code - def render_all_examples(self, template_name: str) -> list[str]:
    # TODO: Review unreachable code - """Render all examples for a template."""
    # TODO: Review unreachable code - template = self.get_template(template_name)
    # TODO: Review unreachable code - if not template or not template.examples:
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - results = []
    # TODO: Review unreachable code - for example in template.examples:
    # TODO: Review unreachable code - if example is not None and "variables" in example:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - rendered = template.render(**example["variables"])
    # TODO: Review unreachable code - results.append(rendered)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to render example: {e}")

    # TODO: Review unreachable code - return results


def create_template_from_variations(prompts: list[Prompt],
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

    # TODO: Review unreachable code - # Find common tokens
    # TODO: Review unreachable code - tokenized = [p.text.split() for p in prompts]
    # TODO: Review unreachable code - common_tokens = set(tokenized[0])

    # TODO: Review unreachable code - for tokens in tokenized[1:]:
    # TODO: Review unreachable code - common_tokens &= set(tokens)

    # TODO: Review unreachable code - # TODO: Implement more sophisticated pattern detection
    # TODO: Review unreachable code - # For now, create a simple template
    # TODO: Review unreachable code - base_prompt = prompts[0]

    # TODO: Review unreachable code - template = PromptTemplate(
    # TODO: Review unreachable code - name=template_name,
    # TODO: Review unreachable code - template_text="{subject} with {variation}",
    # TODO: Review unreachable code - category=base_prompt.category,
    # TODO: Review unreachable code - providers=list(set(p for prompt in prompts for p in prompt.providers)),
    # TODO: Review unreachable code - variables={
    # TODO: Review unreachable code - "subject": "Main subject or concept",
    # TODO: Review unreachable code - "variation": "Variation or modification"
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - tags=list(set(tag for prompt in prompts for tag in prompt.tags)),
    # TODO: Review unreachable code - notes=f"Template created from {len(prompts)} prompt variations"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return template
