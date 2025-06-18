"""Style transfer workflow template.

Workflow for applying artistic styles to images or creating style variations.
"""

import logging

from alicemultiverse.workflows.base import WorkflowContext, WorkflowStep, WorkflowTemplate

logger = logging.getLogger(__name__)


class StyleTransferWorkflow(WorkflowTemplate):
    """Workflow for transferring artistic styles to images.

    This workflow:
    1. Takes an input image (or generates one)
    2. Applies style transfer using various techniques
    3. Generates multiple style variations
    4. Optionally enhances the results

    Parameters:
        input_image: Path to input image (optional, will generate if not provided)
        style_reference: Path or description of style reference
        style_provider: Provider for style transfer (default: firefly)
        num_variations: Number of style variations (default: 3)
        style_strength: How strongly to apply the style (0-1, default: 0.7)
        preserve_content: How much to preserve original content (0-1, default: 0.5)
        enhance_results: Whether to enhance final images (default: True)
    """

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define the style transfer workflow steps."""
        steps = []
        params = context.initial_params

        # Step 1: Input image handling
        if not params.get("input_image"):
            # Generate an image if none provided
            steps.append(WorkflowStep(
                name="generate_base_image",
                provider=params.get("base_provider", "leonardo"),
                operation="generate",
                parameters={
                    "model": params.get("base_model", "phoenix"),
                    "width": params.get("width", 1024),
                    "height": params.get("height", 1024),
                    "quality": "high",
                },
                cost_limit=params.get("base_cost_limit", 0.05)
            ))

        # Step 2: Style transfer variations
        style_provider = params.get("style_provider", "firefly")
        num_variations = params.get("num_variations", 3)
        style_strength = params.get("style_strength", 0.7)
        preserve_content = params.get("preserve_content", 0.5)

        # Different style approaches for each variation
        style_approaches = [
            {
                "name": "artistic",
                "strength": style_strength,
                "preserve": preserve_content,
            },
            {
                "name": "bold",
                "strength": min(1.0, style_strength * 1.3),
                "preserve": preserve_content * 0.7,
            },
            {
                "name": "subtle",
                "strength": style_strength * 0.6,
                "preserve": min(1.0, preserve_content * 1.3),
            },
            {
                "name": "experimental",
                "strength": style_strength * 1.1,
                "preserve": preserve_content * 0.9,
            },
            {
                "name": "balanced",
                "strength": style_strength * 0.9,
                "preserve": preserve_content * 1.1,
            },
        ]

        for i in range(min(num_variations, len(style_approaches))):
            approach = style_approaches[i]

            if style_provider == "firefly":
                # Adobe Firefly style transfer
                steps.append(WorkflowStep(
                    name=f"style_transfer_{approach['name']}",
                    provider="firefly",
                    operation="style_transfer",
                    parameters={
                        "input_from": params.get("input_image") or "generate_base_image",
                        "style_reference": params.get("style_reference"),
                        "style_strength": approach["strength"],
                        "preserve_content": approach["preserve"],
                        "style_preset": params.get("style_preset"),
                        "seed": params.get("seed"),
                    },
                    condition="previous.success" if not params.get("input_image") else None,
                    cost_limit=params.get("style_cost_limit", 0.08)
                ))
            else:
                # Generic img2img style transfer
                steps.append(WorkflowStep(
                    name=f"style_transfer_{approach['name']}",
                    provider=style_provider,
                    operation="generate",
                    parameters={
                        "input_from": params.get("input_image") or "generate_base_image",
                        "prompt": self._build_style_prompt(params, approach),
                        "init_strength": 1.0 - approach["preserve"],
                        "model": params.get("style_model"),
                        "width": params.get("width", 1024),
                        "height": params.get("height", 1024),
                        "seed": params.get("seed"),
                    },
                    condition="previous.success" if not params.get("input_image") else None,
                    cost_limit=params.get("style_cost_limit", 0.05)
                ))

        # Step 3: Enhancement (if enabled)
        if params.get("enhance_results", True):
            # Enhance each style variation
            for i in range(min(num_variations, len(style_approaches))):
                approach = style_approaches[i]

                steps.append(WorkflowStep(
                    name=f"enhance_{approach['name']}",
                    provider=params.get("enhance_provider", "magnific"),
                    operation="enhance",
                    parameters={
                        "input_from": f"style_transfer_{approach['name']}",
                        "scale": params.get("enhance_scale", 1.5),
                        "creativity": 0.2,  # Low creativity to preserve style
                        "hdr": params.get("enhance_hdr", 0.4),
                        "resemblance": 0.8,  # High resemblance to preserve style
                    },
                    condition=f"style_transfer_{approach['name']}.success",
                    cost_limit=params.get("enhance_cost_limit", 0.10)
                ))

        # Step 4: Create comparison grid
        steps.append(WorkflowStep(
            name="create_comparison",
            provider="local",
            operation="create_grid",
            parameters={
                "collect_all": True,
                "include_original": bool(params.get("input_image")),
                "grid_layout": params.get("grid_layout", "auto"),
                "add_labels": True,
            },
            condition="previous.success",
            cost_limit=0.0
        ))

        # Step 5: Final output
        steps.append(WorkflowStep(
            name="final_output",
            provider="local",
            operation="organize_outputs",
            parameters={
                "create_metadata": True,
                "save_settings": True,
            },
            condition="previous.success",
            cost_limit=0.0
        ))

        return steps

    def _build_style_prompt(self, params: dict, approach: dict) -> str:
        """Build a style transfer prompt."""
        base_prompt = params.get("style_reference", "artistic style")

        # Add approach-specific modifiers
        if approach["name"] == "bold":
            modifiers = "bold, vibrant, high contrast"
        elif approach["name"] == "subtle":
            modifiers = "subtle, refined, delicate"
        elif approach["name"] == "experimental":
            modifiers = "experimental, unique, creative interpretation"
        else:
            modifiers = "balanced, harmonious"

        # Combine with original prompt if provided
        if context_prompt := params.get("prompt"):
            return f"{context_prompt}, in the style of {base_prompt}, {modifiers}"
        else:
            return f"Image in the style of {base_prompt}, {modifiers}"

    def validate(self, context: WorkflowContext) -> list[str]:
        """Validate the workflow can execute."""
        errors = super().validate(context)
        params = context.initial_params

        # Check if we have input or will generate
        if not params.get("input_image") and not context.initial_prompt:
            errors.append("Either input_image or initial_prompt is required")

        # Check style reference
        if not params.get("style_reference"):
            errors.append("style_reference is required (path or description)")

        # Check num_variations
        num_variations = params.get("num_variations", 3)
        if num_variations < 1 or num_variations > 5:
            errors.append(f"num_variations {num_variations} should be between 1 and 5")

        # Check strength values
        style_strength = params.get("style_strength", 0.7)
        if style_strength < 0 or style_strength > 1:
            errors.append(f"style_strength {style_strength} should be between 0 and 1")

        return errors

    def estimate_cost(self, context: WorkflowContext) -> float:
        """Estimate total workflow cost."""
        params = context.initial_params
        total = 0.0

        # Base image generation (if needed)
        if not params.get("input_image"):
            total += 0.03

        # Style transfer variations
        num_variations = params.get("num_variations", 3)
        if params.get("style_provider") == "firefly":
            total += 0.06 * num_variations  # Firefly style transfer
        else:
            total += 0.03 * num_variations  # Generic img2img

        # Enhancement
        if params.get("enhance_results", True):
            total += 0.08 * num_variations  # Enhancement cost

        return total


class ArtisticStyleWorkflow(StyleTransferWorkflow):
    """Workflow optimized for artistic style transfer.

    Focuses on painting and artistic styles.
    """

    def __init__(self):
        super().__init__(name="ArtisticStyle")

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define artistic style steps."""
        # Set artistic defaults
        params = context.initial_params
        params.setdefault("style_provider", "firefly")
        params.setdefault("num_variations", 4)
        params.setdefault("style_strength", 0.8)
        params.setdefault("preserve_content", 0.4)
        params.setdefault("enhance_results", True)
        params.setdefault("enhance_hdr", 0.6)  # More HDR for artistic look

        return super().define_steps(context)


class PhotoStyleWorkflow(StyleTransferWorkflow):
    """Workflow optimized for photographic style transfer.

    Maintains photorealism while applying style.
    """

    def __init__(self):
        super().__init__(name="PhotoStyle")

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define photo style steps."""
        # Set photographic defaults
        params = context.initial_params
        params.setdefault("style_provider", "leonardo")
        params.setdefault("style_model", "photoreal")
        params.setdefault("num_variations", 3)
        params.setdefault("style_strength", 0.5)  # Subtler
        params.setdefault("preserve_content", 0.7)  # Preserve more
        params.setdefault("enhance_results", True)
        params.setdefault("enhance_scale", 2)  # Higher quality

        return super().define_steps(context)
