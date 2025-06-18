"""Configuration management commands for Alice CLI."""

import sys
import click
from pathlib import Path
import json
import yaml

from ..core.config import load_config
from ..core.config_validation import ConfigValidator, SmartConfigBuilder
from ..core.startup_validation import StartupValidator, run_interactive_setup


@click.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.option('--fix', is_flag=True, help='Attempt to fix issues automatically')
@click.option('--config-path', type=click.Path(exists=True), help='Path to configuration file')
def validate(fix: bool, config_path: str):
    """Validate current configuration."""
    validator = StartupValidator(Path(config_path) if config_path else None)
    
    if validator.validate_startup(auto_fix=fix):
        click.echo("\n✓ Configuration is valid and ready to use!")
    else:
        click.echo("\n✗ Configuration has issues that need to be fixed.")
        sys.exit(1)


@config.command()
@click.option('--config-path', type=click.Path(exists=True), help='Path to configuration file')
def show(config_path: str):
    """Show current configuration."""
    try:
        config = load_config(Path(config_path) if config_path else None)
        validator = StartupValidator()
        validator.show_config_summary(dict(config))
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@config.command()
@click.option('--use-case', type=click.Choice(['default', 'quick_scan', 'full_analysis', 'bulk_import']),
              default='default', help='Optimization use case')
@click.option('--output', type=click.Path(), help='Save optimized config to file')
def optimize(use_case: str, output: str):
    """Generate optimized configuration for your system."""
    builder = SmartConfigBuilder()
    
    # Load current config as base
    try:
        base_config = dict(load_config())
    except:
        base_config = {}
    
    # Build optimized config
    optimized = builder.build_config(base_config, use_case)
    
    # Show system info
    system = builder.validator.system_resources
    click.echo(f"\nSystem: {system.cpu_count} CPUs, {system.memory_mb}MB RAM")
    click.echo(f"Recommended profile: {optimized['performance']['profile']}")
    
    # Show optimized settings
    click.echo("\nOptimized settings:")
    perf = optimized['performance']
    click.echo(f"  Max workers: {perf['max_workers']}")
    click.echo(f"  Batch size: {perf['batch_size']}")
    if 'cache_size_mb' in perf:
        click.echo(f"  Cache size: {perf['cache_size_mb']}MB")
    
    # Save if requested
    if output:
        path = Path(output)
        if path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(optimized, f, indent=2)
        else:
            with open(path, 'w') as f:
                yaml.dump(optimized, f, default_flow_style=False)
        click.echo(f"\nSaved optimized configuration to: {output}")


@config.command()
def setup():
    """Interactive configuration setup wizard."""
    click.echo("Welcome to AliceMultiverse Configuration Setup!")
    click.echo("=" * 50)
    
    config = run_interactive_setup()
    
    # Validate the new configuration
    validator = ConfigValidator()
    result = validator.validate_config(config)
    
    if result.is_valid:
        click.echo("\n✓ Configuration is valid!")
        
        # Ask where to save
        save_path = click.prompt("\nSave configuration to", default="settings.yaml")
        
        path = Path(save_path)
        if path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
        else:
            with open(path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        
        click.echo(f"\nConfiguration saved to: {save_path}")
        click.echo("\nNext steps:")
        click.echo("1. Run 'alice keys setup' to configure API keys")
        click.echo("2. Run 'alice' to start organizing your media!")
    else:
        click.echo("\n✗ Configuration has issues:")
        for field, error in result.errors.items():
            click.echo(f"  - {field}: {error}")


@config.command()
def check():
    """Quick configuration check."""
    validator = ConfigValidator()
    
    # Check configuration
    try:
        config = load_config()
        config_dict = dict(config)
        
        # Basic validation
        result = validator.validate_config(config_dict)
        
        if result.is_valid:
            click.echo("✓ Configuration: Valid")
        else:
            click.echo("✗ Configuration: Invalid")
            for field, error in result.errors.items():
                click.echo(f"  - {field}: {error}")
        
        # Runtime check
        runtime_result = validator.validate_runtime_compatibility(config_dict)
        if runtime_result.warnings:
            click.echo("\n⚠ Runtime warnings:")
            for warning in runtime_result.warnings.values():
                click.echo(f"  - {warning}")
        
        # System resources
        system = validator.system_resources
        click.echo(f"\nSystem resources:")
        click.echo(f"  CPUs: {system.cpu_count}")
        click.echo(f"  Memory: {system.memory_mb}MB")
        click.echo(f"  Disk: {system.available_disk_mb}MB free")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}")
        sys.exit(1)


@config.command()
@click.argument('setting', type=str)
@click.argument('value', type=str)
def set(setting: str, value: str):
    """Set a configuration value."""
    try:
        # Load current config
        config_path = Path("settings.yaml")
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # Parse the setting path (e.g., "performance.max_workers")
        keys = setting.split('.')
        current = config
        
        # Navigate to the parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        final_key = keys[-1]
        
        # Try to parse the value
        try:
            # Try as number
            if '.' in value:
                current[final_key] = float(value)
            else:
                current[final_key] = int(value)
        except ValueError:
            # Try as boolean
            if value.lower() in ('true', 'yes', 'on'):
                current[final_key] = True
            elif value.lower() in ('false', 'no', 'off'):
                current[final_key] = False
            else:
                # Keep as string
                current[final_key] = value
        
        # Save back
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        click.echo(f"Set {setting} = {current[final_key]}")
        
        # Validate the change
        validator = ConfigValidator()
        result = validator.validate_config(config)
        if not result.is_valid:
            click.echo("\n⚠ Warning: Configuration now has errors:")
            for field, error in result.errors.items():
                click.echo(f"  - {field}: {error}")
        
    except Exception as e:
        click.echo(f"Error setting configuration: {e}", err=True)
        sys.exit(1)


@config.command()
@click.argument('setting', type=str)
def get(setting: str):
    """Get a configuration value."""
    try:
        config = load_config()
        
        # Navigate the config
        keys = setting.split('.')
        current = config
        
        for key in keys:
            if hasattr(current, key):
                current = getattr(current, key)
            elif isinstance(current, dict) and key in current:
                current = current[key]
            else:
                click.echo(f"Setting not found: {setting}")
                sys.exit(1)
        
        click.echo(f"{setting} = {current}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)