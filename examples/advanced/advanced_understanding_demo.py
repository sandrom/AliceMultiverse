#!/usr/bin/env python3
"""
Advanced Image Understanding Demo

This demo showcases the new advanced image understanding capabilities:

1. Hierarchical tagging with custom vocabularies
2. Project-specific custom instructions
3. Batch analysis with progress tracking and cost management
4. Provider optimization with automatic failover
5. Comprehensive tag expansion and specialized categories

This builds upon the basic image understanding system with enterprise-grade features.
"""

import asyncio
import logging
import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from alicemultiverse.understanding import (
    AdvancedTagger,
    BatchAnalysisRequest,
    BatchAnalyzer,
    CustomInstructionManager,
    ImageAnalyzer,
    ProviderOptimizer,
    TagVocabulary,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()


async def demo_hierarchical_tagging():
    """Demonstrate hierarchical tag expansion."""
    console.print("\n[bold cyan]🏷️  Hierarchical Tagging Demo[/bold cyan]\n")

    # Initialize tag vocabulary
    vocab = TagVocabulary()

    # Show hierarchy structure
    console.print("[bold]Animal Hierarchy Example:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tag", style="cyan")
    table.add_column("Parent", style="yellow")
    table.add_column("Children", style="green")

    animal_hierarchy = vocab.hierarchies["animal"]
    for tag_name, tag_obj in list(animal_hierarchy.items())[:8]:  # Show first 8
        children = ", ".join(tag_obj.children[:3])  # Show max 3 children
        if len(tag_obj.children) > 3:
            children += f" (+{len(tag_obj.children) - 3} more)"

        table.add_row(
            tag_name,
            tag_obj.parent or "—",
            children or "—"
        )

    console.print(table)

    # Demonstrate tag expansion
    console.print("\n[bold]Tag Expansion Example:[/bold]")
    original_tag = "golden_retriever"
    expanded = vocab.expand_tag("animal", original_tag, include_ancestors=True)

    console.print(f"Original tag: [cyan]{original_tag}[/cyan]")
    console.print(f"Expanded tags: [green]{', '.join(expanded)}[/green]")
    console.print("This improves searchability - searching for 'dog' will find 'golden_retriever' images!")


async def demo_custom_instructions():
    """Demonstrate custom instruction management."""
    console.print("\n[bold cyan]📝 Custom Instructions Demo[/bold cyan]\n")

    # Initialize instruction manager
    instruction_manager = CustomInstructionManager()

    # Show available templates
    templates = instruction_manager.list_templates()
    console.print(f"[bold]Available Templates:[/bold] {len(templates)} templates loaded")

    template_table = Table(show_header=True, header_style="bold magenta")
    template_table.add_column("ID", style="cyan")
    template_table.add_column("Name", style="yellow")
    template_table.add_column("Variables", style="green")

    for template in templates[:3]:  # Show first 3
        vars_str = ", ".join(template.variables.keys()) if template.variables else "None"
        template_table.add_row(template.id, template.name, vars_str)

    console.print(template_table)

    # Create a custom project
    project_id = "fashion_photoshoot"

    console.print(f"\n[bold]Setting up project:[/bold] {project_id}")

    # Set project-specific instructions
    project_instructions = {
        "general": "Focus on fashion elements, styling, and brand positioning for luxury fashion photography.",
        "portrait": "Analyze model pose, expression, and styling choices for high-end fashion."
    }

    project_templates = ["fashion_detailed"]
    project_variables = {
        "additional_focus": "Pay special attention to luxury brand positioning and target market appeal"
    }

    instruction_manager.set_project_instructions(
        project_id,
        project_instructions,
        project_templates,
        project_variables
    )

    # Build complete instructions for the project
    complete_instructions = instruction_manager.build_analysis_instructions(
        project_id,
        category="general"
    )

    console.print("\n[bold]Generated Instructions for Project:[/bold]")
    console.print(Panel(complete_instructions[:500] + "...", title="Custom Instructions", expand=False))


async def demo_provider_optimization():
    """Demonstrate provider optimization and cost management."""
    console.print("\n[bold cyan]⚡ Provider Optimization Demo[/bold cyan]\n")

    # Initialize analyzer and optimizer
    analyzer = ImageAnalyzer()
    available_providers = analyzer.get_available_providers()

    if not available_providers:
        console.print("[red]No providers available. Please set API keys to see optimization in action.[/red]")
        return

    console.print(f"[bold]Available Providers:[/bold] {', '.join(available_providers)}")

    # Initialize optimizer
    optimizer = ProviderOptimizer(analyzer)

    # Set budget constraints
    budget = 5.0  # $5 total budget
    daily_budget = 2.0  # $2 daily limit
    optimizer.set_budget(budget, daily_budget=daily_budget)

    console.print(f"\n[bold]Budget Set:[/bold] ${budget:.2f} total, ${daily_budget:.2f} daily")

    # Show cost estimates
    console.print("\n[bold]Cost Estimates:[/bold]")
    costs = analyzer.estimate_costs(detailed=False)

    cost_table = Table(show_header=True, header_style="bold magenta")
    cost_table.add_column("Provider", style="cyan")
    cost_table.add_column("Cost per Image", style="yellow")
    cost_table.add_column("100 Images", style="green")

    for provider, cost in sorted(costs.items(), key=lambda x: x[1]):
        cost_table.add_row(
            provider,
            f"${cost:.4f}",
            f"${cost * 100:.2f}"
        )

    console.print(cost_table)

    # Demonstrate optimal provider selection
    optimal_provider = optimizer.select_optimal_provider(
        optimization_criteria="cost_efficiency",
        budget_limit=0.01,
        detailed=False
    )

    console.print(f"\n[bold]Optimal Provider:[/bold] {optimal_provider or 'None within budget'}")

    # Show provider statistics (mock data since we haven't run analyses)
    stats = optimizer.get_provider_statistics()
    if stats:
        console.print("\n[bold]Provider Statistics:[/bold]")
        for provider, data in stats.items():
            console.print(f"• {provider}: {data['requests']['total']} requests, "
                         f"{data['performance']['uptime_percentage']} uptime")


async def demo_batch_analysis():
    """Demonstrate advanced batch analysis capabilities."""
    console.print("\n[bold cyan]🔄 Batch Analysis Demo[/bold cyan]\n")

    analyzer = ImageAnalyzer()
    batch_analyzer = BatchAnalyzer(analyzer)

    # Create some mock images for demonstration
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        image_paths = []

        # Create 5 mock image files
        for i in range(5):
            img_path = temp_dir / f"fashion_photo_{i:02d}.jpg"
            img_path.touch()  # Create empty file
            image_paths.append(img_path)

        console.print(f"[bold]Created {len(image_paths)} mock images for batch processing[/bold]")

        # Create batch request
        request = BatchAnalysisRequest(
            image_paths=image_paths,
            project_id="fashion_photoshoot",
            provider=None,  # Auto-select optimal
            max_concurrent=3,
            max_cost=1.0,  # $1 budget limit
            detailed=False,
            show_progress=True,
            checkpoint_interval=2
        )

        console.print("\n[bold]Batch Request Configuration:[/bold]")
        config_table = Table(show_header=False)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="yellow")

        config_table.add_row("Images", str(len(image_paths)))
        config_table.add_row("Max Concurrent", str(request.max_concurrent))
        config_table.add_row("Budget Limit", f"${request.max_cost:.2f}")
        config_table.add_row("Progress Tracking", "✓ Enabled")
        config_table.add_row("Checkpointing", f"Every {request.checkpoint_interval} images")

        console.print(config_table)

        # Estimate costs
        try:
            estimated_cost, cost_details = await batch_analyzer.estimate_cost(request)

            console.print("\n[bold]Cost Estimation:[/bold]")
            console.print(f"• Total estimated cost: [green]${estimated_cost:.4f}[/green]")
            console.print(f"• Selected provider: [cyan]{cost_details.get('selected_provider', 'None')}[/cyan]")
            console.print(f"• Images to process: [yellow]{cost_details.get('image_count', 0)}[/yellow]")

            if estimated_cost > request.max_cost:
                console.print("[red]⚠️  Estimated cost exceeds budget limit![/red]")
            else:
                console.print("[green]✓ Within budget - ready to process[/green]")

        except Exception as e:
            console.print(f"[yellow]Cost estimation not available: {e}[/yellow]")
            console.print("[italic]This is normal without API keys - batch system is still demonstrated[/italic]")


