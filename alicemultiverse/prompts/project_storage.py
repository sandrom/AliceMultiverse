"""Project-based storage for prompts.

This module allows prompts to be stored within project directories while
maintaining a central searchable index.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import yaml

from ..core.logging import get_logger
from .models import Prompt, PromptCategory, ProviderType
from .service import PromptService
from .yaml_format import PromptYAMLFormatter

logger = get_logger(__name__)


class ProjectPromptStorage:
    """Manages prompts stored in project directories."""

    PROMPTS_DIR = ".alice/prompts"
    PROMPTS_FILE_JSON = "prompts.json"
    PROMPTS_FILE_YAML = "prompts.yaml"

    def __init__(self, service: PromptService | None = None, format: Literal["json", "yaml"] = "yaml"):
        self.service = service or PromptService()
        self.format = format
        self.prompts_file = self.PROMPTS_FILE_YAML if format == "yaml" else self.PROMPTS_FILE_JSON

    def save_to_project(self, prompt: Prompt, project_path: Path) -> Path:
        """Save a prompt to a project directory.

        Args:
            prompt: The prompt to save
            project_path: Path to the project directory

        Returns:
            Path to the saved prompt file
        """
        # Create prompts directory in project
        prompts_dir = project_path / self.PROMPTS_DIR
        prompts_dir.mkdir(parents=True, exist_ok=True)

        # Check for existing file in either format
        prompts_file = prompts_dir / self.prompts_file
        yaml_file = prompts_dir / self.PROMPTS_FILE_YAML
        json_file = prompts_dir / self.PROMPTS_FILE_JSON

        # Load existing prompts (check both formats)
        prompts_data = None
        if yaml_file.exists() and self.format == "yaml":
            with open(yaml_file) as f:
                prompts_data = yaml.safe_load(f) or {"prompts": [], "metadata": {}}
        elif json_file.exists():
            with open(json_file) as f:
                prompts_data = json.load(f)
        else:
            prompts_data = {"prompts": [], "metadata": {}}

        # Convert prompt to dict
        prompt_dict = self._prompt_to_dict(prompt)

        # Check if prompt already exists
        existing_ids = [p["id"] for p in prompts_data["prompts"]]
        if prompt.id in existing_ids:
            # Update existing
            for i, p in enumerate(prompts_data["prompts"]):
                if p is not None and p["id"] == prompt.id:
                    prompts_data["prompts"][i] = prompt_dict
                    break
        else:
            # Add new
            prompts_data["prompts"].append(prompt_dict)

        # Update metadata
        prompts_data["metadata"]["last_updated"] = datetime.now().isoformat()
        prompts_data["metadata"]["count"] = len(prompts_data["prompts"])

        # Save in chosen format
        if self.format == "yaml":
            with open(prompts_file, 'w') as f:
                yaml.dump(prompts_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        else:
            with open(prompts_file, 'w') as f:
                json.dump(prompts_data, f, indent=2)

        logger.info(f"Saved prompt {prompt.id} to project {project_path.name} as {self.format}")

        # Also save individual prompt file in readable YAML format
        individual_file = prompts_dir / f"{prompt.id}.yaml"
        PromptYAMLFormatter.save_readable_prompt(prompt, individual_file)

        return individual_file

    # TODO: Review unreachable code - def load_from_project(self, project_path: Path) -> list[Prompt]:
    # TODO: Review unreachable code - """Load all prompts from a project directory.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_path: Path to the project directory

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of prompts found in the project
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - prompts_dir = project_path / self.PROMPTS_DIR
    # TODO: Review unreachable code - if not prompts_dir.exists():
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - # Try loading from YAML first, then JSON
    # TODO: Review unreachable code - yaml_file = prompts_dir / self.PROMPTS_FILE_YAML
    # TODO: Review unreachable code - json_file = prompts_dir / self.PROMPTS_FILE_JSON

    # TODO: Review unreachable code - prompts_data = None
    # TODO: Review unreachable code - if yaml_file.exists():
    # TODO: Review unreachable code - with open(yaml_file) as f:
    # TODO: Review unreachable code - prompts_data = yaml.safe_load(f)
    # TODO: Review unreachable code - elif json_file.exists():
    # TODO: Review unreachable code - with open(json_file) as f:
    # TODO: Review unreachable code - prompts_data = json.load(f)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - prompts = []
    # TODO: Review unreachable code - for prompt_dict in prompts_data.get("prompts", []):
    # TODO: Review unreachable code - prompt = self._dict_to_prompt(prompt_dict)
    # TODO: Review unreachable code - prompts.append(prompt)

    # TODO: Review unreachable code - logger.info(f"Loaded {len(prompts)} prompts from project {project_path.name}")
    # TODO: Review unreachable code - return prompts

    # TODO: Review unreachable code - def sync_project_to_index(self, project_path: Path) -> int:
    # TODO: Review unreachable code - """Sync prompts from a project to the central index.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_path: Path to the project directory

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Number of prompts synced
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - prompts = self.load_from_project(project_path)
    # TODO: Review unreachable code - synced = 0

    # TODO: Review unreachable code - for prompt in prompts:
    # TODO: Review unreachable code - # Check if prompt exists in index
    # TODO: Review unreachable code - existing = self.service.get_prompt(prompt.id)
    # TODO: Review unreachable code - if existing:
    # TODO: Review unreachable code - # Update if project version is newer
    # TODO: Review unreachable code - if prompt.updated_at > existing.updated_at:
    # TODO: Review unreachable code - self.service.update_prompt(prompt)
    # TODO: Review unreachable code - synced += 1
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Add new prompt to index
    # TODO: Review unreachable code - self.service.db.add_prompt(prompt)
    # TODO: Review unreachable code - synced += 1

    # TODO: Review unreachable code - logger.info(f"Synced {synced} prompts from project {project_path.name}")
    # TODO: Review unreachable code - return synced

    # TODO: Review unreachable code - def sync_index_to_project(self, project_name: str, project_path: Path) -> int:
    # TODO: Review unreachable code - """Sync prompts from the index to a project.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_name: Name of the project to filter by
    # TODO: Review unreachable code - project_path: Path to the project directory

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Number of prompts synced
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Find all prompts for this project
    # TODO: Review unreachable code - prompts = self.service.search_prompts(project=project_name)

    # TODO: Review unreachable code - synced = 0
    # TODO: Review unreachable code - for prompt in prompts:
    # TODO: Review unreachable code - self.save_to_project(prompt, project_path)
    # TODO: Review unreachable code - synced += 1

    # TODO: Review unreachable code - logger.info(f"Synced {synced} prompts to project {project_path.name}")
    # TODO: Review unreachable code - return synced

    # TODO: Review unreachable code - def discover_project_prompts(self, base_paths: list[Path]) -> dict[str, list[Prompt]]:
    # TODO: Review unreachable code - """Discover all prompts in project directories.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - base_paths: List of base paths to search for projects

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary mapping project names to their prompts
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - project_prompts = {}

    # TODO: Review unreachable code - for base_path in base_paths:
    # TODO: Review unreachable code - if not base_path.exists():
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - # Look for project directories with prompts
    # TODO: Review unreachable code - for project_dir in base_path.iterdir():
    # TODO: Review unreachable code - if not project_dir.is_dir():
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - prompts_dir = project_dir / self.PROMPTS_DIR
    # TODO: Review unreachable code - if prompts_dir.exists():
    # TODO: Review unreachable code - prompts = self.load_from_project(project_dir)
    # TODO: Review unreachable code - if prompts:
    # TODO: Review unreachable code - project_prompts[project_dir.name] = prompts

    # TODO: Review unreachable code - return project_prompts

    # TODO: Review unreachable code - def export_project_prompts(self, project_path: Path, output_path: Path) -> None:
    # TODO: Review unreachable code - """Export all prompts from a project to a standalone file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_path: Path to the project directory
    # TODO: Review unreachable code - output_path: Path for the export file
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - prompts = self.load_from_project(project_path)

    # TODO: Review unreachable code - export_data = {
    # TODO: Review unreachable code - "project": project_path.name,
    # TODO: Review unreachable code - "exported_at": datetime.now().isoformat(),
    # TODO: Review unreachable code - "prompt_count": len(prompts),
    # TODO: Review unreachable code - "prompts": [self._prompt_to_dict(p) for p in prompts]
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - output_path.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - with open(output_path, 'w') as f:
    # TODO: Review unreachable code - json.dump(export_data, f, indent=2)

    # TODO: Review unreachable code - logger.info(f"Exported {len(prompts)} prompts from {project_path.name} to {output_path}")

    # TODO: Review unreachable code - def create_prompt_template(self, project_path: Path, template_name: str = "example") -> Path:
    # TODO: Review unreachable code - """Create a prompt template file in the project.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_path: Path to the project directory
    # TODO: Review unreachable code - template_name: Name for the template

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Path to the created template file
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - templates_dir = project_path / self.PROMPTS_DIR / "templates"
    # TODO: Review unreachable code - templates_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Review unreachable code - template_file = templates_dir / f"{template_name}.yaml"

    # TODO: Review unreachable code - if template_name == "example":
    # TODO: Review unreachable code - # Create a comprehensive example
    # TODO: Review unreachable code - PromptYAMLFormatter.create_example_prompt_yaml(template_file)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Create a basic template
    # TODO: Review unreachable code - template = f"""# {template_name} Prompt Template
