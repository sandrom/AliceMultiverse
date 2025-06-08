"""CLI commands for plugin management."""

import asyncio
import click
import json
from pathlib import Path
from typing import Optional
import yaml

from .registry import PluginRegistry
from .config_manager import PluginConfigManager
from .templates import generate_plugin_template


@click.group()
def plugins():
    """Manage AliceMultiverse plugins."""
    pass


@plugins.command()
@click.option('--type', '-t', type=click.Choice(['all', 'provider', 'effect', 'analyzer', 'workflow']), 
              default='all', help='Filter by plugin type')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed plugin information')
def list(type: str, verbose: bool):
    """List all available plugins."""
    registry = PluginRegistry()
    asyncio.run(registry.initialize())
    
    plugins = registry.plugins
    
    # Filter by type if specified
    if type != 'all':
        plugins = {
            name: plugin for name, plugin in plugins.items()
            if plugin.metadata.type.value == type
        }
    
    if not plugins:
        click.echo(f"No {type} plugins found.")
        return
    
    # Group by type
    by_type = {}
    for name, plugin in plugins.items():
        plugin_type = plugin.metadata.type.value
        if plugin_type not in by_type:
            by_type[plugin_type] = []
        by_type[plugin_type].append((name, plugin))
    
    # Display plugins
    for plugin_type, type_plugins in sorted(by_type.items()):
        click.echo(f"\n{plugin_type.upper()} PLUGINS:")
        click.echo("-" * 40)
        
        for name, plugin in sorted(type_plugins):
            meta = plugin.metadata
            click.echo(f"  {name} (v{meta.version})")
            
            if verbose:
                click.echo(f"    Description: {meta.description}")
                if meta.author:
                    click.echo(f"    Author: {meta.author}")
                if meta.dependencies:
                    click.echo(f"    Dependencies: {', '.join(meta.dependencies)}")
                click.echo()


@plugins.command()
@click.argument('plugin_name')
def info(plugin_name: str):
    """Show detailed information about a plugin."""
    registry = PluginRegistry()
    asyncio.run(registry.initialize())
    
    plugin = registry.get_plugin(plugin_name)
    if not plugin:
        click.echo(f"Plugin '{plugin_name}' not found.", err=True)
        return
    
    meta = plugin.metadata
    
    click.echo(f"\nPlugin: {meta.name}")
    click.echo("=" * 50)
    click.echo(f"Version: {meta.version}")
    click.echo(f"Type: {meta.type.value}")
    click.echo(f"Description: {meta.description}")
    
    if meta.author:
        click.echo(f"Author: {meta.author}")
    
    if meta.email:
        click.echo(f"Email: {meta.email}")
    
    if meta.url:
        click.echo(f"URL: {meta.url}")
    
    if meta.dependencies:
        click.echo(f"\nDependencies:")
        for dep in meta.dependencies:
            click.echo(f"  - {dep}")
    
    if meta.config_schema:
        click.echo(f"\nConfiguration Schema:")
        click.echo(yaml.dump(meta.config_schema, default_flow_style=False, indent=2))


@plugins.command()
@click.argument('plugin_path')
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
def load(plugin_path: str, config: Optional[str]):
    """Load a plugin from file or module."""
    registry = PluginRegistry()
    asyncio.run(registry.initialize())
    
    # Load configuration if provided
    plugin_config = {}
    if config:
        config_path = Path(config)
        if config_path.suffix == '.yaml':
            with open(config_path) as f:
                plugin_config = yaml.safe_load(f)
        else:
            with open(config_path) as f:
                plugin_config = json.load(f)
    
    # Load plugin
    try:
        plugin = registry.loader.load_plugin(plugin_path, plugin_config)
        if plugin:
            registry.register_plugin(plugin)
            click.echo(f"Successfully loaded plugin: {plugin.metadata.name}")
            
            # Save config if provided
            if plugin_config:
                config_manager = PluginConfigManager()
                config_manager.save_config(plugin.metadata.name, plugin_config)
        else:
            click.echo("Failed to load plugin.", err=True)
    except Exception as e:
        click.echo(f"Error loading plugin: {e}", err=True)