async def demo_advanced_tagging():
    """Demonstrate advanced tagging with specialized categories."""
    console.print("\n[bold cyan]🎯 Advanced Tagging Demo[/bold cyan]\n")

    # Mock repository for demonstration
    mock_repo = None  # In real usage, would be AssetRepository()

    # Initialize advanced tagger
    tagger = AdvancedTagger(mock_repo) if mock_repo else None

    if not tagger:
        console.print("[yellow]Advanced tagger requires database repository in production[/yellow]")
        console.print("[italic]Showing conceptual example instead:[/italic]\n")

    # Show specialized categories
    console.print("[bold]Specialized Tag Categories:[/bold]")
    categories = [
        ("mood", "emotional", "Emotional tone and atmosphere"),
        ("composition", "technical", "Photographic composition elements"),
        ("technical_quality", "technical", "Image quality and technical aspects"),
        ("artistic_style", "creative", "Artistic movement and style influences"),
        ("fashion", "domain", "Fashion-specific elements"),
        ("color_palette", "visual", "Color schemes and palettes"),
        ("cultural", "contextual", "Cultural and historical references"),
        ("activity", "content", "Actions and activities depicted"),
    ]

    category_table = Table(show_header=True, header_style="bold magenta")
    category_table.add_column("Category", style="cyan")
    category_table.add_column("Type", style="yellow")
    category_table.add_column("Description", style="green")

    for category, type_, description in categories:
        category_table.add_row(category, type_, description)

    console.print(category_table)

    # Example of tag expansion
    console.print("\n[bold]Example Tag Expansion:[/bold]")
    console.print("Original analysis might detect: [cyan]'portrait', 'woman', 'studio'[/cyan]")
    console.print("Advanced tagger adds:")
    console.print("• [green]Hierarchical:[/green] 'person' → 'human' → 'subject'")
    console.print("• [green]Mood:[/green] 'professional', 'confident' (from pose)")
    console.print("• [green]Technical:[/green] 'studio_lighting', 'shallow_dof'")
    console.print("• [green]Composition:[/green] 'close_up', 'rule_of_thirds'")
    console.print("• [green]Fashion:[/green] 'business_attire', 'formal'")


