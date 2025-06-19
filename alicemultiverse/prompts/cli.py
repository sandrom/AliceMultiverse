"""CLI commands for prompt management."""

from pathlib import Path

import click

# tabulate is optional, fallback to simple display
try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

from ..core.logging import get_logger
from .models import PromptCategory, ProviderType
from .service import PromptService

logger = get_logger(__name__)


@click.group(name="prompts")
def prompts_cli():
    """Manage AI prompts and their effectiveness."""


@prompts_cli.command()
@click.option("--text", "-t", required=True, help="The prompt text")
@click.option("--category", "-c", required=True,
              type=click.Choice([c.value for c in PromptCategory]),
              help="Prompt category")
@click.option("--providers", "-p", multiple=True, required=True,
              type=click.Choice([p.value for p in ProviderType]),
              help="Providers this prompt works with (can specify multiple)")
@click.option("--tags", multiple=True, help="Tags for organization")
@click.option("--project", help="Project name")
@click.option("--style", help="Style (e.g., cyberpunk, minimalist)")
@click.option("--description", "-d", help="What this prompt is good for")
@click.option("--notes", "-n", help="Additional notes or tips")
@click.option("--keywords", multiple=True, help="Additional search keywords")
def add(text: str, category: str, providers: list[str], **kwargs):
    """Add a new prompt to the library."""
    service = PromptService()

    # Convert string values to enums
    category_enum = PromptCategory(category)
    provider_enums = [ProviderType(p) for p in providers]

    # Filter out None values and empty lists
    cleaned_kwargs = {k: v for k, v in kwargs.items() if v and (not isinstance(v, tuple) or len(v) > 0)}

    # Convert tuples to lists
    if 'tags' in cleaned_kwargs:
        cleaned_kwargs['tags'] = list(cleaned_kwargs['tags'])
    if 'keywords' in cleaned_kwargs:
        cleaned_kwargs['keywords'] = list(cleaned_kwargs['keywords'])

    prompt = service.create_prompt(
        text=text,
        category=category_enum,
        providers=provider_enums,
        **cleaned_kwargs
    )

    click.echo(f"✅ Created prompt {prompt.id}")
    click.echo(f"Category: {category}")
    click.echo(f"Providers: {', '.join(providers)}")
    if cleaned_kwargs.get('tags'):
        click.echo(f"Tags: {', '.join(cleaned_kwargs['tags'])}")


@prompts_cli.command()
@click.option("--query", "-q", help="Search in prompt text, description, and notes")
@click.option("--category", "-c",
              type=click.Choice([c.value for c in PromptCategory]),
              help="Filter by category")
@click.option("--provider", "-p",
              type=click.Choice([p.value for p in ProviderType]),
              help="Filter by provider")
