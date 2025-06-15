"""Comprehensive example of the prompt management system."""

import asyncio
from datetime import datetime
from pathlib import Path

from alicemultiverse.prompts import (
    ProjectPromptStorage,
    PromptBatchProcessor,
    PromptCategory,
    PromptProviderIntegration,
    PromptService,
    ProviderType,
    TemplateManager,
)


def main():
    """Demonstrate all prompt management features."""

    print("=== AliceMultiverse Prompt Management System ===\n")

    # 1. Initialize services
    service = PromptService()
    storage = ProjectPromptStorage()
    template_manager = TemplateManager()
    batch_processor = PromptBatchProcessor(service)
    integration = PromptProviderIntegration(service)

    # 2. Create a project structure
    project_path = Path("~/Projects/DemoProject").expanduser()
    project_path.mkdir(exist_ok=True)

    print("1. Initializing project prompt storage...")
    storage.initialize_project_prompts(project_path)
    print(f"   Created: {project_path}/.alice/prompts/")

    # 3. Create some prompts
    print("\n2. Creating sample prompts...")

    prompt1 = service.create_prompt(
        text="A majestic mountain landscape at golden hour, photorealistic style",
        category=PromptCategory.IMAGE_GENERATION,
        providers=[ProviderType.MIDJOURNEY, ProviderType.FLUX],
        tags=["landscape", "nature", "mountains", "golden-hour"],
        project="DemoProject",
        style="photorealistic",
        description="Creates stunning mountain landscapes with warm lighting"
    )
    print(f"   Created: {prompt1.id[:8]} - Mountain landscape")

    prompt2 = service.create_prompt(
        text="Cyberpunk city street at night with neon lights and rain",
        category=PromptCategory.IMAGE_GENERATION,
        providers=[ProviderType.MIDJOURNEY, ProviderType.STABLE_DIFFUSION],
        tags=["cyberpunk", "cityscape", "night", "neon"],
        project="DemoProject",
        style="cyberpunk",
        description="Atmospheric cyberpunk cityscapes"
    )
    print(f"   Created: {prompt2.id[:8]} - Cyberpunk city")

    # 4. Save to project
    print("\n3. Saving prompts to project...")
    storage.save_to_project(prompt1, project_path)
    storage.save_to_project(prompt2, project_path)
    print(f"   Saved to: {project_path}/.alice/prompts/prompts.yaml")

    # 5. Record some usage
    print("\n4. Recording usage data...")

    # Simulate usage for prompt1
    for i in range(5):
        service.record_usage(
            prompt_id=prompt1.id,
            provider=ProviderType.MIDJOURNEY,
            success=(i != 2),  # One failure
            cost=0.10,
            duration_seconds=15 + i
        )

    # Simulate usage for prompt2
    for i in range(3):
        service.record_usage(
            prompt_id=prompt2.id,
            provider=ProviderType.STABLE_DIFFUSION,
            success=True,
            cost=0.05,
            duration_seconds=20 + i
        )

    print("   Recorded 8 usage instances")

    # 6. Search and analyze
    print("\n5. Searching and analyzing prompts...")

    # Search by style
    cyberpunk_prompts = service.search_prompts(style="cyberpunk")
    print(f"   Found {len(cyberpunk_prompts)} cyberpunk prompts")

    # Get effective prompts
    effective = service.get_effective_prompts(min_uses=3)
    print(f"   Found {len(effective)} effective prompts")

    if effective:
        best = effective[0]
        print(f"   Best: {best.text[:50]}...")
        print(f"         Success rate: {best.success_rate()*100:.1f}%")

    # 7. Work with templates
    print("\n6. Working with templates...")

    # List built-in templates
    templates = template_manager.list_templates()
    print(f"   Available templates: {', '.join(templates[:3])}...")

    # Use a template
    landscape_template = template_manager.get_template("landscape")
    if landscape_template:
        rendered = landscape_template.render(
            location="tropical beach",
            time_of_day="sunset",
            weather="partly cloudy",
            style="photorealistic",
            mood="serene"
        )
        print(f"   Rendered: {rendered}")

        # Create prompt from template
        template_prompt = landscape_template.to_prompt(
            location="tropical beach",
            time_of_day="sunset",
            weather="partly cloudy",
            style="photorealistic",
            mood="serene",
            project="DemoProject"
        )
        service.db.add_prompt(template_prompt)
        print(f"   Created from template: {template_prompt.id[:8]}")

    # 8. Batch operations
    print("\n7. Batch operations...")

    # Auto-rate prompts
    from alicemultiverse.prompts.batch import auto_rate_by_success
    all_prompts = service.search_prompts(project="DemoProject")
    rated = batch_processor.batch_update_ratings(
        [p.id for p in all_prompts],
        auto_rate_by_success
    )
    print(f"   Auto-rated {rated} prompts")

    # Auto-tag prompts
    from alicemultiverse.prompts.batch import auto_tag_by_content
    tagged = batch_processor.batch_tag_prompts(all_prompts, auto_tag_by_content)
    print(f"   Auto-tagged {tagged} prompts")

    # 9. Generate variations
    print("\n8. Generating prompt variations...")

    variations = batch_processor.batch_generate_variations(
        prompt1,
        [
            {"modification": "with dramatic storm clouds", "purpose": "Add drama"},
            {"modification": "in minimalist style", "purpose": "Style variation"},
            {"modification": "from aerial perspective", "purpose": "Change viewpoint"}
        ]
    )
    print(f"   Generated {len(variations)} variations")

    # 10. Project insights
    print("\n9. Analyzing project insights...")

    project_data = integration.find_prompts_for_project("DemoProject")
    stats = project_data["statistics"]

    print(f"   Total prompts: {stats['total_prompts']}")
    print(f"   Total uses: {stats['total_uses']}")
    print(f"   Total cost: ${stats['total_cost']:.2f}")

    if stats["by_category"]:
        print("   By category:")
        for cat, count in stats["by_category"].items():
            print(f"     - {cat}: {count}")

    # 11. Export data
    print("\n10. Exporting data...")

    # Export project prompts
    export_path = project_path / "prompt_export.json"
    service.export_prompts(export_path, project_data["prompts"])
    print(f"    Exported to: {export_path}")

    # Export insights
    insights_path = project_path / "project_insights.json"
    integration.export_project_insights("DemoProject", insights_path)
    print(f"    Insights saved to: {insights_path}")

    # 12. Sync operations
    print("\n11. Syncing project prompts...")

    # Discover prompts in projects
    discovered = storage.discover_project_prompts([project_path.parent])
    print(f"    Discovered prompts in {len(discovered)} projects")

    # Final summary
    print("\n=== Summary ===")
    print(f"Created {stats['total_prompts']} prompts")
    print(f"Recorded {stats['total_uses']} usage instances")
    print(f"Generated {len(variations)} variations")
    print(f"Project location: {project_path}")
    print("\nPrompt files:")
    print(f"  - {project_path}/.alice/prompts/prompts.yaml")
    print(f"  - {project_path}/.alice/prompts/*.yaml (individual prompts)")
    print(f"  - {export_path}")
    print(f"  - {insights_path}")

    print("\n✅ Demo completed successfully!")


