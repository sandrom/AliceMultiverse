"""Example of integrating prompt tracking with providers."""

import asyncio
from pathlib import Path

# Example 1: Adding prompt tracking to a provider using decorators
from alicemultiverse.providers.provider import Provider
from alicemultiverse.providers.types import GenerationResult
from alicemultiverse.prompts import track_prompt_usage, PromptTrackingMixin


class ExampleProvider(Provider, PromptTrackingMixin):
    """Example provider with automatic prompt tracking."""
    
    def __init__(self, api_key: str, **kwargs):
        # Initialize both parent classes
        Provider.__init__(self, api_key)
        PromptTrackingMixin.__init__(self, **kwargs)
    
    @track_prompt_usage("example_provider")
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate with automatic prompt tracking."""
        # Your generation logic here
        result = GenerationResult(
            success=True,
            file_path=Path("/tmp/example.png"),
            asset_id="example-123",
            generation_id="gen-456",
            cost=0.05,
            metadata={
                "prompt": prompt,
                "model": "example-v1",
                "project": kwargs.get("project"),
                "parameters": kwargs
            }
        )
        
        # The decorator automatically tracks this prompt usage
        return result


# Example 2: Manual prompt tracking
async def manual_tracking_example():
    """Example of manually tracking prompt usage."""
    from alicemultiverse.prompts import PromptService
    from alicemultiverse.prompts.models import PromptCategory, ProviderType
    
    # Initialize service
    service = PromptService()
    
    # Create a prompt
    prompt = service.create_prompt(
        text="A futuristic city with flying cars at sunset, cyberpunk style",
        category=PromptCategory.IMAGE_GENERATION,
        providers=[ProviderType.MIDJOURNEY, ProviderType.FLUX],
        tags=["cyberpunk", "cityscape", "futuristic"],
        project="FutureCities",
        style="cyberpunk",
        description="Creates dramatic futuristic cityscapes",
        context={
            "aspect_ratio": "16:9",
            "quality": "high"
        }
    )
    
    # Record usage
    usage = service.record_usage(
        prompt_id=prompt.id,
        provider=ProviderType.MIDJOURNEY,
        success=True,
        output_path="/path/to/output.png",
        cost=0.10,
        duration_seconds=15.5,
        notes="Great result with v6"
    )
    
    print(f"Created prompt: {prompt.id}")
    print(f"Recorded usage: {usage.id}")


# Example 3: Project-based prompt management
def project_prompt_example():
    """Example of managing prompts within a project."""
    from alicemultiverse.prompts import ProjectPromptStorage, PromptService
    from alicemultiverse.prompts.models import Prompt, PromptCategory, ProviderType
    
    # Initialize storage
    storage = ProjectPromptStorage(format="yaml")
    service = PromptService()
    
    # Create project directory
    project_path = Path("~/Projects/MyArtProject").expanduser()
    project_path.mkdir(exist_ok=True)
    
    # Initialize prompt storage in project
    storage.initialize_project_prompts(project_path)
    
    # Create and save a prompt
    prompt = Prompt(
        id="proj-001",
        text="Abstract geometric patterns with vibrant colors",
        category=PromptCategory.IMAGE_GENERATION,
        providers=[ProviderType.MIDJOURNEY],
        tags=["abstract", "geometric", "colorful"],
        project="MyArtProject",
        style="abstract",
        description="Creates modern abstract art",
        effectiveness_rating=8.5
    )
    
    # Save to project
    saved_path = storage.save_to_project(prompt, project_path)
    print(f"Saved prompt to: {saved_path}")
    
    # Sync to central index
    synced = storage.sync_project_to_index(project_path)
    print(f"Synced {synced} prompts to index")


# Example 4: Finding and analyzing prompts
def analysis_example():
    """Example of finding and analyzing prompts."""
    from alicemultiverse.prompts import PromptService, PromptProviderIntegration
    from alicemultiverse.prompts.models import PromptCategory, ProviderType
    
    service = PromptService()
    integration = PromptProviderIntegration(service)
    
    # Search for effective prompts
    effective_prompts = service.get_effective_prompts(
        category=PromptCategory.IMAGE_GENERATION,
        provider=ProviderType.MIDJOURNEY,
        min_success_rate=0.8,
        min_uses=5
    )
    
    print(f"\nFound {len(effective_prompts)} effective prompts:")
    for prompt in effective_prompts[:3]:
        print(f"- {prompt.text[:50]}...")
        print(f"  Success rate: {prompt.success_rate()*100:.1f}%")
        print(f"  Uses: {prompt.use_count}")
    
    # Get project insights
    project_data = integration.find_prompts_for_project("MyArtProject")
    stats = project_data["statistics"]
    
    print(f"\nProject Statistics:")
    print(f"Total prompts: {stats['total_prompts']}")
    print(f"Total uses: {stats['total_uses']}")
    print(f"Total cost: ${stats['total_cost']:.2f}")
    
    # Export insights
    output_path = Path("project_insights.json")
    integration.export_project_insights("MyArtProject", output_path)
    print(f"\nExported insights to: {output_path}")


# Example 5: Working with prompt variations
def variations_example():
    """Example of creating and managing prompt variations."""
    from alicemultiverse.prompts import PromptService
    from alicemultiverse.prompts.models import PromptCategory, ProviderType
    
    service = PromptService()
    
    # Create base prompt
    base_prompt = service.create_prompt(
        text="A serene mountain landscape at dawn",
        category=PromptCategory.IMAGE_GENERATION,
        providers=[ProviderType.MIDJOURNEY],
        tags=["landscape", "nature", "mountains"],
        style="photorealistic"
    )
    
    # Create variations
    variations = [
        ("A serene mountain landscape at dawn with mist",
         "Added atmospheric mist",
         "More mystical atmosphere"),
        ("A serene mountain landscape at golden hour",
         "Changed time to golden hour",
         "Warmer, more dramatic lighting"),
        ("A serene mountain landscape at dawn, oil painting style",
         "Changed to artistic style",
         "Artistic interpretation")
    ]
    
    for text, diff, purpose in variations:
        var_prompt = service.create_prompt(
            text=text,
            category=PromptCategory.IMAGE_GENERATION,
            providers=[ProviderType.MIDJOURNEY],
            parent_id=base_prompt.id,
            tags=base_prompt.tags + ["variation"],
            style=base_prompt.style,
            notes=f"Variation: {diff}\nPurpose: {purpose}"
        )
        
        # Link as related
        base_prompt.related_ids.append(var_prompt.id)
    
    service.update_prompt(base_prompt)
    
    # Find similar prompts
    similar = service.find_similar(base_prompt.id)
    print(f"\nFound {len(similar)} similar prompts to base")


if __name__ == "__main__":
    # Run examples
    print("=== Manual Tracking Example ===")
    asyncio.run(manual_tracking_example())
    
    print("\n=== Project Prompt Example ===")
    project_prompt_example()
    
    print("\n=== Analysis Example ===")
    analysis_example()
    
    print("\n=== Variations Example ===")
    variations_example()