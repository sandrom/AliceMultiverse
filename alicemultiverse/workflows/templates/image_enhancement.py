"""Image enhancement workflow template.

Common workflow: Generate → Upscale → Variations
"""

import logging

from alicemultiverse.workflows.base import WorkflowContext, WorkflowStep, WorkflowTemplate

logger = logging.getLogger(__name__)


class ImageEnhancementWorkflow(WorkflowTemplate):
    """Workflow for enhancing images through generation, upscaling, and variations.
    
    This workflow:
    1. Generates an initial image using a high-quality provider
    2. Upscales it using Magnific/Freepik for maximum quality
    3. Optionally generates variations of the upscaled image
    
    Parameters:
        initial_provider: Provider for initial generation (default: leonardo)
        initial_model: Model for initial generation (default: phoenix)
        upscale_provider: Provider for upscaling (default: magnific)
        upscale_scale: Upscaling factor (default: 2)
        generate_variations: Whether to generate variations (default: False)
        variation_count: Number of variations to generate (default: 3)
        variation_provider: Provider for variations (default: same as initial)
    """

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define the enhancement workflow steps."""
        steps = []
        params = context.initial_params

        # Step 1: Initial generation
        initial_provider = params.get("initial_provider", "leonardo")
        initial_model = params.get("initial_model", "phoenix")

        steps.append(WorkflowStep(
            name="initial_generation",
            provider=initial_provider,
            operation="generate",
            parameters={
                "model": initial_model,
                "width": params.get("width", 1024),
                "height": params.get("height", 1024),
                "num_images": 1,
                "guidance_scale": params.get("guidance_scale", 7.0),
                "seed": params.get("seed"),
                "quality": "high",  # Hint for providers that support quality settings
            },
            cost_limit=params.get("initial_cost_limit", 0.10)
        ))

        # Step 2: Upscaling
        upscale_provider = params.get("upscale_provider", "magnific")
        upscale_scale = params.get("upscale_scale", 2)

        steps.append(WorkflowStep(
            name="upscale",
            provider=upscale_provider,
            operation="upscale",
            parameters={
                "input_from": "initial_generation",
                "scale": upscale_scale,
                "model": params.get("upscale_model", "general"),
                "creativity": params.get("upscale_creativity", 0.3),
                "hdr": params.get("upscale_hdr", 0.5),
                "resemblance": params.get("upscale_resemblance", 0.7),
            },
            condition="previous.success",
            cost_limit=params.get("upscale_cost_limit", 0.20)
        ))

        # Step 3: Optional variations
        if params.get("generate_variations", False):
            variation_count = params.get("variation_count", 3)
            variation_provider = params.get("variation_provider", initial_provider)

            for i in range(variation_count):
                steps.append(WorkflowStep(
                    name=f"variation_{i+1}",
                    provider=variation_provider,
                    operation="generate",
                    parameters={
                        "model": initial_model,
                        "width": params.get("width", 1024) * upscale_scale,
                        "height": params.get("height", 1024) * upscale_scale,
                        "num_images": 1,
                        "init_image": "upscale_output",  # Reference upscaled image
                        "init_strength": params.get("variation_strength", 0.7),
                        "guidance_scale": params.get("guidance_scale", 7.0),
                    },
                    condition="upscale.success",
                    cost_limit=params.get("variation_cost_limit", 0.05)
                ))

        # Step 4: Final output (marks files as final)
        steps.append(WorkflowStep(
            name="final_output",
            provider="local",  # Special provider for local operations
            operation="organize",
            parameters={
                "collect_outputs": True,
                "create_comparison": params.get("create_comparison", True),
            },
            condition="previous.success",
            cost_limit=0.0  # No cost for local operations
        ))

        return steps

    def validate(self, context: WorkflowContext) -> list[str]:
        """Validate the workflow can execute."""
        errors = super().validate(context)
        params = context.initial_params

        # Check upscale scale is reasonable
        upscale_scale = params.get("upscale_scale", 2)
        if upscale_scale < 1 or upscale_scale > 4:
            errors.append(f"Upscale scale {upscale_scale} should be between 1 and 4")

        # Check variation count is reasonable
        if params.get("generate_variations", False):
            variation_count = params.get("variation_count", 3)
            if variation_count < 1 or variation_count > 10:
                errors.append(f"Variation count {variation_count} should be between 1 and 10")

        return errors

    def estimate_cost(self, context: WorkflowContext) -> float:
        """Estimate total workflow cost."""
        params = context.initial_params
        total = 0.0

        # Initial generation
        if params.get("initial_provider") == "leonardo":
            total += 0.02  # ~$0.02 for Phoenix
        elif params.get("initial_provider") == "firefly":
            total += 0.04  # Adobe Firefly is slightly more
        else:
            total += 0.03  # Average estimate

        # Upscaling (typically more expensive)
        upscale_scale = params.get("upscale_scale", 2)
        if params.get("upscale_provider") == "magnific":
            # Magnific pricing scales with output size
            total += 0.05 * (upscale_scale / 2)  # Base $0.05 for 2x
        else:
            total += 0.04

        # Variations
        if params.get("generate_variations", False):
            variation_count = params.get("variation_count", 3)
            total += 0.02 * variation_count  # Similar to initial generation

        return total


class QuickEnhanceWorkflow(ImageEnhancementWorkflow):
    """Simplified enhancement workflow for quick results.
    
    Uses faster models and skips variations by default.
    """

    def __init__(self):
        super().__init__(name="QuickEnhance")

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define quick enhancement steps."""
        # Override defaults for speed
        params = context.initial_params
        params.setdefault("initial_provider", "leonardo")
        params.setdefault("initial_model", "flux-schnell")  # Fast model
        params.setdefault("upscale_scale", 2)
        params.setdefault("generate_variations", False)
        params.setdefault("upscale_creativity", 0.2)  # Less creative for speed

        return super().define_steps(context)


class PremiumEnhanceWorkflow(ImageEnhancementWorkflow):
    """Premium enhancement workflow for maximum quality.
    
    Uses best models and includes variations.
    """

    def __init__(self):
        super().__init__(name="PremiumEnhance")

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define premium enhancement steps."""
        # Override defaults for quality
        params = context.initial_params
        params.setdefault("initial_provider", "firefly")  # High quality
        params.setdefault("initial_model", "firefly-v3")
        params.setdefault("upscale_provider", "magnific")
        params.setdefault("upscale_scale", 3)  # Higher scale
        params.setdefault("generate_variations", True)
        params.setdefault("variation_count", 5)
        params.setdefault("upscale_creativity", 0.4)
        params.setdefault("upscale_hdr", 0.7)  # More HDR

        # Add extra quality step
        steps = super().define_steps(context)

        # Insert quality assessment after upscaling
        quality_step = WorkflowStep(
            name="quality_check",
            provider="local",
            operation="assess_quality",
            parameters={
                "input_from": "upscale",
                "min_quality_score": 80,
                "retry_if_low": True,
            },
            condition="upscale.success"
        )

        # Insert before variations
        insert_index = next(
            (i for i, s in enumerate(steps) if s.name.startswith("variation")),
            len(steps) - 1
        )
        steps.insert(insert_index, quality_step)

        return steps