# TODO: Review unreachable code - # Edit this template for your project's prompts
# TODO: Review unreachable code - 
# TODO: Review unreachable code - prompt: "Your prompt text here with {{variable}} placeholders"
# TODO: Review unreachable code - 
# TODO: Review unreachable code - category: image_generation  # or video_generation, music_generation, etc.
# TODO: Review unreachable code - 
# TODO: Review unreachable code - providers:
# TODO: Review unreachable code -   - midjourney
# TODO: Review unreachable code -   - flux
# TODO: Review unreachable code -   - stable_diffusion
# TODO: Review unreachable code - 
# TODO: Review unreachable code - description: "What this prompt creates"
# TODO: Review unreachable code - 
# TODO: Review unreachable code - tags:
# TODO: Review unreachable code -   - {template_name}
# TODO: Review unreachable code -   - your_tags_here
# TODO: Review unreachable code - 
# TODO: Review unreachable code - style: your_style  # e.g., photorealistic, anime, abstract
# TODO: Review unreachable code - 
# TODO: Review unreachable code - project: {project_path.name}
# TODO: Review unreachable code - 
# TODO: Review unreachable code - context:
# TODO: Review unreachable code -   # Add any parameters or settings
# TODO: Review unreachable code -   aspect_ratio: "16:9"
# TODO: Review unreachable code -   quality: "high"
# TODO: Review unreachable code - 
# TODO: Review unreachable code - notes: |
# TODO: Review unreachable code -   Add usage notes, tips, and variations here.
# TODO: Review unreachable code -   This is a multiline field for detailed information.
# TODO: Review unreachable code - 
# TODO: Review unreachable code - # Variables for template substitution
# TODO: Review unreachable code - variables:
# TODO: Review unreachable code -   variable: "Description of what this variable represents"
# TODO: Review unreachable code - # TODO: Review unreachable code - """

            # TODO: Review unreachable code - with open(template_file, 'w') as f:
            # TODO: Review unreachable code -     f.write(template)

        logger.info(f"Created prompt template {template_name} in {project_path.name}")
        return template_file

    # TODO: Review unreachable code - def initialize_project_prompts(self, project_path: Path) -> None:
    # TODO: Review unreachable code - """Initialize prompt storage in a project with examples and templates."""
    # TODO: Review unreachable code - prompts_dir = project_path / self.PROMPTS_DIR
    # TODO: Review unreachable code - prompts_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Review unreachable code - # Create initial structure
    # TODO: Review unreachable code - readme_file = prompts_dir / "README.md"
    # TODO: Review unreachable code - if not readme_file.exists():
    # TODO: Review unreachable code - readme_content = f"""# Project Prompts
