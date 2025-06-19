"""Enhanced YAML format for human-readable prompt storage."""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .models import Prompt


class PromptYAMLFormatter:
    """Formats prompts for optimal human readability in YAML."""

    @staticmethod
    def prompt_to_readable_dict(prompt: Prompt) -> dict[str, Any]:
        """Convert prompt to a human-friendly dictionary structure."""
        # Start with the most important info at the top
        data = {
            'prompt': prompt.text,
            'category': prompt.category.value,
            'providers': [p.value for p in prompt.providers],
        }

        # Add optional descriptive fields if present
        if prompt.description:
            data['description'] = prompt.description

        if prompt.tags:
            data['tags'] = prompt.tags

        if prompt.style:
            data['style'] = prompt.style

        if prompt.project:
            data['project'] = prompt.project

        # Context and parameters
        if prompt.context:
            data['context'] = prompt.context

        # Effectiveness info
        if prompt.effectiveness_rating is not None or prompt.use_count > 0:
            data['effectiveness'] = {
                'rating': prompt.effectiveness_rating,
                'uses': prompt.use_count,
                'successes': prompt.success_count,
                'success_rate': f"{prompt.success_rate() * 100:.1f}%" if prompt.use_count > 0 else "N/A"
            }

        # Notes at the end
        if prompt.notes:
            data['notes'] = prompt.notes

        # Metadata
        data['metadata'] = {
            'id': prompt.id,
            'created': prompt.created_at.isoformat(),
            'updated': prompt.updated_at.isoformat()
        }

        if prompt.parent_id:
            data['metadata']['parent_id'] = prompt.parent_id

        if prompt.related_ids:
            data['metadata']['related_ids'] = prompt.related_ids

        if prompt.keywords:
            data['metadata']['keywords'] = prompt.keywords

        return data

    # TODO: Review unreachable code - @staticmethod
    # TODO: Review unreachable code - def save_readable_prompt(prompt: Prompt, file_path: Path) -> None:
    # TODO: Review unreachable code - """Save a single prompt in readable YAML format."""
    # TODO: Review unreachable code - data = PromptYAMLFormatter.prompt_to_readable_dict(prompt)

    # TODO: Review unreachable code - with open(file_path, 'w') as f:
    # TODO: Review unreachable code - yaml.dump(data, f, default_flow_style=False, sort_keys=False,
    # TODO: Review unreachable code - allow_unicode=True, width=100)

    # TODO: Review unreachable code - @staticmethod
    # TODO: Review unreachable code - def save_prompt_collection(prompts: list[Prompt], file_path: Path,
    # TODO: Review unreachable code - title: str = "Prompt Collection") -> None:
    # TODO: Review unreachable code - """Save multiple prompts in a well-organized YAML file."""
    # TODO: Review unreachable code - # Group prompts by category
    # TODO: Review unreachable code - by_category = {}
    # TODO: Review unreachable code - for prompt in prompts:
    # TODO: Review unreachable code - cat = prompt.category.value
    # TODO: Review unreachable code - if cat not in by_category:
    # TODO: Review unreachable code - by_category[cat] = []
    # TODO: Review unreachable code - by_category[cat].append(prompt)

    # TODO: Review unreachable code - # Create the collection structure
    # TODO: Review unreachable code - collection = {
    # TODO: Review unreachable code - 'title': title,
    # TODO: Review unreachable code - 'generated_at': datetime.now().isoformat(),
    # TODO: Review unreachable code - 'total_prompts': len(prompts),
    # TODO: Review unreachable code - 'prompts_by_category': {}
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Add prompts organized by category
    # TODO: Review unreachable code - for category, category_prompts in sorted(by_category.items()):
    # TODO: Review unreachable code - collection['prompts_by_category'][category] = [
    # TODO: Review unreachable code - PromptYAMLFormatter.prompt_to_readable_dict(p)
    # TODO: Review unreachable code - for p in sorted(category_prompts,
    # TODO: Review unreachable code - key=lambda x: (x.effectiveness_rating or 0),
    # TODO: Review unreachable code - reverse=True)
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - with open(file_path, 'w') as f:
    # TODO: Review unreachable code - yaml.dump(collection, f, default_flow_style=False, sort_keys=False,
    # TODO: Review unreachable code - allow_unicode=True, width=100)

    # TODO: Review unreachable code - @staticmethod
    # TODO: Review unreachable code - def create_example_prompt_yaml(file_path: Path) -> None:
    # TODO: Review unreachable code - """Create an example YAML file showing the format."""
    # TODO: Review unreachable code - example = """# Example Prompt Format
