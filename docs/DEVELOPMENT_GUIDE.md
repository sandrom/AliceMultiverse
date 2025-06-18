# Development Guide

This guide covers development practices and patterns used in AliceMultiverse.

## Architecture Overview

AliceMultiverse uses a mixin-based architecture with Protocol interfaces for type safety:

```python
from alicemultiverse.core.protocols import HasConfig, HasStats

class MyComponent(ConfigMixin, StatsMixin):
    """Component using mixins for functionality."""
    pass
```

## Protocol Interfaces

Protocol interfaces define the expected attributes for type checking without inheritance:

### Available Protocols

```python
# Core protocols
HasConfig      # Components with configuration
HasStats       # Components tracking statistics
HasSearchDB    # Components with search database
HasOrganizer   # Components with organizer instance

# Service protocols  
HasMetadataCache        # Metadata caching
HasSelectionService     # Asset selection
HasProjectService       # Project management
HasUnderstandingProvider # AI understanding
```

### Using Protocols

```python
from typing import TYPE_CHECKING
from alicemultiverse.core.protocols import HasConfig, HasStats

def process_with_config(component: HasConfig) -> None:
    """Function requiring a component with config."""
    if component.config.debug:
        print("Debug mode enabled")

def update_statistics(component: HasStats) -> None:
    """Function requiring statistics tracking."""
    component.stats["processed"] += 1
```

### Multiple Protocols

```python
# Python 3.10+ syntax
def complex_operation(obj: HasConfig & HasStats) -> None:
    """Requires both config and stats."""
    if obj.config.verbose:
        print(f"Processed: {obj.stats['total']}")

# Python 3.9 syntax
from typing import Protocol

class ConfigAndStats(HasConfig, HasStats, Protocol):
    """Combined protocol."""
    pass

def complex_operation(obj: ConfigAndStats) -> None:
    """Requires both config and stats."""
    pass
```

## Mixin Architecture

### Creating Mixins

```python
class CacheMixin:
    """Mixin providing caching functionality."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}
    
    def get_cached(self, key: str) -> Any:
        """Get value from cache."""
        return self._cache.get(key)
    
    def set_cached(self, key: str, value: Any) -> None:
        """Store value in cache."""
        self._cache[key] = value
```

### Type-Safe Mixins

Use TYPE_CHECKING to avoid circular imports:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alicemultiverse.core.protocols import HasConfig

class ConfigurableMixin:
    """Mixin for configurable components."""
    
    if TYPE_CHECKING:
        # Type hints for mypy
        config: Config
    
    def load_config(self, path: str) -> None:
        """Load configuration from file."""
        # Implementation
```

## Performance Optimization

### Parallel Processing

Use the ParallelProcessor for CPU-bound operations:

```python
from alicemultiverse.organizer.parallel_processor import ParallelProcessor

processor = ParallelProcessor(max_workers=8)

# Process files in parallel
results = processor.process_files_parallel(
    file_paths,
    process_function,
    batch_size=100
)
```

### Batch Operations

Use BatchOperationsMixin for database operations:

```python
from alicemultiverse.storage.batch_operations import BatchOperationsMixin

class MyStorage(BatchOperationsMixin):
    def process_many(self, items):
        # Batch insert for performance
        self.batch_upsert_assets(items)
```

### Performance Profiles

Configure performance based on use case:

```python
from alicemultiverse.core.performance_config import get_performance_config

# Get profile-based config
config = get_performance_config("fast")

# Or create custom config
config = PerformanceConfig(
    max_workers=16,
    batch_size=200,
    enable_batch_operations=True
)
```

## Error Handling

### Structured Logging

Use structured logging for better debugging:

```python
from alicemultiverse.core.structured_logging import get_logger

logger = get_logger(__name__)

logger.info("Processing file", extra={
    "file_path": str(path),
    "size": path.stat().st_size,
    "operation": "organize"
})
```

### Error Recovery

Implement graceful error recovery:

```python
def process_with_recovery(self, items):
    """Process items with error recovery."""
    failed = []
    
    for item in items:
        try:
            self._process_item(item)
        except Exception as e:
            logger.error(f"Failed to process {item}: {e}")
            failed.append(item)
    
    if failed:
        # Retry failed items with different strategy
        self._process_failed_items(failed)