@click.option("--tag", "-t", multiple=True, help="Filter by tags")
@click.option("--project", help="Filter by project")
@click.option("--style", help="Filter by style")
@click.option("--min-effectiveness", type=float, help="Minimum effectiveness rating")
@click.option("--min-success-rate", type=float, help="Minimum success rate")
@click.option("--effective", is_flag=True, help="Show only highly effective prompts")
@click.option("--limit", default=20, help="Maximum results to show")
@click.option("--export", type=click.Path(path_type=Path), help="Export results to JSON")
def search(query: str | None, category: str | None, provider: str | None,
           tag: list[str], effective: bool, limit: int, export: Path | None, **kwargs):
    """Search for prompts by various criteria."""
    service = PromptService()

    # Build search criteria
    search_kwargs = {}
    if query:
        search_kwargs['query'] = query
    if category:
        search_kwargs['category'] = PromptCategory(category)
    if provider:
        search_kwargs['providers'] = [ProviderType(provider)]
    if tag:
        search_kwargs['tags'] = list(tag)

    # Add other filters
    for key in ['project', 'style', 'min_effectiveness', 'min_success_rate']:
        if kwargs.get(key):
            search_kwargs[key] = kwargs[key]

    # Use effective prompts preset
    if effective:
        search_kwargs['min_effectiveness'] = 7.0
        search_kwargs['min_success_rate'] = 0.7

    results = service.search_prompts(**search_kwargs)[:limit]

    if export:
        service.export_prompts(export, results)
        click.echo(f"Exported {len(results)} prompts to {export}")
        return

    # TODO: Review unreachable code - if not results:
    # TODO: Review unreachable code - click.echo("No prompts found matching criteria.")
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - # Display results in table format
    # TODO: Review unreachable code - table_data = []
    # TODO: Review unreachable code - for prompt in results:
    # TODO: Review unreachable code - # Truncate text for display
    # TODO: Review unreachable code - text_preview = prompt.text[:50] + "..." if len(prompt.text) > 50 else prompt.text

    # TODO: Review unreachable code - providers_str = ", ".join([p.value for p in prompt.providers[:2]])
    # TODO: Review unreachable code - if len(prompt.providers) > 2:
    # TODO: Review unreachable code - providers_str += f" +{len(prompt.providers) - 2}"

    # TODO: Review unreachable code - tags_str = ", ".join(prompt.tags[:3])
    # TODO: Review unreachable code - if len(prompt.tags) > 3:
    # TODO: Review unreachable code - tags_str += f" +{len(prompt.tags) - 3}"

    # TODO: Review unreachable code - effectiveness = f"{prompt.effectiveness_rating:.1f}" if prompt.effectiveness_rating else "-"
    # TODO: Review unreachable code - success_rate = f"{prompt.success_rate() * 100:.0f}%" if prompt.use_count > 0 else "-"

    # TODO: Review unreachable code - table_data.append([
    # TODO: Review unreachable code - prompt.id[:8],
    # TODO: Review unreachable code - text_preview,
    # TODO: Review unreachable code - prompt.category.value,
    # TODO: Review unreachable code - providers_str,
    # TODO: Review unreachable code - effectiveness,
    # TODO: Review unreachable code - success_rate,
    # TODO: Review unreachable code - prompt.use_count,
    # TODO: Review unreachable code - tags_str
    # TODO: Review unreachable code - ])

    # TODO: Review unreachable code - headers = ["ID", "Prompt", "Category", "Providers", "Rating", "Success", "Uses", "Tags"]

    # TODO: Review unreachable code - if tabulate:
    # TODO: Review unreachable code - click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Fallback to simple display
    # TODO: Review unreachable code - click.echo(" | ".join(headers))
    # TODO: Review unreachable code - click.echo("-" * 80)
    # TODO: Review unreachable code - for row in table_data:
    # TODO: Review unreachable code - click.echo(" | ".join(str(col) for col in row))

    # TODO: Review unreachable code - click.echo(f"\nFound {len(results)} prompts")