# TODO: Review unreachable code - 
# TODO: Review unreachable code - This directory contains AI prompts used in the {project_path.name} project.
# TODO: Review unreachable code - 
# TODO: Review unreachable code - ## Structure
# TODO: Review unreachable code - 
# TODO: Review unreachable code - - `prompts.yaml` - Main collection of all project prompts
# TODO: Review unreachable code - - `*.yaml` - Individual prompt files (one per prompt)
# TODO: Review unreachable code - - `templates/` - Prompt templates and examples
# TODO: Review unreachable code - - `exports/` - Exported prompt collections
# TODO: Review unreachable code - 
# TODO: Review unreachable code - ## Usage
# TODO: Review unreachable code - 
# TODO: Review unreachable code - Prompts are automatically synced with Alice's central prompt database.
# TODO: Review unreachable code - 
# TODO: Review unreachable code - ### Adding a new prompt
# TODO: Review unreachable code - ```bash
# TODO: Review unreachable code - alice prompts add -t "your prompt" -c image_generation -p midjourney --project {project_path.name}
# TODO: Review unreachable code - ```
# TODO: Review unreachable code - 
# TODO: Review unreachable code - ### Syncing with central database
# TODO: Review unreachable code - ```bash
# TODO: Review unreachable code - # Pull prompts from central database
# TODO: Review unreachable code - alice prompts project {project_path} --sync-from-index
# TODO: Review unreachable code - 
# TODO: Review unreachable code - # Push prompts to central database
# TODO: Review unreachable code - alice prompts project {project_path} --sync-to-index
# TODO: Review unreachable code - ```
# TODO: Review unreachable code - 
# TODO: Review unreachable code - ### Viewing project prompts
# TODO: Review unreachable code - ```bash
# TODO: Review unreachable code - alice prompts project {project_path}
# TODO: Review unreachable code - ```
# TODO: Review unreachable code - 
# TODO: Review unreachable code - ## Format
# TODO: Review unreachable code - 
# TODO: Review unreachable code - Prompts are stored in YAML format for easy reading and editing.
# TODO: Review unreachable code - See `templates/example.yaml` for the full format specification.
# TODO: Review unreachable code - """
            # TODO: Review unreachable code - with open(readme_file, 'w') as f:
            # TODO: Review unreachable code -     f.write(readme_content)

        # Create example template
        self.create_prompt_template(project_path, "example")

        # Create directories for organization
        (prompts_dir / "exports").mkdir(exist_ok=True)

        logger.info(f"Initialized prompt storage for project {project_path.name}")

    def _prompt_to_dict(self, prompt: Prompt) -> dict[str, Any]:
        """Convert a Prompt object to a dictionary."""
        return {
            "id": prompt.id,
            "text": prompt.text,
            "category": prompt.category.value,
            "providers": [p.value for p in prompt.providers],
            "tags": prompt.tags,
            "project": prompt.project,
            "style": prompt.style,
            "effectiveness_rating": prompt.effectiveness_rating,
            "use_count": prompt.use_count,
            "success_count": prompt.success_count,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat(),
            "description": prompt.description,
            "notes": prompt.notes,
            "context": prompt.context,
            "parent_id": prompt.parent_id,
            "related_ids": prompt.related_ids,
            "keywords": prompt.keywords
        }

    def _dict_to_prompt(self, data: dict[str, Any]) -> Prompt:
        """Convert a dictionary to a Prompt object."""
        return Prompt(
            id=data["id"],
            text=data["text"],
            category=PromptCategory(data["category"]),
            providers=[ProviderType(p) for p in data["providers"]],
            tags=data.get("tags", []),
            project=data.get("project"),
            style=data.get("style"),
            effectiveness_rating=data.get("effectiveness_rating"),
            use_count=data.get("use_count", 0),
            success_count=data.get("success_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            description=data.get("description"),
            notes=data.get("notes"),
            context=data.get("context", {}),
            parent_id=data.get("parent_id"),
            related_ids=data.get("related_ids", []),
            keywords=data.get("keywords", [])
        )
