#!/usr/bin/env python3
"""
Image Understanding Demo

This example demonstrates the new image understanding capabilities that replace
the old quality assessment system. It shows how to:

1. Analyze images with multiple AI providers
2. Extract semantic tags for searchability
3. Generate prompts from existing images
4. Compare different providers' insights
5. Embed metadata in files for portability
"""

import asyncio
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()


async def single_image_analysis():
    """Analyze a single image with the default (cheapest) provider."""
    from alicemultiverse.understanding import ImageAnalyzer

    console.print("\n[bold cyan]Single Image Analysis Demo[/bold cyan]\n")

    # Initialize analyzer
    analyzer = ImageAnalyzer()

    # Check available providers
    providers = analyzer.get_available_providers()
    console.print(f"Available providers: {', '.join(providers)}")

    if not providers:
        console.print("[red]No providers available! Please set API keys:[/red]")
        console.print("- ANTHROPIC_API_KEY")
        console.print("- OPENAI_API_KEY")
        console.print("- GOOGLE_AI_API_KEY or GEMINI_API_KEY")
        console.print("- DEEPSEEK_API_KEY")
        return

    # Find a test image
    test_image = Path("examples/sample_image.jpg")
    if not test_image.exists():
        # Try to find any image
        for pattern in ["*.jpg", "*.png", "*.webp"]:
            images = list(Path(".").glob(pattern))
            if images:
                test_image = images[0]
                break

    if not test_image.exists():
        console.print("[yellow]No test image found. Using a placeholder path.[/yellow]")
        test_image = Path("test.jpg")

    console.print(f"\nAnalyzing: {test_image}")

    try:
        # Analyze with default provider (cheapest)
        result = await analyzer.analyze(
            test_image,
            generate_prompt=True,
            extract_tags=True,
            detailed=False
        )

        # Display results
        console.print(f"\n[green]Analysis by {result.provider} ({result.model}):[/green]")
        console.print(f"Cost: ${result.cost:.4f}")

        # Description
        console.print("\n[bold]Description:[/bold]")
        console.print(Panel(result.description, expand=False))

        # Tags
        if result.tags:
            console.print("\n[bold]Extracted Tags:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Category", style="cyan")
            table.add_column("Tags", style="green")

            for category, tags in sorted(result.tags.items()):
                table.add_row(category, ", ".join(tags))

            console.print(table)

        # Generated prompt
        if result.generated_prompt:
            console.print("\n[bold]Generated Prompt:[/bold]")
            console.print(Panel(result.generated_prompt, expand=False))

        if result.negative_prompt:
            console.print("\n[bold]Negative Prompt:[/bold]")
            console.print(Panel(result.negative_prompt, expand=False))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def multi_provider_comparison():
    """Compare analysis results from multiple providers."""
    from alicemultiverse.understanding import ImageAnalyzer

    console.print("\n[bold cyan]Multi-Provider Comparison Demo[/bold cyan]\n")

    analyzer = ImageAnalyzer()
    providers = analyzer.get_available_providers()

    if len(providers) < 2:
        console.print("[yellow]Need at least 2 providers for comparison.[/yellow]")
        return

    test_image = Path("examples/sample_image.jpg")

    # Get cost estimates
    console.print("\n[bold]Cost Estimates:[/bold]")
    costs = analyzer.estimate_costs(detailed=False)
    for provider, cost in sorted(costs.items(), key=lambda x: x[1]):
        console.print(f"- {provider}: ${cost:.4f} per image")

    # Compare all providers
    console.print(f"\n[bold]Comparing providers on {test_image}:[/bold]")

    results = await analyzer.compare_providers(
        test_image,
        generate_prompt=True,
        extract_tags=True,
        detailed=False
    )

    # Create comparison table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Provider", style="cyan")
    table.add_column("Cost", style="yellow")
    table.add_column("Tags", style="green")
    table.add_column("Tokens", style="blue")

    total_cost = 0
    all_tags = set()

    for provider, result in results.items():
        tag_count = len(result.get_all_tags())
        all_tags.update(result.get_all_tags())
        total_cost += result.cost

        table.add_row(
            provider,
            f"${result.cost:.4f}",
            str(tag_count),
            str(result.tokens_used or "N/A")
        )

    console.print(table)
    console.print(f"\nTotal cost: ${total_cost:.4f}")
    console.print(f"Unique tags discovered: {len(all_tags)}")

    # Show how tags differ
    console.print("\n[bold]Tag Analysis:[/bold]")
    for provider, result in results.items():
        unique_tags = set(result.get_all_tags()) - (all_tags - set(result.get_all_tags()))
        if unique_tags:
            console.print(f"{provider} unique: {', '.join(sorted(unique_tags))}")


