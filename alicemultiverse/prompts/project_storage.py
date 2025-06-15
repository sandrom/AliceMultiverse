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
                if p["id"] == prompt.id:
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

    def load_from_project(self, project_path: Path) -> list[Prompt]:
        """Load all prompts from a project directory.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of prompts found in the project
        """
        prompts_dir = project_path / self.PROMPTS_DIR
        if not prompts_dir.exists():
            return []

        # Try loading from YAML first, then JSON
        yaml_file = prompts_dir / self.PROMPTS_FILE_YAML
        json_file = prompts_dir / self.PROMPTS_FILE_JSON

        prompts_data = None
        if yaml_file.exists():
            with open(yaml_file) as f:
                prompts_data = yaml.safe_load(f)
        elif json_file.exists():
            with open(json_file) as f:
                prompts_data = json.load(f)
        else:
            return []

        prompts = []
        for prompt_dict in prompts_data.get("prompts", []):
            prompt = self._dict_to_prompt(prompt_dict)
            prompts.append(prompt)

        logger.info(f"Loaded {len(prompts)} prompts from project {project_path.name}")
        return prompts

    def sync_project_to_index(self, project_path: Path) -> int:
        """Sync prompts from a project to the central index.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Number of prompts synced
        """
        prompts = self.load_from_project(project_path)
        synced = 0

        for prompt in prompts:
            # Check if prompt exists in index
            existing = self.service.get_prompt(prompt.id)
            if existing:
                # Update if project version is newer
                if prompt.updated_at > existing.updated_at:
                    self.service.update_prompt(prompt)
                    synced += 1
            else:
                # Add new prompt to index
                self.service.db.add_prompt(prompt)
                synced += 1

        logger.info(f"Synced {synced} prompts from project {project_path.name}")
        return synced

    def sync_index_to_project(self, project_name: str, project_path: Path) -> int:
        """Sync prompts from the index to a project.
        
        Args:
            project_name: Name of the project to filter by
            project_path: Path to the project directory
            
        Returns:
            Number of prompts synced
        """
        # Find all prompts for this project
        prompts = self.service.search_prompts(project=project_name)

        synced = 0
        for prompt in prompts:
            self.save_to_project(prompt, project_path)
            synced += 1

        logger.info(f"Synced {synced} prompts to project {project_path.name}")
        return synced

    def discover_project_prompts(self, base_paths: list[Path]) -> dict[str, list[Prompt]]:
        """Discover all prompts in project directories.
        
        Args:
            base_paths: List of base paths to search for projects
            
        Returns:
            Dictionary mapping project names to their prompts
        """
        project_prompts = {}

        for base_path in base_paths:
            if not base_path.exists():
                continue

            # Look for project directories with prompts
            for project_dir in base_path.iterdir():
                if not project_dir.is_dir():
                    continue

                prompts_dir = project_dir / self.PROMPTS_DIR
                if prompts_dir.exists():
                    prompts = self.load_from_project(project_dir)
                    if prompts:
                        project_prompts[project_dir.name] = prompts

        return project_prompts

    def export_project_prompts(self, project_path: Path, output_path: Path) -> None:
        """Export all prompts from a project to a standalone file.
        
        Args:
            project_path: Path to the project directory
            output_path: Path for the export file
        """
        prompts = self.load_from_project(project_path)

        export_data = {
            "project": project_path.name,
            "exported_at": datetime.now().isoformat(),
            "prompt_count": len(prompts),
            "prompts": [self._prompt_to_dict(p) for p in prompts]
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(prompts)} prompts from {project_path.name} to {output_path}")

    def create_prompt_template(self, project_path: Path, template_name: str = "example") -> Path:
        """Create a prompt template file in the project.
        
        Args:
            project_path: Path to the project directory
            template_name: Name for the template
            
        Returns:
            Path to the created template file
        """
        templates_dir = project_path / self.PROMPTS_DIR / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        template_file = templates_dir / f"{template_name}.yaml"

        if template_name == "example":
            # Create a comprehensive example
            PromptYAMLFormatter.create_example_prompt_yaml(template_file)
        else:
            # Create a basic template
            template = f"""# {template_name} Prompt Template
# Edit this template for your project's prompts

prompt: "Your prompt text here with {{variable}} placeholders"

category: image_generation  # or video_generation, music_generation, etc.

providers:
  - midjourney
  - flux
  - stable_diffusion

description: "What this prompt creates"

tags:
  - {template_name}
  - your_tags_here

style: your_style  # e.g., photorealistic, anime, abstract

project: {project_path.name}

context:
  # Add any parameters or settings
  aspect_ratio: "16:9"
  quality: "high"
  
notes: |
  Add usage notes, tips, and variations here.
  This is a multiline field for detailed information.

# Variables for template substitution
variables:
  variable: "Description of what this variable represents"
"""

            with open(template_file, 'w') as f:
                f.write(template)

        logger.info(f"Created prompt template {template_name} in {project_path.name}")
        return template_file

    def initialize_project_prompts(self, project_path: Path) -> None:
        """Initialize prompt storage in a project with examples and templates."""
        prompts_dir = project_path / self.PROMPTS_DIR
        prompts_dir.mkdir(parents=True, exist_ok=True)

        # Create initial structure
        readme_file = prompts_dir / "README.md"
        if not readme_file.exists():
            readme_content = f"""# Project Prompts

This directory contains AI prompts used in the {project_path.name} project.

## Structure

- `prompts.yaml` - Main collection of all project prompts
- `*.yaml` - Individual prompt files (one per prompt)
- `templates/` - Prompt templates and examples
- `exports/` - Exported prompt collections

## Usage

Prompts are automatically synced with Alice's central prompt database.

### Adding a new prompt
```bash
alice prompts add -t "your prompt" -c image_generation -p midjourney --project {project_path.name}
```

### Syncing with central database
```bash
# Pull prompts from central database
alice prompts project {project_path} --sync-from-index

# Push prompts to central database  
alice prompts project {project_path} --sync-to-index
```

### Viewing project prompts
```bash
alice prompts project {project_path}
```

## Format

Prompts are stored in YAML format for easy reading and editing.
See `templates/example.yaml` for the full format specification.
"""
            with open(readme_file, 'w') as f:
                f.write(readme_content)

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
