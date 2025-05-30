#!/usr/bin/env python3
"""
Multi-Modal Workflow Examples

This example demonstrates the workflow system in AliceMultiverse:
- Image enhancement workflow (generate → upscale → variations)
- Video production workflow (video → audio → enhance)
- Style transfer workflow
- Custom workflow creation
- Cost optimization and progress tracking
"""

import asyncio
import os
from pathlib import Path

from alicemultiverse.workflows import (
    WorkflowTemplate,
    WorkflowStep,
    WorkflowContext,
    WorkflowExecutor,
    get_workflow,
    list_workflows,
    register_workflow,
)
from alicemultiverse.events import EventBus


async def image_enhancement_example():
    """Demonstrate image enhancement workflow."""
    print("\n=== Image Enhancement Workflow ===")
    
    # Get the workflow
    workflow = get_workflow("image_enhancement")
    if not workflow:
        print("Image enhancement workflow not found!")
        return
    
    # Create executor
    executor = WorkflowExecutor()
    
    # First, do a dry run to estimate costs
    print("\n1. Dry run to estimate costs:")
    result = await executor.execute(
        workflow=workflow,
        initial_prompt="A majestic eagle soaring through clouds at sunset",
        parameters={
            "initial_provider": "leonardo",
            "initial_model": "phoenix",
            "upscale_provider": "magnific",
            "upscale_scale": 2,
            "generate_variations": True,
            "variation_count": 3,
        },
        dry_run=True
    )
    print(f"   Estimated cost: ${result.total_cost:.2f}")
    
    # Execute the workflow (if API keys are set)
    if os.environ.get("LEONARDO_API_KEY") and os.environ.get("FREEPIK_API_KEY"):
        print("\n2. Executing workflow:")
        result = await executor.execute(
            workflow=workflow,
            initial_prompt="A majestic eagle soaring through clouds at sunset",
            parameters={
                "initial_provider": "leonardo",
                "initial_model": "phoenix",
                "upscale_provider": "magnific", 
                "upscale_scale": 2,
                "generate_variations": True,
                "variation_count": 3,
                "upscale_creativity": 0.3,
                "upscale_hdr": 0.5,
            },
            budget_limit=1.00  # Stop if cost exceeds $1
        )
        
        print(f"   Status: {result.status}")
        print(f"   Completed steps: {result.completed_steps}/{result.total_steps}")
        print(f"   Total cost: ${result.total_cost:.2f}")
        print(f"   Execution time: {result.execution_time:.1f}s")
        
        if result.final_outputs:
            print(f"   Output files: {len(result.final_outputs)}")
            for output in result.final_outputs:
                print(f"     - {output}")
    else:
        print("\n   ⚠️  Skipping execution - API keys not set")


async def quick_enhancement_example():
    """Demonstrate quick enhancement workflow."""
    print("\n=== Quick Enhancement Workflow ===")
    
    # Use the quick variant for faster results
    workflow = get_workflow("quick_enhance")
    if not workflow:
        # Fall back to creating one
        from alicemultiverse.workflows.templates.image_enhancement import QuickEnhanceWorkflow
        workflow = QuickEnhanceWorkflow()
    
    executor = WorkflowExecutor()
    
    # Estimate cost
    result = await executor.execute(
        workflow=workflow,
        initial_prompt="Colorful abstract art",
        dry_run=True
    )
    
    print(f"Quick workflow estimated cost: ${result.total_cost:.2f}")
    print("This uses faster models and skips variations")


async def video_production_example():
    """Demonstrate video production workflow."""
    print("\n=== Video Production Workflow ===")
    
    workflow = get_workflow("video_production")
    if not workflow:
        print("Video production workflow not found!")
        return
    
    executor = WorkflowExecutor()
    
    # Dry run
    print("\n1. Planning a video with audio:")
    result = await executor.execute(
        workflow=workflow,
        initial_prompt="Time-lapse of a flower blooming",
        parameters={
            "video_provider": "veo",
            "video_duration": 8,
            "add_audio": True,
            "audio_style": "ambient",
            "enhance_video": False,  # Skip enhancement for cost
            "add_captions": False,
        },
        dry_run=True
    )
    
    print(f"   Estimated cost: ${result.total_cost:.2f}")
    print(f"   Steps: {[step.name for step in workflow.define_steps(result.context)]}")


async def style_transfer_example():
    """Demonstrate style transfer workflow."""
    print("\n=== Style Transfer Workflow ===")
    
    workflow = get_workflow("style_transfer")
    if not workflow:
        print("Style transfer workflow not found!")
        return
    
    executor = WorkflowExecutor()
    
    # Example with generated base image
    print("\n1. Style transfer with generated base:")
    result = await executor.execute(
        workflow=workflow,
        initial_prompt="Portrait of a person",
        parameters={
            "style_reference": "Van Gogh starry night painting style",
            "style_provider": "firefly",
            "num_variations": 3,
            "style_strength": 0.7,
            "preserve_content": 0.5,
            "enhance_results": True,
        },
        dry_run=True
    )
    
    print(f"   Estimated cost: ${result.total_cost:.2f}")
    print(f"   Will create {result.context.initial_params['num_variations']} style variations")


