"""Smart content variation generator for reusing successful content."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..analytics.performance_tracker import PerformanceTracker
from ..memory.style_memory import PreferenceType, StyleMemory
from ..providers.provider_types import GenerationRequest

logger = logging.getLogger(__name__)


class VariationType(Enum):
    """Types of content variations."""
    STYLE = "style"  # Different artistic styles
    MOOD = "mood"  # Different emotional tones
    COLOR = "color"  # Color palette variations
    COMPOSITION = "composition"  # Layout and framing
    TEMPO = "tempo"  # Pacing variations
    ASPECT_RATIO = "aspect_ratio"  # Different formats
    DETAIL_LEVEL = "detail_level"  # Complexity variations
    TIME_OF_DAY = "time_of_day"  # Lighting variations
    SEASON = "season"  # Seasonal variations
    CAMERA = "camera"  # Camera angle/movement


class VariationStrategy(Enum):
    """Strategies for generating variations."""
    SYSTEMATIC = "systematic"  # Try all variations
    PERFORMANCE_BASED = "performance_based"  # Based on past success
    EXPLORATION = "exploration"  # Try new combinations
    OPTIMIZATION = "optimization"  # Refine successful patterns
    A_B_TESTING = "a_b_testing"  # Compare specific variations


@dataclass
class VariationTemplate:
    """Template for a specific variation."""
    variation_id: str
    variation_type: VariationType
    name: str
    description: str
    modifiers: dict[str, Any]
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: datetime | None = None
    performance_score: float = 0.0


@dataclass
class ContentBase:
    """Base content to create variations from."""
    content_id: str
    original_prompt: str
    original_parameters: dict[str, Any]
    provider: str
    model: str
    output_path: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    success_metrics: dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class VariationResult:
    """Result of a variation generation."""
    variation_id: str
    base_content_id: str
    variation_type: VariationType
    modified_prompt: str
    modified_parameters: dict[str, Any]
    output_path: Path
    generation_time: float
    cost: float
    success: bool
    error_message: str | None = None
    performance_metrics: dict[str, float] = field(default_factory=dict)


class VariationGenerator:
    """Generate smart content variations based on successful patterns."""

    # Variation templates by type
    STYLE_VARIATIONS = {
        "photorealistic": {"style": "photorealistic, ultra detailed, 8k"},
        "anime": {"style": "anime style, cel shaded, vibrant colors"},
        "oil_painting": {"style": "oil painting, impasto, textured brushstrokes"},
        "watercolor": {"style": "watercolor painting, soft edges, flowing colors"},
        "cyberpunk": {"style": "cyberpunk, neon lights, futuristic, high tech"},
        "minimalist": {"style": "minimalist, simple, clean lines, negative space"},
        "surreal": {"style": "surreal, dreamlike, impossible geometry"},
        "vintage": {"style": "vintage, retro, film grain, nostalgic"},
    }

    MOOD_VARIATIONS = {
        "dramatic": {"mood": "dramatic lighting, high contrast, intense"},
        "serene": {"mood": "peaceful, calm, tranquil, soft lighting"},
        "mysterious": {"mood": "mysterious, foggy, enigmatic, shadows"},
        "joyful": {"mood": "bright, cheerful, vibrant, uplifting"},
        "melancholic": {"mood": "melancholic, moody, contemplative"},
        "epic": {"mood": "epic scale, grandiose, awe-inspiring"},
        "intimate": {"mood": "intimate, close, personal, warm"},
        "tense": {"mood": "tense, suspenseful, edge of seat"},
    }

    COLOR_VARIATIONS = {
        "warm": {"color": "warm color palette, oranges, reds, yellows"},
        "cool": {"color": "cool color palette, blues, greens, purples"},
        "monochrome": {"color": "black and white, grayscale, monochromatic"},
        "pastel": {"color": "pastel colors, soft hues, light tones"},
        "neon": {"color": "neon colors, vibrant, electric, glowing"},
        "earth_tones": {"color": "earth tones, browns, ochres, natural colors"},
        "complementary": {"color": "complementary color scheme, high contrast"},
        "analogous": {"color": "analogous colors, harmonious, flowing"},
    }

    COMPOSITION_VARIATIONS = {
        "rule_of_thirds": {"composition": "rule of thirds composition"},
        "centered": {"composition": "centered composition, symmetrical"},
        "diagonal": {"composition": "diagonal composition, dynamic lines"},
        "golden_ratio": {"composition": "golden ratio composition"},
        "leading_lines": {"composition": "leading lines, guiding the eye"},
        "framing": {"composition": "natural framing, frame within frame"},
        "patterns": {"composition": "repeating patterns, rhythm"},
        "negative_space": {"composition": "emphasis on negative space"},
    }

    TIME_VARIATIONS = {
        "golden_hour": {"time": "golden hour lighting, warm sunset"},
        "blue_hour": {"time": "blue hour, twilight, soft blue light"},
        "midday": {"time": "midday sun, harsh shadows, bright"},
        "night": {"time": "nighttime, moonlight, stars, dark"},
        "dawn": {"time": "dawn, first light, morning mist"},
        "overcast": {"time": "overcast, diffused lighting, soft shadows"},
        "stormy": {"time": "stormy weather, dramatic clouds"},
        "foggy": {"time": "foggy, misty, atmospheric"},
    }

    CAMERA_VARIATIONS = {
        "wide_angle": {"camera": "wide angle lens, expansive view"},
        "telephoto": {"camera": "telephoto lens, compressed perspective"},
        "macro": {"camera": "macro photography, extreme close-up"},
        "aerial": {"camera": "aerial view, bird's eye perspective"},
        "low_angle": {"camera": "low angle shot, looking up"},
        "high_angle": {"camera": "high angle shot, looking down"},
        "dutch_angle": {"camera": "dutch angle, tilted, dynamic"},
        "pov": {"camera": "first person POV, immersive"},
    }

    def __init__(
        self,
        style_memory: StyleMemory | None = None,
        performance_tracker: PerformanceTracker | None = None,
        cache_dir: Path | None = None,
    ):
        """Initialize the variation generator.
        
        Args:
            style_memory: Style memory system for preferences
            performance_tracker: Performance tracking system
            cache_dir: Directory for caching variations
        """
        self.style_memory = style_memory
        self.performance_tracker = performance_tracker
        self.cache_dir = cache_dir or Path("data/variations")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Variation templates
        self.templates: dict[VariationType, dict[str, VariationTemplate]] = {}
        self._load_templates()

        # Track successful variations
        self.successful_variations: dict[str, list[VariationResult]] = {}
        self._load_successful_variations()

    def _load_templates(self):
        """Load variation templates."""
        # Load built-in templates
        template_data = {
            VariationType.STYLE: self.STYLE_VARIATIONS,
            VariationType.MOOD: self.MOOD_VARIATIONS,
            VariationType.COLOR: self.COLOR_VARIATIONS,
            VariationType.COMPOSITION: self.COMPOSITION_VARIATIONS,
            VariationType.TIME_OF_DAY: self.TIME_VARIATIONS,
            VariationType.CAMERA: self.CAMERA_VARIATIONS,
        }

        for var_type, variations in template_data.items():
            self.templates[var_type] = {}
            for name, modifiers in variations.items():
                template = VariationTemplate(
                    variation_id=f"{var_type.value}_{name}",
                    variation_type=var_type,
                    name=name,
                    description=modifiers.get(var_type.value, ""),
                    modifiers=modifiers,
                )
                self.templates[var_type][name] = template

        # Load custom templates
        custom_file = self.cache_dir / "custom_templates.json"
        if custom_file.exists():
            with open(custom_file) as f:
                custom_data = json.load(f)
                for var_type_str, templates in custom_data.items():
                    var_type = VariationType(var_type_str)
                    if var_type not in self.templates:
                        self.templates[var_type] = {}

                    for name, data in templates.items():
                        template = VariationTemplate(
                            variation_id=data["variation_id"],
                            variation_type=var_type,
                            name=name,
                            description=data["description"],
                            modifiers=data["modifiers"],
                            success_rate=data.get("success_rate", 0.0),
                            usage_count=data.get("usage_count", 0),
                            performance_score=data.get("performance_score", 0.0),
                        )
                        self.templates[var_type][name] = template

    def _load_successful_variations(self):
        """Load successful variation history."""
        history_file = self.cache_dir / "successful_variations.json"
        if history_file.exists():
            with open(history_file) as f:
                data = json.load(f)
                # Convert to VariationResult objects
                for content_id, variations in data.items():
                    self.successful_variations[content_id] = []
                    for var_data in variations:
                        result = VariationResult(
                            variation_id=var_data["variation_id"],
                            base_content_id=var_data["base_content_id"],
                            variation_type=VariationType(var_data["variation_type"]),
                            modified_prompt=var_data["modified_prompt"],
                            modified_parameters=var_data["modified_parameters"],
                            output_path=Path(var_data["output_path"]),
                            generation_time=var_data["generation_time"],
                            cost=var_data["cost"],
                            success=var_data["success"],
                            performance_metrics=var_data.get("performance_metrics", {}),
                        )
                        self.successful_variations[content_id].append(result)

    async def generate_variations(
        self,
        base_content: ContentBase,
        variation_types: list[VariationType] | None = None,
        strategy: VariationStrategy = VariationStrategy.PERFORMANCE_BASED,
        max_variations: int = 5,
    ) -> list[GenerationRequest]:
        """Generate variation requests for base content.
        
        Args:
            base_content: Base content to vary
            variation_types: Types of variations to generate
            strategy: Strategy for selecting variations
            max_variations: Maximum number of variations
            
        Returns:
            List of generation requests for variations
        """
        if variation_types is None:
            # Use all types based on content
            variation_types = self._select_variation_types(base_content)

        # Select variations based on strategy
        selected_variations = await self._select_variations(
            base_content, variation_types, strategy, max_variations
        )

        # Generate requests
        requests = []
        for variation in selected_variations:
            request = self._create_variation_request(base_content, variation)
            requests.append(request)

        return requests

    def _select_variation_types(self, base_content: ContentBase) -> list[VariationType]:
        """Select appropriate variation types for content."""
        # Analyze content to determine suitable variations
        prompt_lower = base_content.original_prompt.lower()

        suitable_types = []

        # Always try style and mood
        suitable_types.extend([VariationType.STYLE, VariationType.MOOD])

        # Add color if not already specified
        if not any(color in prompt_lower for color in ["color", "black and white", "monochrome"]):
            suitable_types.append(VariationType.COLOR)

        # Add composition for scenes
        if any(word in prompt_lower for word in ["scene", "landscape", "view", "shot"]):
            suitable_types.append(VariationType.COMPOSITION)

        # Add time variations for outdoor scenes
        if any(word in prompt_lower for word in ["outdoor", "landscape", "city", "nature"]):
            suitable_types.append(VariationType.TIME_OF_DAY)

        # Add camera for dynamic content
        if base_content.provider in ["runway", "luma", "pika"]:
            suitable_types.append(VariationType.CAMERA)

        return suitable_types

    async def _select_variations(
        self,
        base_content: ContentBase,
        variation_types: list[VariationType],
        strategy: VariationStrategy,
        max_variations: int,
    ) -> list[VariationTemplate]:
        """Select specific variations based on strategy."""
        selected = []

        if strategy == VariationStrategy.SYSTEMATIC:
            # Try all variations systematically
            for var_type in variation_types:
                if var_type in self.templates:
                    templates = list(self.templates[var_type].values())
                    selected.extend(templates[:max_variations // len(variation_types)])

        elif strategy == VariationStrategy.PERFORMANCE_BASED:
            # Select based on past performance
            for var_type in variation_types:
                if var_type in self.templates:
                    # Sort by success rate and performance
                    templates = sorted(
                        self.templates[var_type].values(),
                        key=lambda t: (t.success_rate * 0.7 + t.performance_score * 0.3),
                        reverse=True
                    )
                    selected.extend(templates[:max_variations // len(variation_types)])

        elif strategy == VariationStrategy.EXPLORATION:
            # Try less-used variations
            for var_type in variation_types:
                if var_type in self.templates:
                    # Sort by usage count (ascending)
                    templates = sorted(
                        self.templates[var_type].values(),
                        key=lambda t: t.usage_count
                    )
                    selected.extend(templates[:max_variations // len(variation_types)])

        elif strategy == VariationStrategy.OPTIMIZATION:
            # Refine successful patterns
            if self.style_memory:
                # Get user preferences
                for var_type in variation_types:
                    if var_type in self.templates:
                        # Match templates to preferences
                        pref_type = self._variation_to_preference_type(var_type)
                        if pref_type:
                            preferences = await self.style_memory.get_top_preferences(
                                pref_type, limit=3
                            )
                            for pref in preferences:
                                # Find matching template
                                for template in self.templates[var_type].values():
                                    if pref.value in template.name:
                                        selected.append(template)
                                        break

        elif strategy == VariationStrategy.A_B_TESTING:
            # Select pairs for comparison
            for var_type in variation_types[:max_variations // 2]:
                if var_type in self.templates:
                    templates = list(self.templates[var_type].values())
                    if len(templates) >= 2:
                        # Select contrasting pairs
                        selected.extend([templates[0], templates[-1]])

        return selected[:max_variations]

    def _variation_to_preference_type(self, var_type: VariationType) -> PreferenceType | None:
        """Convert variation type to preference type."""
        mapping = {
            VariationType.STYLE: PreferenceType.STYLE,
            VariationType.MOOD: PreferenceType.MOOD,
            VariationType.COLOR: PreferenceType.COLOR_PALETTE,
            VariationType.COMPOSITION: PreferenceType.COMPOSITION,
            VariationType.CAMERA: PreferenceType.CAMERA_ANGLE,
        }
        return mapping.get(var_type)

    def _create_variation_request(
        self,
        base_content: ContentBase,
        variation: VariationTemplate,
    ) -> GenerationRequest:
        """Create a generation request for a variation."""
        # Start with original prompt
        modified_prompt = base_content.original_prompt

        # Apply variation modifiers
        modifier_text = ", ".join(variation.modifiers.values())
        modified_prompt = f"{modified_prompt}, {modifier_text}"

        # Copy and update parameters
        modified_params = base_content.original_parameters.copy()

        # Add variation metadata
        modified_params["variation_id"] = variation.variation_id
        modified_params["variation_type"] = variation.variation_type.value
        modified_params["base_content_id"] = base_content.content_id

        # Create output path
        base_path = Path(base_content.output_path)
        variation_path = base_path.parent / f"{base_path.stem}_{variation.name}{base_path.suffix}"

        return GenerationRequest(
            prompt=modified_prompt,
            model=base_content.model,
            output_path=variation_path,
            parameters=modified_params,
        )

    async def analyze_variation_success(
        self,
        result: VariationResult,
        metrics: dict[str, float],
    ):
        """Analyze and record variation success.
        
        Args:
            result: Variation generation result
            metrics: Performance metrics (views, engagement, etc.)
        """
        # Update performance metrics
        result.performance_metrics = metrics

        # Calculate success score (0-1)
        success_score = self._calculate_success_score(metrics)

        # Update template statistics
        for var_type, templates in self.templates.items():
            for name, template in templates.items():
                if template.variation_id == result.variation_id:
                    template.usage_count += 1
                    template.last_used = datetime.now()

                    # Update success rate (moving average)
                    if template.usage_count == 1:
                        template.success_rate = success_score
                    else:
                        template.success_rate = (
                            template.success_rate * (template.usage_count - 1) + success_score
                        ) / template.usage_count

                    # Update performance score
                    template.performance_score = max(
                        template.performance_score,
                        success_score
                    )
                    break

        # Store successful variation
        if success_score > 0.7:  # Threshold for "successful"
            if result.base_content_id not in self.successful_variations:
                self.successful_variations[result.base_content_id] = []
            self.successful_variations[result.base_content_id].append(result)

        # Save to cache
        self._save_templates()
        self._save_successful_variations()

        # Update style memory if available
        if self.style_memory and success_score > 0.8:
            await self._update_style_memory(result)

    def _calculate_success_score(self, metrics: dict[str, float]) -> float:
        """Calculate success score from metrics."""
        # Weighted scoring based on different metrics
        weights = {
            "engagement_rate": 0.3,
            "view_duration": 0.2,
            "likes": 0.2,
            "shares": 0.15,
            "comments": 0.15,
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in metrics:
                # Normalize metric (assume 0-1 range)
                value = min(1.0, metrics[metric])
                score += value * weight
                total_weight += weight

        if total_weight > 0:
            return score / total_weight
        return 0.0

    async def _update_style_memory(self, result: VariationResult):
        """Update style memory with successful variation."""
        if not self.style_memory:
            return

        # Extract style elements from variation
        pref_type = self._variation_to_preference_type(result.variation_type)
        if pref_type:
            # Find the template name
            template_name = None
            for templates in self.templates[result.variation_type].values():
                if templates.variation_id == result.variation_id:
                    template_name = templates.name
                    break

            if template_name:
                await self.style_memory.record_preference(
                    preference_type=pref_type,
                    value=template_name,
                    context={
                        "variation_id": result.variation_id,
                        "performance_score": self._calculate_success_score(
                            result.performance_metrics
                        ),
                    },
                    strength=0.8,
                )

    def _save_templates(self):
        """Save custom templates to cache."""
        custom_data = {}

        for var_type, templates in self.templates.items():
            custom_data[var_type.value] = {}
            for name, template in templates.items():
                # Only save templates that have been used
                if template.usage_count > 0:
                    custom_data[var_type.value][name] = {
                        "variation_id": template.variation_id,
                        "description": template.description,
                        "modifiers": template.modifiers,
                        "success_rate": template.success_rate,
                        "usage_count": template.usage_count,
                        "performance_score": template.performance_score,
                    }

        with open(self.cache_dir / "custom_templates.json", "w") as f:
            json.dump(custom_data, f, indent=2)

    def _save_successful_variations(self):
        """Save successful variations to cache."""
        data = {}

        for content_id, variations in self.successful_variations.items():
            data[content_id] = []
            for var in variations:
                data[content_id].append({
                    "variation_id": var.variation_id,
                    "base_content_id": var.base_content_id,
                    "variation_type": var.variation_type.value,
                    "modified_prompt": var.modified_prompt,
                    "modified_parameters": var.modified_parameters,
                    "output_path": str(var.output_path),
                    "generation_time": var.generation_time,
                    "cost": var.cost,
                    "success": var.success,
                    "performance_metrics": var.performance_metrics,
                })

        with open(self.cache_dir / "successful_variations.json", "w") as f:
            json.dump(data, f, indent=2)

    async def get_recommended_variations(
        self,
        content_type: str,
        limit: int = 5,
    ) -> list[VariationTemplate]:
        """Get recommended variations based on past success.
        
        Args:
            content_type: Type of content (e.g., "video", "image")
            limit: Maximum recommendations
            
        Returns:
            List of recommended variation templates
        """
        recommendations = []

        # Collect all templates with good performance
        for var_type, templates in self.templates.items():
            for template in templates.values():
                if template.success_rate > 0.7 and template.usage_count > 2:
                    recommendations.append(template)

        # Sort by performance
        recommendations.sort(
            key=lambda t: t.success_rate * 0.6 + t.performance_score * 0.4,
            reverse=True
        )

        return recommendations[:limit]

    def get_variation_report(self) -> dict[str, Any]:
        """Generate a report on variation performance."""
        report = {
            "total_variations_tracked": sum(
                len(variations) for variations in self.successful_variations.values()
            ),
            "variation_types": {},
            "top_performers": [],
            "exploration_opportunities": [],
        }

        # Analyze by variation type
        for var_type, templates in self.templates.items():
            type_stats = {
                "total_templates": len(templates),
                "used_templates": sum(1 for t in templates.values() if t.usage_count > 0),
                "average_success_rate": 0.0,
                "top_template": None,
            }

            used_templates = [t for t in templates.values() if t.usage_count > 0]
            if used_templates:
                type_stats["average_success_rate"] = sum(
                    t.success_rate for t in used_templates
                ) / len(used_templates)

                top_template = max(used_templates, key=lambda t: t.success_rate)
                type_stats["top_template"] = {
                    "name": top_template.name,
                    "success_rate": top_template.success_rate,
                    "usage_count": top_template.usage_count,
                }

            report["variation_types"][var_type.value] = type_stats

        # Find top performers across all types
        all_templates = []
        for templates in self.templates.values():
            all_templates.extend(templates.values())

        top_performers = sorted(
            [t for t in all_templates if t.usage_count > 0],
            key=lambda t: t.success_rate,
            reverse=True
        )[:5]

        report["top_performers"] = [
            {
                "variation_id": t.variation_id,
                "type": t.variation_type.value,
                "name": t.name,
                "success_rate": t.success_rate,
                "usage_count": t.usage_count,
            }
            for t in top_performers
        ]

        # Find exploration opportunities (unused or low-usage templates)
        unused_templates = [
            t for t in all_templates if t.usage_count < 2
        ][:5]

        report["exploration_opportunities"] = [
            {
                "variation_id": t.variation_id,
                "type": t.variation_type.value,
                "name": t.name,
                "description": t.description,
            }
            for t in unused_templates
        ]

        return report
