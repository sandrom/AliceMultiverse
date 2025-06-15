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

    @staticmethod
    def save_readable_prompt(prompt: Prompt, file_path: Path) -> None:
        """Save a single prompt in readable YAML format."""
        data = PromptYAMLFormatter.prompt_to_readable_dict(prompt)

        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False,
                     allow_unicode=True, width=100)

    @staticmethod
    def save_prompt_collection(prompts: list[Prompt], file_path: Path,
                              title: str = "Prompt Collection") -> None:
        """Save multiple prompts in a well-organized YAML file."""
        # Group prompts by category
        by_category = {}
        for prompt in prompts:
            cat = prompt.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(prompt)

        # Create the collection structure
        collection = {
            'title': title,
            'generated_at': datetime.now().isoformat(),
            'total_prompts': len(prompts),
            'prompts_by_category': {}
        }

        # Add prompts organized by category
        for category, category_prompts in sorted(by_category.items()):
            collection['prompts_by_category'][category] = [
                PromptYAMLFormatter.prompt_to_readable_dict(p)
                for p in sorted(category_prompts,
                              key=lambda x: (x.effectiveness_rating or 0),
                              reverse=True)
            ]

        with open(file_path, 'w') as f:
            yaml.dump(collection, f, default_flow_style=False, sort_keys=False,
                     allow_unicode=True, width=100)

    @staticmethod
    def create_example_prompt_yaml(file_path: Path) -> None:
        """Create an example YAML file showing the format."""
        example = """# Example Prompt Format
# This file shows how to structure prompts in YAML

prompt: "A serene Japanese garden with cherry blossoms in full bloom, koi pond reflecting the sky, traditional wooden bridge, soft morning light, photorealistic, 8k"

category: image_generation

providers:
  - midjourney
  - flux
  - stable_diffusion

description: "Creates a peaceful Japanese garden scene with traditional elements"

tags:
  - landscape
  - japanese
  - nature
  - serene
  - photorealistic

style: photorealistic

project: SpringScenes

context:
  aspect_ratio: "16:9"
  model_version: "v6"
  quality: "high"
  steps: 50

effectiveness:
  rating: 8.5
  uses: 24
  successes: 22
  success_rate: "91.7%"

notes: |
  This prompt works exceptionally well for creating calming scenes.
  Best results with Midjourney v6 using --ar 16:9 --q 2
  For Flux, increase the steps to 50 for better detail
  
  Variations to try:
  - Change "morning light" to "golden hour" for warmer tones
  - Add "misty atmosphere" for more mystical feeling
  - Include "stone lanterns" for additional traditional elements

metadata:
  id: "550e8400-e29b-41d4-a716-446655440000"
  created: "2024-01-15T10:30:00"
  updated: "2024-01-20T14:45:00"
  keywords:
    - zen
    - meditation
    - tranquil
"""

        with open(file_path, 'w') as f:
            f.write(example)