```

## Testing

### Writing Tests

Use pytest for testing:

```python
import pytest
from unittest.mock import MagicMock

class TestMyComponent:
    @pytest.fixture
    def component(self):
        """Create test component."""
        return MyComponent()
    
    def test_basic_functionality(self, component):
        """Test basic operations."""
        result = component.process("test")
        assert result["status"] == "success"
```

### Mocking Protocols

```python
def test_with_protocol():
    """Test component with protocol."""
    mock_component = MagicMock()
    mock_component.config = MagicMock()
    mock_component.stats = {"total": 0}
    
    # Now satisfies HasConfig & HasStats
    process_component(mock_component)
```

## Best Practices

### 1. Type Annotations

Always use type annotations:

```python
from pathlib import Path
from typing import List, Optional, Dict, Any

def organize_files(
    paths: List[Path],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """Organize files with options."""
    # Implementation
```

### 2. Docstrings

Use descriptive docstrings:

```python
def complex_operation(
    data: List[Dict[str, Any]],
    mode: str = "fast"
) -> Dict[str, Any]:
    """Perform complex operation on data.
    
    Args:
        data: List of data dictionaries to process
        mode: Processing mode ('fast', 'accurate', 'balanced')
        
    Returns:
        Dictionary with results and statistics
        
    Raises:
        ValueError: If mode is not recognized
        ProcessingError: If operation fails
    """
```

### 3. Configuration

Use dataclasses for configuration:

```python
from dataclasses import dataclass

@dataclass
class ProcessingConfig:
    """Configuration for processing."""
    max_retries: int = 3
    timeout: float = 30.0
    verbose: bool = False
```

### 4. Constants

Define constants in appropriate modules:

```python
# In alicemultiverse/core/constants.py
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi"}

DEFAULT_BATCH_SIZE = 100
MAX_PARALLEL_WORKERS = 16
```

## Adding New Features

### 1. Create Protocol (if needed)

```python
# In alicemultiverse/core/protocols.py
class HasNewFeature(Protocol):
    """Protocol for new feature."""
    feature_manager: Any
```

### 2. Implement Mixin

```python
# In alicemultiverse/features/new_feature.py
class NewFeatureMixin:
    """Mixin providing new feature."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_manager = FeatureManager()
```

### 3. Add Tests

```python
# In tests/unit/test_new_feature.py
class TestNewFeature:
    def test_feature_functionality(self):
        """Test new feature works correctly."""
        # Test implementation
```

### 4. Update Documentation

- Add to this guide if it's a development pattern
- Add to user documentation if it's a user-facing feature
- Update CHANGELOG.md with the changes

## Debugging Tips

### 1. Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Use Type Checking

```bash
# Run mypy for type checking
mypy alicemultiverse/

# Run with specific module
mypy alicemultiverse/organizer/
```

### 3. Performance Profiling

```python
import cProfile
import pstats

def profile_operation():
    """Profile performance-critical operation."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Operation to profile
    expensive_operation()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

## Common Patterns

### Lazy Loading

```python
class LazyComponent:
    """Component with lazy initialization."""
    
    def __init__(self):
        self._expensive_resource = None
    
    @property
    def expensive_resource(self):
        """Lazy load expensive resource."""
        if self._expensive_resource is None:
            self._expensive_resource = self._load_resource()
        return self._expensive_resource
```

### Context Managers

```python
from contextlib import contextmanager

@contextmanager
def temporary_config(component, **kwargs):
    """Temporarily modify configuration."""
    original = {}
    
    # Save original values
    for key, value in kwargs.items():
        original[key] = getattr(component.config, key)
        setattr(component.config, key, value)
    
    try:
        yield component
    finally:
        # Restore original values
        for key, value in original.items():
            setattr(component.config, key, value)
```

### Factory Pattern

```python
from typing import Type

class ComponentFactory:
    """Factory for creating components."""
    
    _registry = {}
    
    @classmethod
    def register(cls, name: str, component_class: Type):
        """Register component class."""
        cls._registry[name] = component_class
    
    @classmethod
    def create(cls, name: str, **kwargs):
        """Create component by name."""
        if name not in cls._registry:
            raise ValueError(f"Unknown component: {name}")
        
        return cls._registry[name](**kwargs)
```