# Example: Integration with providers
async def provider_integration_example():
    """Show how to integrate prompt tracking with providers."""

    # Mock provider for demonstration
    class MockImageProvider:
        def __init__(self):
            self.name = "mock_provider"

        @track_prompt_usage("mock_provider")
        async def generate(self, prompt: str, **kwargs):
            # Simulate generation
            await asyncio.sleep(0.1)

            from alicemultiverse.providers.types import GenerationResult
            return GenerationResult(
                success=True,
                file_path=Path(f"/tmp/mock_{datetime.now().timestamp()}.png"),
                asset_id=f"mock-{datetime.now().timestamp()}",
                generation_id=f"gen-{datetime.now().timestamp()}",
                cost=0.05,
                metadata={
                    "prompt": prompt,
                    "provider": self.name,
                    "model": "mock-v1",
                    "project": kwargs.get("project")
                }
            )

    # Use the provider
    provider = MockImageProvider()

    # Generate with automatic tracking
    result = await provider.generate(
        "A beautiful sunset over the ocean",
        project="DemoProject"
    )

    print(f"Generated: {result.asset_id}")
    print("Prompt automatically tracked!")


# Example: CSV import
def csv_import_example():
    """Show how to import prompts from CSV."""

    # Create sample CSV
    csv_path = Path("sample_prompts.csv")
    csv_content = """text,category,providers,tags,project,style,description
"Epic fantasy castle on a mountain",image_generation,"midjourney,flux","fantasy,castle,epic",FantasyProject,fantasy,"Creates epic fantasy architecture"
"Futuristic spacecraft in orbit",image_generation,"midjourney,stable_diffusion","scifi,space,futuristic",SciFiProject,scifi,"Detailed spacecraft designs"
"Abstract geometric patterns",image_generation,"flux,leonardo","abstract,geometric,modern",AbstractArt,abstract,"Modern abstract compositions"
"""

    with open(csv_path, 'w') as f:
        f.write(csv_content)

    # Import
    processor = PromptBatchProcessor()
    imported = processor.batch_create_from_csv(csv_path)

    print(f"Imported {len(imported)} prompts from CSV")

    # Clean up
    csv_path.unlink()


if __name__ == "__main__":
    # Run main demo
    main()

    print("\n" + "="*50 + "\n")

    # Run provider integration example
    print("=== Provider Integration Example ===")
    asyncio.run(provider_integration_example())

    print("\n" + "="*50 + "\n")

    # Run CSV import example
    print("=== CSV Import Example ===")
    csv_import_example()
