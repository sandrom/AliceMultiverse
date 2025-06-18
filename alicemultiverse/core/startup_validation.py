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
        
        # Validate configuration
        result = self.validator.validate_config(config_dict)
        
        # Show results
        self._show_validation_results(result)
        
        # Handle errors
        if not result.is_valid:
            if auto_fix:
                return self._attempt_auto_fix(config_dict, result)
            else:
                self._show_fix_instructions(result)
                return False
        
        # Check runtime compatibility
        runtime_result = self.validator.validate_runtime_compatibility(config_dict)
        if runtime_result.warnings:
            self._show_runtime_warnings(runtime_result)
        
        return True
    
    def _show_validation_results(self, result: ValidationResult) -> None:
        """Display validation results."""
        if result.is_valid and not result.warnings:
            self.console.print("[green]✓ Configuration is valid[/green]")
            return
        
        # Show errors
        if result.errors:
            self.console.print("\n[red]Configuration Errors:[/red]")
            for field, error in result.errors.items():
                self.console.print(f"  [red]✗[/red] {field}: {error}")
        
        # Show warnings  
        if result.warnings:
            self.console.print("\n[yellow]Warnings:[/yellow]")
            for field, warning in result.warnings.items():
                self.console.print(f"  [yellow]![/yellow] {field}: {warning}")
        
        # Show recommendations
        if result.recommendations:
            self.console.print("\n[blue]Recommendations:[/blue]")
            for rec in result.recommendations:
                self.console.print(f"  [blue]→[/blue] {rec}")
    
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
            elif "permission" in error:
                fixes.append(f"Fix permissions: chmod 755 {error.split(': ')[1]}")
            elif "API key" in error.lower():
                fixes.append("Configure API keys: alice keys setup")
            elif "profile" in field:
                fixes.append("Set valid profile: default, fast, memory_constrained, or large_collection")
        
        return fixes
    
    def _attempt_auto_fix(self, config: Dict[str, Any], result: ValidationResult) -> bool:
        """Attempt to automatically fix configuration issues."""
        self.console.print("\n[yellow]Attempting automatic fixes...[/yellow]")
        
        fixed_any = False
        
        # Fix paths
        for field, error in result.errors.items():
            if field.startswith('paths.') and "does not exist" in error:
                path = Path(error.split(': ')[1])
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.console.print(f"  [green]✓[/green] Created directory: {path}")
                    fixed_any = True
                except Exception as e:
                    self.console.print(f"  [red]✗[/red] Could not create {path}: {e}")
        
        # Apply recommended settings
        if 'performance' in config:
            profile, settings = self.validator.recommend_performance_profile()
            config['performance'].update(settings)
            config['performance']['profile'] = profile
            self.console.print(f"  [green]✓[/green] Applied recommended profile: {profile}")
            fixed_any = True
        
        if fixed_any:
            # Re-validate
            new_result = self.validator.validate_config(config)
            if new_result.is_valid:
                self.console.print("\n[green]✓ All issues fixed![/green]")
                return True
            else:
                self.console.print("\n[yellow]Some issues remain:[/yellow]")
                self._show_validation_results(new_result)
        
        return False
    
    def show_config_summary(self, config: Dict[str, Any]) -> None:
        """Show configuration summary."""
        table = Table(title="Configuration Summary")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        # Paths
        paths = config.get('paths', {})
        table.add_row("Inbox", str(paths.get('inbox', 'Not set')))
        table.add_row("Organized", str(paths.get('organized', 'Not set')))
        
        # Performance
        perf = config.get('performance', {})
        table.add_row("Performance Profile", perf.get('profile', 'default'))
        table.add_row("Max Workers", str(perf.get('max_workers', 8)))
        table.add_row("Batch Size", str(perf.get('batch_size', 100)))
        
        # Features
        understanding = config.get('understanding', {})
        table.add_row("Understanding", "Enabled" if understanding.get('enabled') else "Disabled")
        
        self.console.print(table)
    
    def interactive_setup(self) -> Dict[str, Any]:
        """Interactive configuration setup."""
        self.console.print("\n[bold]Interactive Configuration Setup[/bold]")
        
        config = {}
        
        # Get paths
        self.console.print("\n[cyan]1. Directory Configuration[/cyan]")
        
        inbox = self.console.input("Inbox directory (where AI images are): ")
        config['paths'] = {'inbox': inbox}
        
        organized = self.console.input("Organized directory (where to put organized files): ")
        config['paths']['organized'] = organized
        
        # Get performance preference
        self.console.print("\n[cyan]2. Performance Configuration[/cyan]")
        
        # Show system info
        sys_res = self.validator.system_resources
        self.console.print(f"Your system: {sys_res.cpu_count} CPUs, {sys_res.memory_mb}MB RAM")
        
        profile, settings = self.validator.recommend_performance_profile()
        self.console.print(f"Recommended profile: [green]{profile}[/green]")
        
        use_recommended = self.console.input("Use recommended settings? [Y/n]: ")
        if use_recommended.lower() != 'n':
            config['performance'] = settings
            config['performance']['profile'] = profile
        
        # Understanding
        self.console.print("\n[cyan]3. AI Understanding[/cyan]")
        enable_understanding = self.console.input("Enable AI understanding? [y/N]: ")
        if enable_understanding.lower() == 'y':
            config['understanding'] = {'enabled': True}
            self.console.print("Remember to run 'alice keys setup' to configure API keys")
        
        return config


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
    
    # Show summary if requested
    if show_summary:
        try:
            config = load_config(config_path)
            validator.show_config_summary(dict(config))
        except Exception:
            pass
    
    return True


def run_interactive_setup() -> Dict[str, Any]:
    """Run interactive configuration setup."""
    validator = StartupValidator()
    return validator.interactive_setup()


def check_api_keys() -> ValidationResult:
    """Check API key configuration."""
    result = ValidationResult(is_valid=True)
    
    # Check environment variables
    providers = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY', 
        'google': 'GOOGLE_AI_API_KEY'
    }
    
    found_keys = []
    for provider, env_var in providers.items():
        if os.environ.get(env_var):
            found_keys.append(provider)
    
    if not found_keys:
        result.add_warning(
            'api_keys',
            "No API keys found in environment. Run 'alice keys setup' to configure."
        )
    else:
        result.add_recommendation(
            f"Found API keys for: {', '.join(found_keys)}"
        )
    
    return result