@plugins.command()
@click.argument('plugin_type', type=click.Choice(['provider', 'effect', 'analyzer', 'workflow']))
@click.argument('plugin_name')
@click.option('--output', '-o', type=click.Path(), help='Output directory')
def create(plugin_type: str, plugin_name: str, output: Optional[str]):
    """Create a new plugin template."""
    output_dir = Path(output) if output else Path.cwd()
    
    try:
        file_path = generate_plugin_template(plugin_type, plugin_name, output_dir)
        click.echo(f"Created plugin template: {file_path}")
        click.echo("\nNext steps:")
        click.echo(f"1. Edit {file_path} to implement your plugin")
        click.echo(f"2. Load the plugin: alice plugins load {file_path}")
        
    except Exception as e:
        click.echo(f"Error creating plugin: {e}", err=True)


@plugins.command()
@click.argument('plugin_name')
@click.option('--format', '-f', type=click.Choice(['yaml', 'json']), 
              default='yaml', help='Configuration format')
def config(plugin_name: str, format: str):
    """Show or edit plugin configuration."""
    config_manager = PluginConfigManager()
    registry = PluginRegistry()
    asyncio.run(registry.initialize())
    
    # Get plugin to access schema
    plugin = registry.get_plugin(plugin_name)
    if not plugin:
        click.echo(f"Plugin '{plugin_name}' not found.", err=True)
        return
    
    # Load existing config
    config = config_manager.load_config(plugin_name)
    
    if not config and plugin.metadata.config_schema:
        # Generate default config from schema
        config = config_manager.get_default_config(plugin.metadata.config_schema)
        click.echo("No configuration found. Generated defaults from schema:")
    
    # Display config
    if format == 'yaml':
        click.echo(yaml.dump(config, default_flow_style=False, indent=2))
    else:
        click.echo(json.dumps(config, indent=2))


@plugins.command()
@click.argument('plugin_name')
@click.argument('config_path', type=click.Path(exists=True))
def set_config(plugin_name: str, config_path: str):
    """Set configuration for a plugin."""
    config_manager = PluginConfigManager()
    registry = PluginRegistry()
    asyncio.run(registry.initialize())
    
    # Get plugin to validate against schema
    plugin = registry.get_plugin(plugin_name)
    if not plugin:
        click.echo(f"Plugin '{plugin_name}' not found.", err=True)
        return
    
    # Load config file
    path = Path(config_path)
    if path.suffix == '.yaml':
        with open(path) as f:
            config = yaml.safe_load(f)
    else:
        with open(path) as f:
            config = json.load(f)
    
    # Validate config
    if plugin.metadata.config_schema:
        if not config_manager.validate_config(config, plugin.metadata.config_schema):
            click.echo("Configuration validation failed.", err=True)
            return
    
    # Save config
    config_manager.save_config(plugin_name, config)
    click.echo(f"Configuration saved for plugin: {plugin_name}")


@plugins.command()
@click.argument('plugin_name')
@click.argument('image_paths', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), required=True, help='Output directory')
@click.option('--params', '-p', type=str, help='Parameters as JSON string')
def apply_effect(plugin_name: str, image_paths: tuple, output: str, params: Optional[str]):
    """Apply an effect plugin to images."""
    registry = PluginRegistry()
    asyncio.run(registry.initialize())
    
    plugin = registry.get_plugin(plugin_name)
    if not plugin:
        click.echo(f"Plugin '{plugin_name}' not found.", err=True)
        return
    
    if plugin.metadata.type.value != 'effect':
        click.echo(f"Plugin '{plugin_name}' is not an effect plugin.", err=True)
        return
    
    # Parse parameters
    parameters = {}
    if params:
        try:
            parameters = json.loads(params)
        except json.JSONDecodeError:
            click.echo("Invalid JSON parameters.", err=True)
            return
    
    # Apply effect to each image
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_images():
        for img_path in image_paths:
            try:
                input_path = Path(img_path)
                output_path = output_dir / f"{input_path.stem}_effect{input_path.suffix}"
                
                result = await plugin.apply(input_path, output_path, parameters)
                click.echo(f"Processed: {img_path} -> {result}")
                
            except Exception as e:
                click.echo(f"Error processing {img_path}: {e}", err=True)
    
    asyncio.run(process_images())


if __name__ == "__main__":
    plugins()