"""CLI command modules for AliceMultiverse."""

from .behavior import add_behavior_arguments
from .interface import add_interface_command
from .keys import add_keys_commands
from .mcp import add_mcp_command
from .metrics import add_metrics_command
from .migrate import add_migrate_commands
from .monitor import add_monitor_commands
from .organize import add_organize_arguments
from .output import add_output_arguments
from .plugins import add_plugins_commands
from .recreate import add_recreate_commands
from .setup import add_setup_command
from .storage import add_storage_commands
from .technical import add_technical_arguments
from .understanding import add_understanding_arguments

__all__ = [
    "add_keys_commands",
    "add_setup_command",
    "add_recreate_commands",
    "add_interface_command",
    "add_mcp_command",
    "add_metrics_command",
    "add_plugins_commands",
    "add_migrate_commands",
    "add_monitor_commands",
    "add_storage_commands",
    "add_organize_arguments",
    "add_understanding_arguments",
    "add_output_arguments",
    "add_behavior_arguments",
    "add_technical_arguments",
]