async def pipeline_integration():
    """Show how image understanding integrates with the pipeline."""
    console.print("\n[bold cyan]Pipeline Integration Demo[/bold cyan]\n")

    # This would normally be part of the organization pipeline
    console.print("Example pipeline configuration:")
    console.print(Panel("""
pipeline:
  mode: standard  # Uses DeepSeek + Google (cost-effective)
  detailed: false
  stages:
    - understanding_deepseek
    - understanding_google

# Or for premium analysis:
pipeline:
  mode: premium  # Uses all providers
  detailed: true
    """, expand=False))

    console.print("\nThe pipeline will:")
    console.print("1. Analyze each image during organization")
    console.print("2. Extract and merge tags from multiple providers")
    console.print("3. Embed all metadata in the image files")
    console.print("4. Update the search index automatically")


async def batch_analysis():
    """Demonstrate batch analysis of multiple images."""
    from alicemultiverse.understanding import ImageAnalyzer

    console.print("\n[bold cyan]Batch Analysis Demo[/bold cyan]\n")

    analyzer = ImageAnalyzer()

    # Find multiple images
    images = []
    for pattern in ["*.jpg", "*.png", "*.webp"]:
        images.extend(list(Path(".").glob(pattern))[:5])  # Max 5 images

    if not images:
        console.print("[yellow]No images found for batch analysis.[/yellow]")
        return

    console.print(f"Found {len(images)} images to analyze")

    # Choose provider based on budget
    budget = 0.10  # $0.10 total budget
    best_provider = await analyzer.find_best_provider_for_budget(
        budget, len(images), detailed=False
    )

    if not best_provider:
        console.print(f"[red]No provider fits budget of ${budget:.2f}[/red]")
        return

    console.print(f"Using {best_provider} to fit budget of ${budget:.2f}")

    # Analyze batch
    results = await analyzer.analyze_batch(
        images,
        provider=best_provider,
        generate_prompt=False,  # Save tokens
        extract_tags=True,
        max_concurrent=3
    )

    # Summary
    total_cost = sum(r.cost for r in results)
    total_tags = sum(len(r.get_all_tags()) for r in results)

    console.print("\n[green]Batch complete![/green]")
    console.print(f"- Analyzed: {len(results)} images")
    console.print(f"- Total cost: ${total_cost:.4f}")
    console.print(f"- Total tags: {total_tags}")
    console.print(f"- Avg tags/image: {total_tags/len(results):.1f}")


async def main():
    """Run all demos."""
    console.print("""
[bold magenta]AliceMultiverse Image Understanding Demo[/bold magenta]

This demo shows the new image understanding system that replaces
quality assessment. Instead of subjective quality scores, we now
extract semantic information to make images searchable.
    """)

    # Run demos
    await single_image_analysis()
    await multi_provider_comparison()
    await pipeline_integration()
    await batch_analysis()

    console.print("\n[bold green]Demo complete![/bold green]")
    console.print("\nKey benefits over quality assessment:")
    console.print("- Semantic tags for better search")
    console.print("- Multiple provider perspectives")
    console.print("- Prompt generation from images")
    console.print("- Cost-aware processing")
    console.print("- All metadata embedded in files")


if __name__ == "__main__":
    asyncio.run(main())