@prompts_cli.command()
@click.argument("prompt_id")
def show(prompt_id: str):
    """Show detailed information about a prompt."""
    service = PromptService()

    # Support partial ID matching
    if len(prompt_id) < 36:
        results = service.search_prompts()
        matches = [p for p in results if p.id.startswith(prompt_id)]
        if len(matches) == 0:
            click.echo(f"No prompt found with ID starting with '{prompt_id}'")
            return
        # TODO: Review unreachable code - elif len(matches) > 1:
        # TODO: Review unreachable code - click.echo(f"Multiple prompts found starting with '{prompt_id}':")
        # TODO: Review unreachable code - for p in matches[:5]:
        # TODO: Review unreachable code - click.echo(f"  {p.id}: {p.text[:50]}...")
        # TODO: Review unreachable code - return
        # TODO: Review unreachable code - prompt = matches[0]
    else:
        prompt = service.get_prompt(prompt_id)
        if not prompt:
            click.echo(f"Prompt not found: {prompt_id}")
            return

    # TODO: Review unreachable code - # Display prompt details
    # TODO: Review unreachable code - click.echo(f"\n{'='*60}")
    # TODO: Review unreachable code - click.echo(f"ID: {prompt.id}")
    # TODO: Review unreachable code - click.echo(f"Created: {prompt.created_at.strftime('%Y-%m-%d %H:%M')}")
    # TODO: Review unreachable code - click.echo(f"Updated: {prompt.updated_at.strftime('%Y-%m-%d %H:%M')}")
    # TODO: Review unreachable code - click.echo(f"\nCategory: {prompt.category.value}")
    # TODO: Review unreachable code - click.echo(f"Providers: {', '.join([p.value for p in prompt.providers])}")

    # TODO: Review unreachable code - if prompt.project:
    # TODO: Review unreachable code - click.echo(f"Project: {prompt.project}")
    # TODO: Review unreachable code - if prompt.style:
    # TODO: Review unreachable code - click.echo(f"Style: {prompt.style}")
    # TODO: Review unreachable code - if prompt.tags:
    # TODO: Review unreachable code - click.echo(f"Tags: {', '.join(prompt.tags)}")

    # TODO: Review unreachable code - click.echo("\n--- PROMPT TEXT ---")
    # TODO: Review unreachable code - click.echo(prompt.text)

    # TODO: Review unreachable code - if prompt.description:
    # TODO: Review unreachable code - click.echo("\n--- DESCRIPTION ---")
    # TODO: Review unreachable code - click.echo(prompt.description)

    # TODO: Review unreachable code - if prompt.notes:
    # TODO: Review unreachable code - click.echo("\n--- NOTES ---")
    # TODO: Review unreachable code - click.echo(prompt.notes)

    # TODO: Review unreachable code - if prompt.context:
    # TODO: Review unreachable code - click.echo("\n--- CONTEXT ---")
    # TODO: Review unreachable code - for key, value in prompt.context.items():
    # TODO: Review unreachable code - click.echo(f"  {key}: {value}")

    # TODO: Review unreachable code - click.echo("\n--- STATISTICS ---")
    # TODO: Review unreachable code - click.echo(f"Uses: {prompt.use_count}")
    # TODO: Review unreachable code - click.echo(f"Successes: {prompt.success_count}")
    # TODO: Review unreachable code - click.echo(f"Success Rate: {prompt.success_rate() * 100:.1f}%")
    # TODO: Review unreachable code - if prompt.effectiveness_rating:
    # TODO: Review unreachable code - click.echo(f"Effectiveness Rating: {prompt.effectiveness_rating}/10")

    # TODO: Review unreachable code - # Show recent usage
    # TODO: Review unreachable code - usage_history = service.get_usage_history(prompt.id, limit=5)
    # TODO: Review unreachable code - if usage_history:
    # TODO: Review unreachable code - click.echo("\n--- RECENT USAGE ---")
    # TODO: Review unreachable code - for usage in usage_history:
    # TODO: Review unreachable code - status = "✅" if usage.success else "❌"
    # TODO: Review unreachable code - click.echo(f"{status} {usage.timestamp.strftime('%Y-%m-%d %H:%M')} - {usage.provider.value}")
    # TODO: Review unreachable code - if usage.notes:
    # TODO: Review unreachable code - click.echo(f"   Notes: {usage.notes}")

    # TODO: Review unreachable code - # Show similar prompts
    # TODO: Review unreachable code - similar = service.find_similar(prompt.id, limit=3)
    # TODO: Review unreachable code - if similar:
    # TODO: Review unreachable code - click.echo("\n--- SIMILAR PROMPTS ---")
    # TODO: Review unreachable code - for sim in similar:
    # TODO: Review unreachable code - click.echo(f"• {sim.id[:8]}: {sim.text[:60]}...")


@prompts_cli.command()
@click.argument("prompt_id")
@click.option("--provider", "-p", required=True,
              type=click.Choice([p.value for p in ProviderType]),
              help="Provider used")
@click.option("--success/--failure", default=True, help="Was it successful?")
@click.option("--output", "-o", help="Path to generated output")
@click.option("--cost", type=float, help="API cost")
@click.option("--duration", type=float, help="Generation time in seconds")
@click.option("--notes", "-n", help="Notes about this usage")
def use(prompt_id: str, provider: str, success: bool, **kwargs):
    """Record usage of a prompt."""
    service = PromptService()

    # Support partial ID matching
    if len(prompt_id) < 36:
        results = service.search_prompts()
        matches = [p for p in results if p.id.startswith(prompt_id)]
        if len(matches) == 0:
            click.echo(f"No prompt found with ID starting with '{prompt_id}'")
            return
        # TODO: Review unreachable code - elif len(matches) > 1:
        # TODO: Review unreachable code - click.echo(f"Multiple prompts found starting with '{prompt_id}':")
        # TODO: Review unreachable code - for p in matches[:5]:
        # TODO: Review unreachable code - click.echo(f"  {p.id}: {p.text[:50]}...")
        # TODO: Review unreachable code - return
        # TODO: Review unreachable code - prompt_id = matches[0].id

    service.record_usage(
        prompt_id=prompt_id,
        provider=ProviderType(provider),
        success=success,
        output_path=kwargs.get('output'),
        cost=kwargs.get('cost'),
        duration_seconds=kwargs.get('duration'),
        notes=kwargs.get('notes')
    )

    status = "✅ Success" if success else "❌ Failure"
    click.echo(f"{status} - Recorded usage of prompt {prompt_id[:8]} with {provider}")


