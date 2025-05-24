# Development Guide

## Project Structure

The AliceMultiverse codebase has been refactored into a modular, maintainable Python package:

```
alicemultiverse/
├── __init__.py              # Package initialization
├── version.py               # Version information
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── config.py            # Configuration management (OmegaConf)
│   ├── config_dataclass.py  # Dataclass-based configuration
│   ├── config_adapter.py    # Config system adapter
│   ├── constants.py         # Project constants
│   ├── exceptions.py        # Custom exceptions
│   ├── metadata_cache.py    # Basic metadata caching
│   ├── unified_cache.py     # Unified cache system
│   ├── types.py             # Type definitions
│   ├── file_ops.py          # File operations
│   ├── logging.py           # Logging setup
│   └── keys/                # API key management
│       ├── __init__.py
│       ├── cli.py           # Keys CLI commands
│       └── manager.py       # Key storage manager
├── quality/                 # Quality assessment
│   ├── __init__.py
│   ├── brisque.py          # BRISQUE implementation
│   ├── sightengine.py      # SightEngine integration
│   ├── claude.py           # Claude integration
│   ├── scorer.py           # Quality scoring logic
│   └── pipeline_stages.py  # Pipeline stage definitions
├── organizer/              # Media organization
│   ├── __init__.py
│   ├── media_organizer.py  # Main organizer class
│   ├── helpers.py          # Organizer utilities
│   └── runner.py           # CLI runner
├── metadata/               # Enhanced metadata system
│   ├── __init__.py
│   ├── models.py           # Metadata models
│   ├── extractor.py        # Metadata extraction
│   ├── embedder.py         # Image embedding
│   └── search.py           # Semantic search
├── database/               # Database layer (optional)
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy models
│   ├── repository.py       # Data access layer
│   └── config.py           # DB configuration
├── assets/                 # Asset management
│   ├── __init__.py
│   ├── hashing.py          # Content hashing
│   └── discovery.py        # Asset discovery
└── interface/              # User interfaces
    ├── __init__.py
    ├── main_cli.py         # Main CLI entry point
    ├── cli_handler.py      # CLI command handler
    └── alice_interface.py  # Alice AI interface
```

## Code Style Guidelines

### 1. **PEP 8 Compliance**
- Use `black` for automatic formatting
- Line length: 88 characters
- Use meaningful variable names

### 2. **Type Hints**
All functions should have type hints:

```python
def process_image(
    image_path: Path,
    quality_threshold: float = 0.8
) -> Optional[Dict[str, Any]]:
    """Process an image file.
    
    Args:
        image_path: Path to the image file
        quality_threshold: Minimum quality score (0-1)
        
    Returns:
        Processing results or None if failed
        
    Raises:
        MediaAnalysisError: If analysis fails
    """
```

### 3. **Documentation**
- All modules, classes, and functions must have docstrings
- Use Google-style docstrings
- Include examples for complex functions

### 4. **Error Handling**
- Use custom exceptions from `core.exceptions`
- Log errors appropriately
- Never use bare `except:` clauses

### 5. **Testing**
- Write tests for all new functionality
- Aim for >80% code coverage
- Use pytest fixtures for setup

## Development Setup

### 1. **Clone and Install**
```bash
git clone https://github.com/yourusername/alicemultiverse.git
cd alicemultiverse
pip install -e ".[dev,quality,secure]"
```

### 2. **Run Tests**
```bash
# Run all tests
pytest

# With coverage
pytest --cov=alicemultiverse --cov-report=html

# Specific test file
pytest tests/test_config.py
```

### 3. **Code Quality Checks**
```bash
# Format code
black alicemultiverse tests

# Sort imports
isort alicemultiverse tests

# Lint
flake8 alicemultiverse tests

# Type checking
mypy alicemultiverse
```

### 4. **Pre-commit Hook**
Create `.git/hooks/pre-commit`:
```bash
#!/bin/sh
black --check alicemultiverse tests
isort --check-only alicemultiverse tests
flake8 alicemultiverse tests
mypy alicemultiverse
```

## Adding New Features

### 1. **New AI Detector**
1. Create detector in `detectors/` module
2. Inherit from `BaseDetector` class
3. Implement `detect()` method
4. Add to detector registry

### 2. **New Quality Assessor**
1. Create assessor in `quality/` module
2. Implement standard interface
3. Add configuration options
4. Update pipeline stages

### 3. **New File Type Support**
1. Update constants in `core/constants.py`
2. Add detection logic
3. Update file discovery
4. Add tests

## Architecture Principles

### 1. **Separation of Concerns**
- Each module has a single responsibility
- Clear interfaces between modules
- No circular dependencies

### 2. **Dependency Injection**
- Pass dependencies explicitly
- Use interfaces/protocols
- Easy to mock for testing

### 3. **Configuration Over Code**
- Behavior controlled by configuration
- Sensible defaults
- Easy overrides

### 4. **Logging Over Printing**
- Use structured logging
- Appropriate log levels
- No print statements in library code

### 5. **Fail Gracefully**
- Handle errors appropriately
- Provide useful error messages
- Continue processing when possible

## Performance Considerations

### 1. **Async Operations**
- Use async/await for I/O operations
- Batch API calls
- Implement rate limiting

### 2. **Caching**
- Cache expensive computations
- Use content-based hashing
- Implement cache invalidation

### 3. **Memory Management**
- Process large files in chunks
- Release resources promptly
- Monitor memory usage

## Release Process

1. Update version in `alicemultiverse/version.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag -a v2.0.0 -m "Release v2.0.0"`
5. Build distribution: `python -m build`
6. Upload to PyPI: `twine upload dist/*`

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run quality checks
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open Pull Request

## Troubleshooting

### Import Errors
- Ensure package is installed: `pip install -e .`
- Check Python path: `python -c "import sys; print(sys.path)"`

### Test Failures
- Check test dependencies: `pip install -e ".[dev]"`
- Run specific test with verbose: `pytest -vv tests/test_file.py::test_name`

### Type Checking Issues
- Update type stubs: `pip install types-requests types-aiofiles`
- Use `# type: ignore` sparingly with explanation