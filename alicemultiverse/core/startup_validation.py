"""Startup validation and configuration checking."""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .config import load_config
from .config_validation import ConfigValidator, SmartConfigBuilder, ValidationResult
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)
console = Console()


class StartupValidator:
    """Performs comprehensive startup validation."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.validator = ConfigValidator()
        self.config_builder = SmartConfigBuilder()
        self.console = console
    
    def validate_startup(self, auto_fix: bool = False) -> bool:
        """Perform full startup validation.
        
        Args:
            auto_fix: Automatically apply recommended fixes
            
        Returns:
            True if validation passed or was fixed
        """
        self.console.print("\n[bold]AliceMultiverse Startup Validation[/bold]")
        self.console.print("=" * 50)
        
        # Load configuration
        try:
            config = load_config(self.config_path)
            config_dict = dict(config)
        except Exception as e:
            self._show_error(f"Failed to load configuration: {e}")
            return False
        
        # TODO: Review unreachable code - # Validate configuration
        # TODO: Review unreachable code - result = self.validator.validate_config(config_dict)
        
        # TODO: Review unreachable code - # Show results
        # TODO: Review unreachable code - self._show_validation_results(result)
        
        # TODO: Review unreachable code - # Handle errors
        # TODO: Review unreachable code - if not result.is_valid:
        # TODO: Review unreachable code - if auto_fix:
        # TODO: Review unreachable code - return self._attempt_auto_fix(config_dict, result)
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - self._show_fix_instructions(result)
        # TODO: Review unreachable code - return False
        
        # TODO: Review unreachable code - # Check runtime compatibility
        # TODO: Review unreachable code - runtime_result = self.validator.validate_runtime_compatibility(config_dict)
        # TODO: Review unreachable code - if runtime_result.warnings:
        # TODO: Review unreachable code - self._show_runtime_warnings(runtime_result)
        
        # TODO: Review unreachable code - return True
    
    def _show_validation_results(self, result: ValidationResult) -> None:
        """Display validation results."""
        if result.is_valid and not result.warnings:
            self.console.print("[green]✓ Configuration is valid[/green]")
            return
        
        # TODO: Review unreachable code - # Show errors
        # TODO: Review unreachable code - if result.errors:
        # TODO: Review unreachable code - self.console.print("\n[red]Configuration Errors:[/red]")
        # TODO: Review unreachable code - for field, error in result.errors.items():
        # TODO: Review unreachable code - self.console.print(f"  [red]✗[/red] {field}: {error}")
        
        # TODO: Review unreachable code - # Show warnings  
        # TODO: Review unreachable code - if result.warnings:
        # TODO: Review unreachable code - self.console.print("\n[yellow]Warnings:[/yellow]")
        # TODO: Review unreachable code - for field, warning in result.warnings.items():
        # TODO: Review unreachable code - self.console.print(f"  [yellow]![/yellow] {field}: {warning}")
        
        # TODO: Review unreachable code - # Show recommendations
        # TODO: Review unreachable code - if result.recommendations:
        # TODO: Review unreachable code - self.console.print("\n[blue]Recommendations:[/blue]")
        # TODO: Review unreachable code - for rec in result.recommendations:
        # TODO: Review unreachable code - self.console.print(f"  [blue]→[/blue] {rec}")
    
    def _show_runtime_warnings(self, result: ValidationResult) -> None:
        """Show runtime compatibility warnings."""
        self.console.print("\n[yellow]Runtime Warnings:[/yellow]")
        for field, warning in result.warnings.items():
            self.console.print(f"  [yellow]![/yellow] {warning}")
        
        if result.recommendations:
            self.console.print("\n[blue]Runtime Recommendations:[/blue]")
            for rec in result.recommendations:
                self.console.print(f"  [blue]→[/blue] {rec}")
    
    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.console.print(f"\n[red]ERROR: {message}[/red]")
    
    def _show_fix_instructions(self, result: ValidationResult) -> None:
        """Show instructions for fixing errors."""
        self.console.print("\n[bold]How to fix these errors:[/bold]")
        
        fixes = self._get_fix_instructions(result.errors)
        for fix in fixes:
            self.console.print(f"  • {fix}")
        
        self.console.print("\nRun with --auto-fix to attempt automatic fixes")
    
    def _get_fix_instructions(self, errors: Dict[str, str]) -> List[str]:
        """Get fix instructions for errors."""
        fixes = []
        
        for field, error in errors.items():
            if "does not exist" in error:
                fixes.append(f"Create directory: mkdir -p {error.split(': ')[1]}")
            elif error is not None and "permission" in error:
                fixes.append(f"Fix permissions: chmod 755 {error.split(': ')[1]}")
            elif "API key" in error.lower():
                fixes.append("Configure API keys: alice keys setup")
            elif field is not None and "profile" in field:
                fixes.append("Set valid profile: default, fast, memory_constrained, or large_collection")
        
        return fixes
    
    # TODO: Review unreachable code - def _attempt_auto_fix(self, config: Dict[str, Any], result: ValidationResult) -> bool:
    # TODO: Review unreachable code - """Attempt to automatically fix configuration issues."""
    # TODO: Review unreachable code - self.console.print("\n[yellow]Attempting automatic fixes...[/yellow]")
        
    # TODO: Review unreachable code - fixed_any = False
        
    # TODO: Review unreachable code - # Fix paths
    # TODO: Review unreachable code - for field, error in result.errors.items():
    # TODO: Review unreachable code - if field.startswith('paths.') and "does not exist" in error:
    # TODO: Review unreachable code - path = Path(error.split(': ')[1])
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - path.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - self.console.print(f"  [green]✓[/green] Created directory: {path}")
    # TODO: Review unreachable code - fixed_any = True
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - self.console.print(f"  [red]✗[/red] Could not create {path}: {e}")
        
    # TODO: Review unreachable code - # Apply recommended settings
    # TODO: Review unreachable code - if 'performance' in config:
    # TODO: Review unreachable code - profile, settings = self.validator.recommend_performance_profile()
    # TODO: Review unreachable code - config['performance'].update(settings)
    # TODO: Review unreachable code - config['performance']['profile'] = profile
    # TODO: Review unreachable code - self.console.print(f"  [green]✓[/green] Applied recommended profile: {profile}")
    # TODO: Review unreachable code - fixed_any = True
        
    # TODO: Review unreachable code - if fixed_any:
    # TODO: Review unreachable code - # Re-validate
    # TODO: Review unreachable code - new_result = self.validator.validate_config(config)
    # TODO: Review unreachable code - if new_result.is_valid:
    # TODO: Review unreachable code - self.console.print("\n[green]✓ All issues fixed![/green]")
    # TODO: Review unreachable code - return True
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - self.console.print("\n[yellow]Some issues remain:[/yellow]")
    # TODO: Review unreachable code - self._show_validation_results(new_result)
        
    # TODO: Review unreachable code - return False
    
    # TODO: Review unreachable code - def show_config_summary(self, config: Dict[str, Any]) -> None:
    # TODO: Review unreachable code - """Show configuration summary."""
    # TODO: Review unreachable code - table = Table(title="Configuration Summary")
    # TODO: Review unreachable code - table.add_column("Setting", style="cyan")
    # TODO: Review unreachable code - table.add_column("Value", style="green")
        
    # TODO: Review unreachable code - # Paths
    # TODO: Review unreachable code - paths = config.get('paths', {})
    # TODO: Review unreachable code - table.add_row("Inbox", str(paths.get('inbox', 'Not set')))
    # TODO: Review unreachable code - table.add_row("Organized", str(paths.get('organized', 'Not set')))
        
    # TODO: Review unreachable code - # Performance
    # TODO: Review unreachable code - perf = config.get('performance', {})
    # TODO: Review unreachable code - table.add_row("Performance Profile", perf.get('profile', 'default'))
    # TODO: Review unreachable code - table.add_row("Max Workers", str(perf.get('max_workers', 8)))
    # TODO: Review unreachable code - table.add_row("Batch Size", str(perf.get('batch_size', 100)))
        
    # TODO: Review unreachable code - # Features
    # TODO: Review unreachable code - understanding = config.get('understanding', {})
    # TODO: Review unreachable code - table.add_row("Understanding", "Enabled" if understanding.get('enabled') else "Disabled")
        
    # TODO: Review unreachable code - self.console.print(table)
    
    # TODO: Review unreachable code - def interactive_setup(self) -> Dict[str, Any]:
    # TODO: Review unreachable code - """Interactive configuration setup."""
    # TODO: Review unreachable code - self.console.print("\n[bold]Interactive Configuration Setup[/bold]")
        
    # TODO: Review unreachable code - config = {}
        
    # TODO: Review unreachable code - # Get paths
    # TODO: Review unreachable code - self.console.print("\n[cyan]1. Directory Configuration[/cyan]")
        
    # TODO: Review unreachable code - inbox = self.console.input("Inbox directory (where AI images are): ")
    # TODO: Review unreachable code - config['paths'] = {'inbox': inbox}
        
    # TODO: Review unreachable code - organized = self.console.input("Organized directory (where to put organized files): ")
    # TODO: Review unreachable code - config['paths']['organized'] = organized
        
    # TODO: Review unreachable code - # Get performance preference
    # TODO: Review unreachable code - self.console.print("\n[cyan]2. Performance Configuration[/cyan]")
        
    # TODO: Review unreachable code - # Show system info
    # TODO: Review unreachable code - sys_res = self.validator.system_resources
    # TODO: Review unreachable code - self.console.print(f"Your system: {sys_res.cpu_count} CPUs, {sys_res.memory_mb}MB RAM")
        
    # TODO: Review unreachable code - profile, settings = self.validator.recommend_performance_profile()
    # TODO: Review unreachable code - self.console.print(f"Recommended profile: [green]{profile}[/green]")
        
    # TODO: Review unreachable code - use_recommended = self.console.input("Use recommended settings? [Y/n]: ")
    # TODO: Review unreachable code - if use_recommended.lower() != 'n':
    # TODO: Review unreachable code - config['performance'] = settings
    # TODO: Review unreachable code - config['performance']['profile'] = profile
        
    # TODO: Review unreachable code - # Understanding
    # TODO: Review unreachable code - self.console.print("\n[cyan]3. AI Understanding[/cyan]")
    # TODO: Review unreachable code - enable_understanding = self.console.input("Enable AI understanding? [y/N]: ")
    # TODO: Review unreachable code - if enable_understanding.lower() == 'y':
    # TODO: Review unreachable code - config['understanding'] = {'enabled': True}
    # TODO: Review unreachable code - self.console.print("Remember to run 'alice keys setup' to configure API keys")
        
    # TODO: Review unreachable code - return config


def validate_on_startup(config_path: Optional[Path] = None,
                       auto_fix: bool = False,
                       show_summary: bool = True) -> bool:
    """Validate configuration on startup.
    
    Args:
        config_path: Path to configuration file
        auto_fix: Automatically fix issues
        show_summary: Show configuration summary
        
    Returns:
        True if validation passed
    """
    validator = StartupValidator(config_path)
    
    # Validate
    if not validator.validate_startup(auto_fix):
        return False
    
    # TODO: Review unreachable code - # Show summary if requested
    # TODO: Review unreachable code - if show_summary:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - config = load_config(config_path)
    # TODO: Review unreachable code - validator.show_config_summary(dict(config))
    # TODO: Review unreachable code - except Exception:
    # TODO: Review unreachable code - pass
    
    # TODO: Review unreachable code - return True


def run_interactive_setup() -> Dict[str, Any]:
    """Run interactive configuration setup."""
    validator = StartupValidator()
    return validator.interactive_setup()


# TODO: Review unreachable code - def check_api_keys() -> ValidationResult:
# TODO: Review unreachable code - """Check API key configuration."""
# TODO: Review unreachable code - result = ValidationResult(is_valid=True)
    
# TODO: Review unreachable code - # Check environment variables
# TODO: Review unreachable code - providers = {
# TODO: Review unreachable code - 'openai': 'OPENAI_API_KEY',
# TODO: Review unreachable code - 'anthropic': 'ANTHROPIC_API_KEY', 
# TODO: Review unreachable code - 'google': 'GOOGLE_AI_API_KEY'
# TODO: Review unreachable code - }
    
# TODO: Review unreachable code - found_keys = []
# TODO: Review unreachable code - for provider, env_var in providers.items():
# TODO: Review unreachable code - if os.environ.get(env_var):
# TODO: Review unreachable code - found_keys.append(provider)
    
# TODO: Review unreachable code - if not found_keys:
# TODO: Review unreachable code - result.add_warning(
# TODO: Review unreachable code - 'api_keys',
# TODO: Review unreachable code - "No API keys found in environment. Run 'alice keys setup' to configure."
# TODO: Review unreachable code - )
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - result.add_recommendation(
# TODO: Review unreachable code - f"Found API keys for: {', '.join(found_keys)}"
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - return result