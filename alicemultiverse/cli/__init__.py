"""Unified CLI module for AliceMultiverse.

This module consolidates all CLI commands into a single location.
The CLI is primarily for debugging - normal usage is through AI assistants.
"""

from .main import create_parser, main

__all__ = ["main", "create_parser"]