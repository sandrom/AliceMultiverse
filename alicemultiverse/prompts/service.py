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

    def update_prompt(self, prompt: Prompt) -> None:
        """Update an existing prompt."""
        prompt.updated_at = datetime.now()
        self.db.update_prompt(prompt)
        logger.info(f"Updated prompt {prompt.id}")

    def get_prompt(self, prompt_id: str) -> Prompt | None:
        """Get a prompt by ID."""
        return self.db.get_prompt(prompt_id)

    def search_prompts(
        self,
        query: str | None = None,
        category: PromptCategory | None = None,
        providers: list[ProviderType] | None = None,
        tags: list[str] | None = None,
        project: str | None = None,
        style: str | None = None,
        min_effectiveness: float | None = None,
        min_success_rate: float | None = None,
        **kwargs
    ) -> list[Prompt]:
        """Search for prompts with various criteria."""
        criteria = PromptSearchCriteria(
            query=query,
            category=category,
            providers=providers,
            tags=tags,
            project=project,
            style=style,
            min_effectiveness=min_effectiveness,
            min_success_rate=min_success_rate,
            **kwargs
        )

        results = self.db.search_prompts(criteria)
        logger.info(f"Found {len(results)} prompts matching criteria")

        return results

    def find_similar(self, prompt_id: str, limit: int = 10) -> list[Prompt]:
        """Find prompts similar to the given one."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return []

        # Search by similar attributes
        similar = []

        # First, get directly related prompts
        for related_id in prompt.related_ids:
            related = self.get_prompt(related_id)
            if related:
                similar.append(related)

        # Then search by tags and style
        if prompt.tags or prompt.style:
            results = self.search_prompts(
                tags=prompt.tags[:3] if prompt.tags else None,  # Top 3 tags
                style=prompt.style,
                category=prompt.category
            )
            for result in results:
                if result.id != prompt_id and result not in similar:
                    similar.append(result)

        return similar[:limit]

    def record_usage(
        self,
        prompt_id: str,
        provider: ProviderType,
        success: bool,
        output_path: str | None = None,
        cost: float | None = None,
        duration_seconds: float | None = None,
        notes: str | None = None,
        parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> PromptUsage:
        """Record usage of a prompt."""
        usage = PromptUsage(
            id=hashlib.sha256(f"{prompt_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            prompt_id=prompt_id,
            provider=provider,
            timestamp=datetime.now(),
            success=success,
            output_path=output_path,
            cost=cost,
            duration_seconds=duration_seconds,
            notes=notes,
            parameters=parameters or {},
            metadata=metadata or {}
        )

        self.db.add_usage(usage)
        logger.info(f"Recorded {'successful' if success else 'failed'} usage of prompt {prompt_id}")

        return usage

    def get_usage_history(self, prompt_id: str, limit: int = 100) -> list[PromptUsage]:
        """Get usage history for a prompt."""
        return self.db.get_usage_history(prompt_id, limit)

    def get_effective_prompts(
        self,
        category: PromptCategory | None = None,
        provider: ProviderType | None = None,
        min_success_rate: float = 0.7,
        min_uses: int = 3,
        limit: int = 20
    ) -> list[Prompt]:
        """Get the most effective prompts."""
        prompts = self.search_prompts(
            category=category,
            providers=[provider] if provider else None,
            min_success_rate=min_success_rate
        )

        # Filter by minimum uses
        prompts = [p for p in prompts if p.use_count >= min_uses]

        # Sort by effectiveness and success rate
        prompts.sort(
            key=lambda p: (
                p.effectiveness_rating or 0,
                p.success_rate(),
                p.use_count
            ),
            reverse=True
        )

        return prompts[:limit]

    def export_prompts(self, output_path: Path, prompts: list[Prompt] | None = None) -> None:
        """Export prompts to JSON file."""
        if prompts is None:
            prompts = self.search_prompts()  # Export all

        data = []
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
                "success_count": prompt.success_count,
                "success_rate": prompt.success_rate(),
                "created_at": prompt.created_at.isoformat(),
                "updated_at": prompt.updated_at.isoformat(),
                "description": prompt.description,
                "notes": prompt.notes,
                "context": prompt.context,
                "parent_id": prompt.parent_id,
                "related_ids": prompt.related_ids,
                "keywords": prompt.keywords
            }
            data.append(prompt_data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(prompts)} prompts to {output_path}")

    def import_prompts(self, input_path: Path) -> int:
        """Import prompts from JSON file."""
        with open(input_path) as f:
            data = json.load(f)

        imported = 0
        for prompt_data in data:
            # Check if prompt already exists
            existing = self.db.get_prompt(prompt_data["id"])
            if existing:
                logger.debug(f"Skipping existing prompt {prompt_data['id']}")
                continue

            prompt = Prompt(
                id=prompt_data["id"],
                text=prompt_data["text"],
                category=PromptCategory(prompt_data["category"]),
                providers=[ProviderType(p) for p in prompt_data["providers"]],
                tags=prompt_data.get("tags", []),
                project=prompt_data.get("project"),
                style=prompt_data.get("style"),
                effectiveness_rating=prompt_data.get("effectiveness_rating"),
                use_count=prompt_data.get("use_count", 0),
                success_count=prompt_data.get("success_count", 0),
                created_at=datetime.fromisoformat(prompt_data["created_at"]),
                updated_at=datetime.fromisoformat(prompt_data["updated_at"]),
                description=prompt_data.get("description"),
                notes=prompt_data.get("notes"),
                context=prompt_data.get("context", {}),
                parent_id=prompt_data.get("parent_id"),
                related_ids=prompt_data.get("related_ids", []),
                keywords=prompt_data.get("keywords", [])
            )

            self.db.add_prompt(prompt)
            imported += 1

        logger.info(f"Imported {imported} prompts from {input_path}")
        return imported