async def demo_complete_workflow():
    """Demonstrate the complete advanced understanding workflow."""
    console.print("\n[bold cyan]🚀 Complete Advanced Workflow[/bold cyan]\n")

    console.print("[bold]Workflow Steps:[/bold]")

    steps = [
        ("1. Project Setup", "Create project with custom instructions and vocabulary"),
        ("2. Cost Planning", "Estimate costs and set budget constraints"),
        ("3. Provider Selection", "Choose optimal provider based on cost/quality"),
        ("4. Batch Processing", "Process images with progress tracking"),
        ("5. Tag Enhancement", "Apply hierarchical and specialized tags"),
        ("6. Database Storage", "Store results with full metadata"),
        ("7. Quality Monitoring", "Track provider performance and costs"),
    ]

    workflow_table = Table(show_header=False, box=None)
    workflow_table.add_column("Step", style="bold cyan")
    workflow_table.add_column("Description", style="white")

    for step, description in steps:
        workflow_table.add_row(step, description)

    console.print(workflow_table)

    console.print("\n[bold]Key Benefits:[/bold]")
    benefits = [
        "🎯 [green]Precision:[/green] Hierarchical tags improve search accuracy",
        "💰 [green]Cost Control:[/green] Budget management and provider optimization",
        "📈 [green]Scalability:[/green] Efficient batch processing with checkpoints",
        "🔧 [green]Customization:[/green] Project-specific instructions and vocabularies",
        "📊 [green]Monitoring:[/green] Comprehensive cost and performance tracking",
        "🔄 [green]Reliability:[/green] Automatic failover and retry mechanisms",
    ]

    for benefit in benefits:
        console.print(f"  {benefit}")


async def main():
    """Run all advanced understanding demos."""
    console.print("""
[bold magenta]AliceMultiverse Advanced Image Understanding Demo[/bold magenta]

This demo showcases enterprise-grade image understanding capabilities that extend
the basic system with hierarchical tagging, custom instructions, batch processing,
provider optimization, and comprehensive cost management.
    """)

    try:
        # Run all demos
        await demo_hierarchical_tagging()
        await demo_custom_instructions()
        await demo_provider_optimization()
        await demo_batch_analysis()
        await demo_advanced_tagging()
        await demo_complete_workflow()

        console.print("\n[bold green]✅ Advanced Understanding Demo Complete![/bold green]")

        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Set up API keys: [cyan]alice keys setup[/cyan]")
        console.print("2. Configure project: [cyan]alice project create my_project[/cyan]")
        console.print("3. Run advanced analysis: [cyan]alice organize --pipeline advanced[/cyan]")
        console.print("4. Monitor costs: [cyan]alice costs report[/cyan]")

    except Exception as e:
        console.print(f"[red]Demo failed: {e}[/red]")
        logger.exception("Demo execution failed")


if __name__ == "__main__":
    asyncio.run(main())