@prompts_cli.command()
@click.argument("prompt_id")
@click.option("--rating", "-r", type=click.FloatRange(0, 10),
              help="Effectiveness rating (0-10)")
@click.option("--add-tag", multiple=True, help="Add tags")
@click.option("--remove-tag", multiple=True, help="Remove tags")
@click.option("--notes", "-n", help="Update notes")
@click.option("--description", "-d", help="Update description")
def update(prompt_id: str, rating: float | None, add_tag: list[str],
           remove_tag: list[str], notes: str | None, description: str | None):
    """Update prompt metadata."""
    service = PromptService()

    # Support partial ID matching
    if len(prompt_id) < 36:
        results = service.search_prompts()
        matches = [p for p in results if p.id.startswith(prompt_id)]
        if len(matches) == 0:
            click.echo(f"No prompt found with ID starting with '{prompt_id}'")
            return
        # TODO: Review unreachable code - elif len(matches) > 1:
        # TODO: Review unreachable code - click.echo(f"Multiple prompts found starting with '{prompt_id}':")
        # TODO: Review unreachable code - for p in matches[:5]:
        # TODO: Review unreachable code - click.echo(f"  {p.id}: {p.text[:50]}...")
        # TODO: Review unreachable code - return
        # TODO: Review unreachable code - prompt = matches[0]
    else:
        prompt = service.get_prompt(prompt_id)
        if not prompt:
            click.echo(f"Prompt not found: {prompt_id}")
            return

    # TODO: Review unreachable code - # Apply updates
    # TODO: Review unreachable code - updated = False

    # TODO: Review unreachable code - if rating is not None:
    # TODO: Review unreachable code - prompt.effectiveness_rating = rating
    # TODO: Review unreachable code - updated = True
    # TODO: Review unreachable code - click.echo(f"Set effectiveness rating to {rating}/10")

    # TODO: Review unreachable code - if add_tag:
    # TODO: Review unreachable code - for tag in add_tag:
    # TODO: Review unreachable code - if tag not in prompt.tags:
    # TODO: Review unreachable code - prompt.tags.append(tag)
    # TODO: Review unreachable code - updated = True
    # TODO: Review unreachable code - click.echo(f"Added tags: {', '.join(add_tag)}")

    # TODO: Review unreachable code - if remove_tag:
    # TODO: Review unreachable code - for tag in remove_tag:
    # TODO: Review unreachable code - if tag in prompt.tags:
    # TODO: Review unreachable code - prompt.tags.remove(tag)
    # TODO: Review unreachable code - updated = True
    # TODO: Review unreachable code - click.echo(f"Removed tags: {', '.join(remove_tag)}")

    # TODO: Review unreachable code - if notes is not None:
    # TODO: Review unreachable code - prompt.notes = notes
    # TODO: Review unreachable code - updated = True
    # TODO: Review unreachable code - click.echo("Updated notes")

    # TODO: Review unreachable code - if description is not None:
    # TODO: Review unreachable code - prompt.description = description
    # TODO: Review unreachable code - updated = True
    # TODO: Review unreachable code - click.echo("Updated description")

    # TODO: Review unreachable code - if updated:
    # TODO: Review unreachable code - service.update_prompt(prompt)
    # TODO: Review unreachable code - click.echo(f"✅ Updated prompt {prompt.id[:8]}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - click.echo("No changes made")


@prompts_cli.command()
@click.option("--category", "-c",
              type=click.Choice([c.value for c in PromptCategory]),
              help="Filter by category")
