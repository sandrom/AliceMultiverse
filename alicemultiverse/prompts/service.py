"""High-level service for prompt management."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.logging import get_logger
from .database import PromptDatabase
from .models import Prompt, PromptCategory, PromptSearchCriteria, PromptUsage, ProviderType

logger = get_logger(__name__)


class PromptService:
    """Service for managing prompts and their usage."""

    def __init__(self, db_path: Path | None = None):
        self.db = PromptDatabase(db_path)

    def create_prompt(
        self,
        text: str,
        category: PromptCategory,
        providers: list[ProviderType],
        tags: list[str] | None = None,
        project: str | None = None,
        style: str | None = None,
        description: str | None = None,
        notes: str | None = None,
        context: dict[str, Any] | None = None,
        parent_id: str | None = None,
        keywords: list[str] | None = None
    ) -> Prompt:
        """Create a new prompt."""
        prompt = Prompt(
            id=hashlib.sha256(f"{text}:{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            text=text,
            category=category,
            providers=providers,
            tags=tags or [],
            project=project,
            style=style,
            description=description,
            notes=notes,
            context=context or {},
            parent_id=parent_id,
            keywords=keywords or []
        )

        self.db.add_prompt(prompt)
        logger.info(f"Created prompt {prompt.id} in category {category.value}")

        return prompt

    # TODO: Review unreachable code - def update_prompt(self, prompt: Prompt) -> None:
    # TODO: Review unreachable code - """Update an existing prompt."""
    # TODO: Review unreachable code - prompt.updated_at = datetime.now()
    # TODO: Review unreachable code - self.db.update_prompt(prompt)
    # TODO: Review unreachable code - logger.info(f"Updated prompt {prompt.id}")

    # TODO: Review unreachable code - def get_prompt(self, prompt_id: str) -> Prompt | None:
    # TODO: Review unreachable code - """Get a prompt by ID."""
    # TODO: Review unreachable code - return self.db.get_prompt(prompt_id)

    # TODO: Review unreachable code - def search_prompts(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - query: str | None = None,
    # TODO: Review unreachable code - category: PromptCategory | None = None,
    # TODO: Review unreachable code - providers: list[ProviderType] | None = None,
    # TODO: Review unreachable code - tags: list[str] | None = None,
    # TODO: Review unreachable code - project: str | None = None,
    # TODO: Review unreachable code - style: str | None = None,
    # TODO: Review unreachable code - min_effectiveness: float | None = None,
    # TODO: Review unreachable code - min_success_rate: float | None = None,
    # TODO: Review unreachable code - **kwargs
    # TODO: Review unreachable code - ) -> list[Prompt]:
    # TODO: Review unreachable code - """Search for prompts with various criteria."""
    # TODO: Review unreachable code - criteria = PromptSearchCriteria(
    # TODO: Review unreachable code - query=query,
    # TODO: Review unreachable code - category=category,
    # TODO: Review unreachable code - providers=providers,
    # TODO: Review unreachable code - tags=tags,
    # TODO: Review unreachable code - project=project,
    # TODO: Review unreachable code - style=style,
    # TODO: Review unreachable code - min_effectiveness=min_effectiveness,
    # TODO: Review unreachable code - min_success_rate=min_success_rate,
    # TODO: Review unreachable code - **kwargs
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - results = self.db.search_prompts(criteria)
    # TODO: Review unreachable code - logger.info(f"Found {len(results)} prompts matching criteria")

    # TODO: Review unreachable code - return results

    # TODO: Review unreachable code - def find_similar(self, prompt_id: str, limit: int = 10) -> list[Prompt]:
    # TODO: Review unreachable code - """Find prompts similar to the given one."""
    # TODO: Review unreachable code - prompt = self.get_prompt(prompt_id)
    # TODO: Review unreachable code - if not prompt:
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - # Search by similar attributes
    # TODO: Review unreachable code - similar = []

    # TODO: Review unreachable code - # First, get directly related prompts
    # TODO: Review unreachable code - for related_id in prompt.related_ids:
    # TODO: Review unreachable code - related = self.get_prompt(related_id)
    # TODO: Review unreachable code - if related:
    # TODO: Review unreachable code - similar.append(related)

    # TODO: Review unreachable code - # Then search by tags and style
    # TODO: Review unreachable code - if prompt.tags or prompt.style:
    # TODO: Review unreachable code - results = self.search_prompts(
    # TODO: Review unreachable code - tags=prompt.tags[:3] if prompt.tags else None,  # Top 3 tags
    # TODO: Review unreachable code - style=prompt.style,
    # TODO: Review unreachable code - category=prompt.category
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - for result in results:
    # TODO: Review unreachable code - if result.id != prompt_id and result not in similar:
    # TODO: Review unreachable code - similar.append(result)

    # TODO: Review unreachable code - return similar[:limit]

    # TODO: Review unreachable code - def record_usage(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - prompt_id: str,
    # TODO: Review unreachable code - provider: ProviderType,
    # TODO: Review unreachable code - success: bool,
    # TODO: Review unreachable code - output_path: str | None = None,
    # TODO: Review unreachable code - cost: float | None = None,
    # TODO: Review unreachable code - duration_seconds: float | None = None,
    # TODO: Review unreachable code - notes: str | None = None,
    # TODO: Review unreachable code - parameters: dict[str, Any] | None = None,
    # TODO: Review unreachable code - metadata: dict[str, Any] | None = None
    # TODO: Review unreachable code - ) -> PromptUsage:
    # TODO: Review unreachable code - """Record usage of a prompt."""
    # TODO: Review unreachable code - usage = PromptUsage(
    # TODO: Review unreachable code - id=hashlib.sha256(f"{prompt_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:16],
    # TODO: Review unreachable code - prompt_id=prompt_id,
    # TODO: Review unreachable code - provider=provider,
    # TODO: Review unreachable code - timestamp=datetime.now(),
    # TODO: Review unreachable code - success=success,
    # TODO: Review unreachable code - output_path=output_path,
    # TODO: Review unreachable code - cost=cost,
    # TODO: Review unreachable code - duration_seconds=duration_seconds,
    # TODO: Review unreachable code - notes=notes,
    # TODO: Review unreachable code - parameters=parameters or {},
    # TODO: Review unreachable code - metadata=metadata or {}
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - self.db.add_usage(usage)
    # TODO: Review unreachable code - logger.info(f"Recorded {'successful' if success else 'failed'} usage of prompt {prompt_id}")

    # TODO: Review unreachable code - return usage

    # TODO: Review unreachable code - def get_usage_history(self, prompt_id: str, limit: int = 100) -> list[PromptUsage]:
    # TODO: Review unreachable code - """Get usage history for a prompt."""
    # TODO: Review unreachable code - return self.db.get_usage_history(prompt_id, limit)

    # TODO: Review unreachable code - def get_effective_prompts(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - category: PromptCategory | None = None,
    # TODO: Review unreachable code - provider: ProviderType | None = None,
    # TODO: Review unreachable code - min_success_rate: float = 0.7,
    # TODO: Review unreachable code - min_uses: int = 3,
    # TODO: Review unreachable code - limit: int = 20
    # TODO: Review unreachable code - ) -> list[Prompt]:
    # TODO: Review unreachable code - """Get the most effective prompts."""
    # TODO: Review unreachable code - prompts = self.search_prompts(
    # TODO: Review unreachable code - category=category,
    # TODO: Review unreachable code - providers=[provider] if provider else None,
    # TODO: Review unreachable code - min_success_rate=min_success_rate
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Filter by minimum uses
    # TODO: Review unreachable code - prompts = [p for p in prompts if p.use_count >= min_uses]

    # TODO: Review unreachable code - # Sort by effectiveness and success rate
    # TODO: Review unreachable code - prompts.sort(
    # TODO: Review unreachable code - key=lambda p: (
    # TODO: Review unreachable code - p.effectiveness_rating or 0,
    # TODO: Review unreachable code - p.success_rate(),
    # TODO: Review unreachable code - p.use_count
    # TODO: Review unreachable code - ),
    # TODO: Review unreachable code - reverse=True
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return prompts[:limit]

    # TODO: Review unreachable code - def export_prompts(self, output_path: Path, prompts: list[Prompt] | None = None) -> None:
    # TODO: Review unreachable code - """Export prompts to JSON file."""
    # TODO: Review unreachable code - if prompts is None:
    # TODO: Review unreachable code - prompts = self.search_prompts()  # Export all

    # TODO: Review unreachable code - data = []
    # TODO: Review unreachable code - for prompt in prompts:
    # TODO: Review unreachable code - prompt_data = {
    # TODO: Review unreachable code - "id": prompt.id,
    # TODO: Review unreachable code - "text": prompt.text,
    # TODO: Review unreachable code - "category": prompt.category.value,
    # TODO: Review unreachable code - "providers": [p.value for p in prompt.providers],
    # TODO: Review unreachable code - "tags": prompt.tags,
    # TODO: Review unreachable code - "project": prompt.project,
    # TODO: Review unreachable code - "style": prompt.style,
    # TODO: Review unreachable code - "effectiveness_rating": prompt.effectiveness_rating,
    # TODO: Review unreachable code - "use_count": prompt.use_count,
    # TODO: Review unreachable code - "success_count": prompt.success_count,
    # TODO: Review unreachable code - "success_rate": prompt.success_rate(),
    # TODO: Review unreachable code - "created_at": prompt.created_at.isoformat(),
    # TODO: Review unreachable code - "updated_at": prompt.updated_at.isoformat(),
    # TODO: Review unreachable code - "description": prompt.description,
    # TODO: Review unreachable code - "notes": prompt.notes,
    # TODO: Review unreachable code - "context": prompt.context,
    # TODO: Review unreachable code - "parent_id": prompt.parent_id,
    # TODO: Review unreachable code - "related_ids": prompt.related_ids,
    # TODO: Review unreachable code - "keywords": prompt.keywords
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - data.append(prompt_data)

    # TODO: Review unreachable code - output_path.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - with open(output_path, 'w') as f:
    # TODO: Review unreachable code - json.dump(data, f, indent=2)

    # TODO: Review unreachable code - logger.info(f"Exported {len(prompts)} prompts to {output_path}")

    # TODO: Review unreachable code - def import_prompts(self, input_path: Path) -> int:
    # TODO: Review unreachable code - """Import prompts from JSON file."""
    # TODO: Review unreachable code - with open(input_path) as f:
    # TODO: Review unreachable code - data = json.load(f)

    # TODO: Review unreachable code - imported = 0
    # TODO: Review unreachable code - for prompt_data in data:
    # TODO: Review unreachable code - # Check if prompt already exists
    # TODO: Review unreachable code - existing = self.db.get_prompt(prompt_data["id"])
    # TODO: Review unreachable code - if existing:
    # TODO: Review unreachable code - logger.debug(f"Skipping existing prompt {prompt_data['id']}")
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - prompt = Prompt(
    # TODO: Review unreachable code - id=prompt_data["id"],
    # TODO: Review unreachable code - text=prompt_data["text"],
    # TODO: Review unreachable code - category=PromptCategory(prompt_data["category"]),
    # TODO: Review unreachable code - providers=[ProviderType(p) for p in prompt_data["providers"]],
    # TODO: Review unreachable code - tags=prompt_data.get("tags", []),
    # TODO: Review unreachable code - project=prompt_data.get("project"),
    # TODO: Review unreachable code - style=prompt_data.get("style"),
    # TODO: Review unreachable code - effectiveness_rating=prompt_data.get("effectiveness_rating"),
    # TODO: Review unreachable code - use_count=prompt_data.get("use_count", 0),
    # TODO: Review unreachable code - success_count=prompt_data.get("success_count", 0),
    # TODO: Review unreachable code - created_at=datetime.fromisoformat(prompt_data["created_at"]),
    # TODO: Review unreachable code - updated_at=datetime.fromisoformat(prompt_data["updated_at"]),
    # TODO: Review unreachable code - description=prompt_data.get("description"),
    # TODO: Review unreachable code - notes=prompt_data.get("notes"),
    # TODO: Review unreachable code - context=prompt_data.get("context", {}),
    # TODO: Review unreachable code - parent_id=prompt_data.get("parent_id"),
    # TODO: Review unreachable code - related_ids=prompt_data.get("related_ids", []),
    # TODO: Review unreachable code - keywords=prompt_data.get("keywords", [])
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - self.db.add_prompt(prompt)
    # TODO: Review unreachable code - imported += 1

    # TODO: Review unreachable code - logger.info(f"Imported {imported} prompts from {input_path}")
    # TODO: Review unreachable code - return imported
