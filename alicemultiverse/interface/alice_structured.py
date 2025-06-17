"""Alice Structured Interface - Compatibility layer for the refactored modular interface."""

# Import the refactored interface from the structured module
from .structured import AliceStructuredInterface

# Export the interface for backward compatibility
__all__ = ["AliceStructuredInterface"]

# This file now serves as a compatibility layer that imports from the new modular structure.
# The actual implementation has been refactored into the structured/ subdirectory:
#
# structured/
# ├── __init__.py               # Package exports
# ├── base.py                   # Base class with common functionality
# ├── asset_operations.py       # Asset-related operations
# ├── organization_operations.py # Organization and tagging operations
# ├── project_operations.py     # Project management operations
# ├── selection_operations.py   # Selection management operations
# ├── workflow_operations.py    # Workflow and generation operations
# └── interface.py              # Main interface combining all mixins
#
# The refactoring improves maintainability by:
# 1. Separating concerns into logical modules
# 2. Using mixins for better code organization
# 3. Making it easier to add new operations
# 4. Reducing the size of individual files
# 5. Improving testability of individual components