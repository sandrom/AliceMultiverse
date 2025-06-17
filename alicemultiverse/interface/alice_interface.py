"""Alice Interface - Compatibility layer for the refactored natural language interface."""

# Import the refactored interface from the natural module
from .natural import AliceInterface

# Export the interface for backward compatibility
__all__ = ["AliceInterface"]

# This file now serves as a compatibility layer that imports from the new modular structure.
# The actual implementation has been refactored into the natural/ subdirectory:
#
# natural/
# ├── __init__.py                # Package exports
# ├── base.py                    # Base class with common functionality
# ├── search_operations.py       # Search and similarity operations
# ├── content_operations.py      # Content generation operations
# ├── organization_operations.py # Organization, tagging, and grouping
# ├── project_operations.py      # Project management and asset info
# ├── similarity_operations.py   # Reserved for future similarity features
# └── interface.py               # Main interface combining all mixins
#
# The refactoring improves maintainability by:
# 1. Separating natural language processing from structured operations
# 2. Using mixins for better code organization
# 3. Making it easier to add new AI-friendly operations
# 4. Reducing the size of individual files
# 5. Improving testability of individual components
#
# The natural language interface differs from the structured interface in that:
# - It accepts more flexible, AI-friendly inputs
# - It includes natural language parsing (e.g., time references)
# - It simplifies responses for AI consumption
# - It handles errors with AI-friendly messages and suggestions