@click.option("--provider", "-p",
              type=click.Choice([p.value for p in ProviderType]),
              help="Filter by provider")
@click.option("--min-success-rate", type=float, default=0.7,
              help="Minimum success rate")
@click.option("--min-uses", type=int, default=3,
              help="Minimum number of uses")
@click.option("--limit", default=10, help="Number of results")
def effective(category: str | None, provider: str | None,
              min_success_rate: float, min_uses: int, limit: int):
    """Show the most effective prompts."""
    service = PromptService()

    category_enum = PromptCategory(category) if category else None
    provider_enum = ProviderType(provider) if provider else None

    prompts = service.get_effective_prompts(
        category=category_enum,
        provider=provider_enum,
        min_success_rate=min_success_rate,
        min_uses=min_uses,
        limit=limit
    )

    if not prompts:
        click.echo("No effective prompts found with the given criteria.")
        return

    # TODO: Review unreachable code - click.echo(f"\n🌟 TOP {len(prompts)} MOST EFFECTIVE PROMPTS")
    # TODO: Review unreachable code - click.echo("="*80)

    # TODO: Review unreachable code - for i, prompt in enumerate(prompts, 1):
    # TODO: Review unreachable code - click.echo(f"\n#{i}. {prompt.category.value.upper()} - {prompt.id[:8]}")
    # TODO: Review unreachable code - click.echo(f"Providers: {', '.join([p.value for p in prompt.providers])}")
    # TODO: Review unreachable code - click.echo(f"Success Rate: {prompt.success_rate() * 100:.1f}% ({prompt.success_count}/{prompt.use_count} uses)")
    # TODO: Review unreachable code - if prompt.effectiveness_rating:
    # TODO: Review unreachable code - click.echo(f"Rating: {prompt.effectiveness_rating}/10")
    # TODO: Review unreachable code - if prompt.tags:
    # TODO: Review unreachable code - click.echo(f"Tags: {', '.join(prompt.tags[:5])}")
    # TODO: Review unreachable code - click.echo(f"\nPrompt: {prompt.text[:150]}...")
    # TODO: Review unreachable code - if prompt.description:
    # TODO: Review unreachable code - click.echo(f"Good for: {prompt.description}")


@prompts_cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
def import_prompts(input_file: Path):
    """Import prompts from a JSON file."""
    service = PromptService()
    count = service.import_prompts(input_file)
    click.echo(f"✅ Imported {count} prompts from {input_file}")


@prompts_cli.command()
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option("--category", "-c",
              type=click.Choice([c.value for c in PromptCategory]),
              help="Export only this category")
def export(output_file: Path, category: str | None):
    """Export prompts to a JSON file."""
    service = PromptService()

    if category:
        prompts = service.search_prompts(category=PromptCategory(category))
    else:
        prompts = None  # Export all

    service.export_prompts(output_file, prompts)

    count = len(prompts) if prompts else "all"
    click.echo(f"✅ Exported {count} prompts to {output_file}")


@prompts_cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--sync-to-index", is_flag=True, help="Sync project prompts to central index")
@click.option("--sync-from-index", is_flag=True, help="Sync prompts from index to project")
@click.option("--project-name", help="Project name for sync-from-index")
def project(project_path: Path, sync_to_index: bool, sync_from_index: bool, project_name: str | None):
    """Manage prompts in a project directory."""
    from .project_storage import ProjectPromptStorage

    storage = ProjectPromptStorage()

    if sync_to_index:
        count = storage.sync_project_to_index(project_path)
        click.echo(f"✅ Synced {count} prompts from project to central index")

    elif sync_from_index:
        if not project_name:
            project_name = project_path.name
        count = storage.sync_index_to_project(project_name, project_path)
        click.echo(f"✅ Synced {count} prompts from index to project")

    else:
        # Show project prompts
        prompts = storage.load_from_project(project_path)
        if not prompts:
            click.echo(f"No prompts found in project {project_path.name}")
            return

        # TODO: Review unreachable code - click.echo(f"\n📁 Project: {project_path.name}")
        # TODO: Review unreachable code - click.echo(f"Found {len(prompts)} prompts")
        # TODO: Review unreachable code - click.echo("-" * 60)

        # TODO: Review unreachable code - for prompt in prompts[:10]:  # Show first 10
        # TODO: Review unreachable code - providers = ", ".join([p.value for p in prompt.providers[:2]])
        # TODO: Review unreachable code - click.echo(f"\n• {prompt.id[:8]}: {prompt.text[:60]}...")
        # TODO: Review unreachable code - click.echo(f"  Category: {prompt.category.value}, Providers: {providers}")
        # TODO: Review unreachable code - if prompt.tags:
        # TODO: Review unreachable code - click.echo(f"  Tags: {', '.join(prompt.tags[:5])}")