# TODO: Review unreachable code - # This file shows how to structure prompts in YAML
# TODO: Review unreachable code - 
# TODO: Review unreachable code - prompt: "A serene Japanese garden with cherry blossoms in full bloom, koi pond reflecting the sky, traditional wooden bridge, soft morning light, photorealistic, 8k"
# TODO: Review unreachable code - 
# TODO: Review unreachable code - category: image_generation
# TODO: Review unreachable code - 
# TODO: Review unreachable code - providers:
# TODO: Review unreachable code -   - midjourney
# TODO: Review unreachable code -   - flux
# TODO: Review unreachable code -   - stable_diffusion
# TODO: Review unreachable code - 
# TODO: Review unreachable code - description: "Creates a peaceful Japanese garden scene with traditional elements"
# TODO: Review unreachable code - 
# TODO: Review unreachable code - tags:
# TODO: Review unreachable code -   - landscape
# TODO: Review unreachable code -   - japanese
# TODO: Review unreachable code -   - nature
# TODO: Review unreachable code -   - serene
# TODO: Review unreachable code -   - photorealistic
# TODO: Review unreachable code - 
# TODO: Review unreachable code - style: photorealistic
# TODO: Review unreachable code - 
# TODO: Review unreachable code - project: SpringScenes
# TODO: Review unreachable code - 
# TODO: Review unreachable code - context:
# TODO: Review unreachable code -   aspect_ratio: "16:9"
# TODO: Review unreachable code -   model_version: "v6"
# TODO: Review unreachable code -   quality: "high"
# TODO: Review unreachable code -   steps: 50
# TODO: Review unreachable code - 
# TODO: Review unreachable code - effectiveness:
# TODO: Review unreachable code -   rating: 8.5
# TODO: Review unreachable code -   uses: 24
# TODO: Review unreachable code -   successes: 22
# TODO: Review unreachable code -   success_rate: "91.7%"
# TODO: Review unreachable code - 
# TODO: Review unreachable code - notes: |
# TODO: Review unreachable code -   This prompt works exceptionally well for creating calming scenes.
# TODO: Review unreachable code -   Best results with Midjourney v6 using --ar 16:9 --q 2
# TODO: Review unreachable code -   For Flux, increase the steps to 50 for better detail
# TODO: Review unreachable code - 
# TODO: Review unreachable code -   Variations to try:
# TODO: Review unreachable code -   - Change "morning light" to "golden hour" for warmer tones
# TODO: Review unreachable code -   - Add "misty atmosphere" for more mystical feeling
# TODO: Review unreachable code -   - Include "stone lanterns" for additional traditional elements
# TODO: Review unreachable code - 
# TODO: Review unreachable code - metadata:
# TODO: Review unreachable code -   id: "550e8400-e29b-41d4-a716-446655440000"
# TODO: Review unreachable code -   created: "2024-01-15T10:30:00"
# TODO: Review unreachable code -   updated: "2024-01-20T14:45:00"
# TODO: Review unreachable code -   keywords:
# TODO: Review unreachable code -     - zen
# TODO: Review unreachable code -     - meditation
# TODO: Review unreachable code -     - tranquil
# TODO: Review unreachable code - """

    # TODO: Review unreachable code -     with open(file_path, 'w') as f:
    # TODO: Review unreachable code -         f.write(example)