async def custom_workflow_example():
    """Demonstrate creating a custom workflow."""
    print("\n=== Custom Workflow Example ===")
    
    # Define a custom workflow
    class LogoDesignWorkflow(WorkflowTemplate):
        """Custom workflow for logo design using Ideogram."""
        
        def define_steps(self, context: WorkflowContext):
            params = context.initial_params
            
            return [
                # Generate logo with Ideogram (best for text)
                WorkflowStep(
                    name="generate_logo",
                    provider="ideogram",
                    operation="generate",
                    parameters={
                        "model": "ideogram-v3",
                        "style": "design",
                        "width": 1024,
                        "height": 1024,
                        "magic_prompt": True,
                    },
                    cost_limit=0.15
                ),
                # Create variations
                WorkflowStep(
                    name="logo_variation_1",
                    provider="ideogram",
                    operation="generate", 
                    parameters={
                        "model": "ideogram-v3",
                        "style": "design",
                        "width": 1024,
                        "height": 1024,
                        "seed": 12345,  # Different seed
                    },
                    condition="previous.success",
                    cost_limit=0.15
                ),
                # Upscale the best one
                WorkflowStep(
                    name="upscale_logo",
                    provider="magnific",
                    operation="upscale",
                    parameters={
                        "input_from": "generate_logo",
                        "scale": 2,
                        "creativity": 0.1,  # Low creativity for logos
                        "resemblance": 0.9,  # High resemblance
                    },
                    condition="generate_logo.success",
                    cost_limit=0.20
                ),
            ]
    
    # Register the custom workflow
    register_workflow("logo_design", LogoDesignWorkflow)
    
    # Use it
    workflow = get_workflow("logo_design")
    executor = WorkflowExecutor()
    
    result = await executor.execute(
        workflow=workflow,
        initial_prompt="Modern tech company logo with text 'AliceAI'",
        dry_run=True
    )
    
    print(f"Custom logo workflow estimated cost: ${result.total_cost:.2f}")


async def progress_tracking_example():
    """Demonstrate progress tracking with events."""
    print("\n=== Progress Tracking Example ===")
    
    # Create event bus
    bus = EventBus()
    
    # Subscribe to events
    @bus.subscribe("workflow.started")
    async def on_start(event):
        print(f"▶️  Started: {event.workflow_name} ({event.total_steps} steps)")
    
    @bus.subscribe("workflow.step.started")
    async def on_step_start(event):
        print(f"   🔄 Step started: {event.step_name}")
    
    @bus.subscribe("workflow.step.completed")
    async def on_step_done(event):
        status = "✅" if event.success else "❌"
        print(f"   {status} Step completed: {event.step_name} (${event.cost:.3f})")
    
    @bus.subscribe("workflow.completed")
    async def on_complete(event):
        print(f"✅ Completed: {event.completed_steps}/{event.total_steps} steps")
        print(f"   Total cost: ${event.total_cost:.2f}")
        print(f"   Time: {event.execution_time:.1f}s")
    
    # Create executor with event bus
    executor = WorkflowExecutor(event_bus=bus)
    
    # Run a simple workflow
    workflow = get_workflow("quick_enhance")
    if workflow:
        # Note: This would actually execute if API keys are set
        print("\nWould track progress for workflow execution...")
        print("Events would show each step's progress in real-time")


async def list_available_workflows():
    """List all available workflows."""
    print("\n=== Available Workflows ===")
    
    workflows = list_workflows()
    print(f"\nFound {len(workflows)} workflows:")
    
    for name in sorted(workflows):
        workflow = get_workflow(name)
        if workflow:
            print(f"\n{name}:")
            print(f"  Description: {workflow.get_description()}")
            print(f"  Required providers: {', '.join(workflow.get_required_providers())}")
            
            # Estimate cost with default parameters
            context = WorkflowContext(initial_prompt="Test")
            cost = workflow.estimate_cost(context)
            print(f"  Estimated cost: ${cost:.2f}")


async def main():
    """Run all examples."""
    print("Multi-Modal Workflow Examples")
    print("=" * 50)
    
    # List available workflows
    await list_available_workflows()
    
    # Run examples
    await image_enhancement_example()
    await quick_enhancement_example()
    await video_production_example()
    await style_transfer_example()
    await custom_workflow_example()
    await progress_tracking_example()
    
    print("\n✅ All examples complete!")
    print("\nNote: To actually execute workflows, ensure API keys are set:")
    print("  - LEONARDO_API_KEY")
    print("  - FREEPIK_API_KEY (for Magnific)")
    print("  - GOOGLE_AI_API_KEY (for Veo)")
    print("  - ADOBE_CLIENT_ID (for Firefly)")
    print("  - IDEOGRAM_API_KEY")


if __name__ == "__main__":
    asyncio.run(main())