@prompts_cli.command()
@click.option("--base-paths", multiple=True, type=click.Path(exists=True, path_type=Path),
              help="Base paths to search for projects")
@click.option("--sync-all", is_flag=True, help="Sync all discovered prompts to index")
def discover(base_paths: list[Path], sync_all: bool):
    """Discover prompts in project directories."""
    from ..core.config import load_config
    from .project_storage import ProjectPromptStorage

    storage = ProjectPromptStorage()

    # Use configured project paths if not specified
    if not base_paths:
        config = load_config()
        if hasattr(config, 'storage') and hasattr(config.storage, 'project_paths'):
            base_paths = [Path(p) for p in config.storage.project_paths]
        else:
            click.echo("No base paths specified and none configured")
            return

    # TODO: Review unreachable code - # Discover prompts
    # TODO: Review unreachable code - project_prompts = storage.discover_project_prompts(list(base_paths))

    # TODO: Review unreachable code - if not project_prompts:
    # TODO: Review unreachable code - click.echo("No project prompts found")
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - total_prompts = sum(len(prompts) for prompts in project_prompts.values())
    # TODO: Review unreachable code - click.echo(f"\n🔍 Discovered {total_prompts} prompts across {len(project_prompts)} projects")
    # TODO: Review unreachable code - click.echo("=" * 60)

    # TODO: Review unreachable code - for project_name, prompts in project_prompts.items():
    # TODO: Review unreachable code - click.echo(f"\n📁 {project_name}: {len(prompts)} prompts")

    # TODO: Review unreachable code - # Group by category
    # TODO: Review unreachable code - by_category = {}
    # TODO: Review unreachable code - for prompt in prompts:
    # TODO: Review unreachable code - cat = prompt.category.value
    # TODO: Review unreachable code - if cat not in by_category:
    # TODO: Review unreachable code - by_category[cat] = 0
    # TODO: Review unreachable code - by_category[cat] += 1

    # TODO: Review unreachable code - for cat, count in by_category.items():
    # TODO: Review unreachable code - click.echo(f"  - {cat}: {count}")

    # TODO: Review unreachable code - if sync_all:
    # TODO: Review unreachable code - click.echo("\n🔄 Syncing all discovered prompts to index...")
    # TODO: Review unreachable code - total_synced = 0
    # TODO: Review unreachable code - for base_path in base_paths:
    # TODO: Review unreachable code - for project_dir in base_path.iterdir():
    # TODO: Review unreachable code - if project_dir.is_dir() and project_dir.name in project_prompts:
    # TODO: Review unreachable code - synced = storage.sync_project_to_index(project_dir)
    # TODO: Review unreachable code - total_synced += synced

    # TODO: Review unreachable code - click.echo(f"✅ Synced {total_synced} prompts to central index")


@prompts_cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", type=click.Choice(["yaml", "json"]), default="yaml",
              help="Storage format for prompts")
def init(project_path: Path, format: str):
    """Initialize prompt storage in a project directory."""
    from .project_storage import ProjectPromptStorage

    storage = ProjectPromptStorage(format=format)
    storage.initialize_project_prompts(project_path)

    click.echo(f"✅ Initialized prompt storage in {project_path}")
    click.echo("📁 Created .alice/prompts/ directory structure")
    click.echo(f"📝 Format: {format.upper()}")
    click.echo("\nNext steps:")
    click.echo("1. Check out .alice/prompts/templates/example.yaml for format reference")
    click.echo(f"2. Add prompts: alice prompts add -t 'your prompt' -c image_generation -p midjourney --project {project_path.name}")
    click.echo(f"3. View prompts: alice prompts project {project_path}")


@prompts_cli.command()
@click.option("--list", "list_templates", is_flag=True, help="List available templates")
@click.option("--show", help="Show template details")
@click.option("--render", help="Render a template")
@click.option("--save", help="Save rendered prompt")
@click.option("--create", help="Create new template")
@click.option("--from-prompt", help="Create template from existing prompt")
def template(list_templates: bool, show: str | None, render: str | None,
            save: str | None, create: str | None, from_prompt: str | None, **kwargs):
    """Work with prompt templates."""
    from .models import PromptCategory, ProviderType
    from .templates import PromptTemplate, TemplateManager

    manager = TemplateManager()

    if list_templates:
        templates = manager.list_templates()
        if not templates:
            click.echo("No templates found")
            return

        # TODO: Review unreachable code - click.echo("\n📋 Available Templates:")
        # TODO: Review unreachable code - click.echo("=" * 40)
        # TODO: Review unreachable code - for name in templates:
        # TODO: Review unreachable code - template = manager.get_template(name)
        # TODO: Review unreachable code - if template:
        # TODO: Review unreachable code - click.echo(f"\n• {name}")
        # TODO: Review unreachable code - click.echo(f"  Category: {template.category.value}")
        # TODO: Review unreachable code - click.echo(f"  Providers: {', '.join([p.value for p in template.providers])}")
        # TODO: Review unreachable code - if template.variables:
        # TODO: Review unreachable code - click.echo(f"  Variables: {', '.join(template.variables.keys())}")

    elif show:
        template = manager.get_template(show)
        if not template:
            click.echo(f"Template '{show}' not found")
            return

        # TODO: Review unreachable code - click.echo(f"\n📋 Template: {template.name}")
        # TODO: Review unreachable code - click.echo("=" * 60)
        # TODO: Review unreachable code - click.echo(f"Template: {template.template_text}")
        # TODO: Review unreachable code - click.echo(f"Category: {template.category.value}")
        # TODO: Review unreachable code - click.echo(f"Providers: {', '.join([p.value for p in template.providers])}")

        # TODO: Review unreachable code - if template.variables:
        # TODO: Review unreachable code - click.echo("\nVariables:")
        # TODO: Review unreachable code - for var, desc in template.variables.items():
        # TODO: Review unreachable code - default = ""
        # TODO: Review unreachable code - if template.default_values and var in template.default_values:
        # TODO: Review unreachable code - default = f" (default: {template.default_values[var]})"
        # TODO: Review unreachable code - click.echo(f"  - {var}: {desc}{default}")

        # TODO: Review unreachable code - if template.examples:
        # TODO: Review unreachable code - click.echo("\nExamples:")
        # TODO: Review unreachable code - for i, example in enumerate(template.examples, 1):
        # TODO: Review unreachable code - click.echo(f"\n  Example {i}:")
        # TODO: Review unreachable code - if example is not None and "variables" in example:
        # TODO: Review unreachable code - for var, val in example["variables"].items():
        # TODO: Review unreachable code - click.echo(f"    {var}: {val}")
        # TODO: Review unreachable code - if example is not None and "result" in example:
        # TODO: Review unreachable code - click.echo(f"    → {example['result']}")

    elif render:
        template = manager.get_template(render)
        if not template:
            click.echo(f"Template '{render}' not found")
            return

        # TODO: Review unreachable code - # Collect variable values
        # TODO: Review unreachable code - values = {}
        # TODO: Review unreachable code - click.echo(f"\nRendering template: {render}")
        # TODO: Review unreachable code - click.echo("Enter variable values (press Enter for defaults):\n")

        # TODO: Review unreachable code - for var, desc in template.variables.items():
        # TODO: Review unreachable code - default = ""
        # TODO: Review unreachable code - if template.default_values and var in template.default_values:
        # TODO: Review unreachable code - default = template.default_values[var]
        # TODO: Review unreachable code - prompt_text = f"{var} ({desc}) [{default}]: "
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - prompt_text = f"{var} ({desc}): "

        # TODO: Review unreachable code - value = click.prompt(prompt_text, default=default, show_default=False)
        # TODO: Review unreachable code - values[var] = value

        # TODO: Review unreachable code - # Render
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - rendered = template.render(**values)
        # TODO: Review unreachable code - click.echo("\n✅ Rendered prompt:")
        # TODO: Review unreachable code - click.echo("-" * 60)
        # TODO: Review unreachable code - click.echo(rendered)
        # TODO: Review unreachable code - click.echo("-" * 60)

        # TODO: Review unreachable code - # Optionally save
        # TODO: Review unreachable code - if save or click.confirm("\nSave this prompt?"):
        # TODO: Review unreachable code - service = PromptService()
        # TODO: Review unreachable code - prompt = template.to_prompt(**values)

        # TODO: Review unreachable code - # Additional metadata
        # TODO: Review unreachable code - if project := click.prompt("Project name", default=""):
        # TODO: Review unreachable code - prompt.project = project
        # TODO: Review unreachable code - if tags := click.prompt("Additional tags (comma-separated)", default=""):
        # TODO: Review unreachable code - prompt.tags.extend([t.strip() for t in tags.split(",")])

        # TODO: Review unreachable code - service.db.add_prompt(prompt)
        # TODO: Review unreachable code - click.echo(f"✅ Saved as prompt {prompt.id}")

        # TODO: Review unreachable code - except ValueError as e:
        # TODO: Review unreachable code - click.echo(f"❌ Error: {e}")

    elif create:
        # Interactive template creation
        click.echo(f"\n📝 Creating new template: {create}")

        template_text = click.prompt("Template text (use {var} for variables)")
        category = click.prompt("Category", type=click.Choice([c.value for c in PromptCategory]))

        # Extract variables
        import re
        var_names = re.findall(r'\{(\w+)\}', template_text)

        variables = {}
        if var_names:
            click.echo(f"\nFound variables: {', '.join(var_names)}")
            for var in var_names:
                desc = click.prompt(f"Description for '{var}'")
                variables[var] = desc

        # Providers
        [p.value for p in ProviderType]
        providers_str = click.prompt("Providers (comma-separated)",
                                   default="midjourney,flux")
        providers = [ProviderType(p.strip()) for p in providers_str.split(",")]

        # Create template
        template = PromptTemplate(
            name=create,
            template_text=template_text,
            category=PromptCategory(category),
            providers=providers,
            variables=variables
        )

        # Save
        path = manager.save_template(template)
        click.echo(f"✅ Created template: {path}")

    elif from_prompt:
        # Create template from existing prompt
        service = PromptService()

        # Find prompt
        if len(from_prompt) < 36:
            results = service.search_prompts()
            matches = [p for p in results if p.id.startswith(from_prompt)]
            if not matches:
                click.echo(f"No prompt found starting with '{from_prompt}'")
                return
            # TODO: Review unreachable code - prompt = matches[0]
        else:
            prompt = service.get_prompt(from_prompt)
            if not prompt:
                click.echo(f"Prompt not found: {from_prompt}")
                return

        # TODO: Review unreachable code - template_name = click.prompt("Template name")

        # TODO: Review unreachable code - # Auto-detect or ask for variables
        # TODO: Review unreachable code - import re
        # TODO: Review unreachable code - detected_vars = re.findall(r'\{(\w+)\}', prompt.text)

        # TODO: Review unreachable code - if detected_vars:
        # TODO: Review unreachable code - click.echo(f"Detected variables: {', '.join(detected_vars)}")
        # TODO: Review unreachable code - use_detected = click.confirm("Use these variables?", default=True)
        # TODO: Review unreachable code - if use_detected:
        # TODO: Review unreachable code - variables = detected_vars
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - var_str = click.prompt("Enter variable names (comma-separated)")
        # TODO: Review unreachable code - variables = [v.strip() for v in var_str.split(",")]
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - var_str = click.prompt("Enter variable names (comma-separated)", default="")
        # TODO: Review unreachable code - variables = [v.strip() for v in var_str.split(",")] if var_str else None

        # TODO: Review unreachable code - template = manager.create_from_prompt(prompt, template_name, variables)
        # TODO: Review unreachable code - path = manager.save_template(template)

        # TODO: Review unreachable code - click.echo(f"✅ Created template from prompt: {path}")
