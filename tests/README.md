# Test Suite Documentation

This directory contains the test suite for AliceMultiverse, following Python testing best practices with pytest.

## Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for full workflows
└── conftest.py     # Shared fixtures and test configuration
```

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test
pytest tests/unit/test_config.py::TestConfig::test_default_config_structure

# Run tests matching a pattern
pytest -k "config"

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Coverage

```bash
# Run with coverage report
pytest --cov=alicemultiverse

# Generate HTML coverage report
pytest --cov=alicemultiverse --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Test Organization

### Unit Tests

Unit tests focus on individual components in isolation:

- `test_config.py` - Configuration loading and validation
- `test_cli.py` - Command-line interface parsing
- `test_metadata_cache.py` - Metadata caching functionality
- `test_quality.py` - BRISQUE quality assessment
- `test_keys.py` - API key management

### Integration Tests

Integration tests verify complete workflows:

- `test_full_workflow.py` - End-to-end organization scenarios

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `temp_dir` - Temporary directory for test files
- `sample_config` - Sample configuration dictionary
- `omega_config` - OmegaConf configuration object
- `sample_media_files` - Test media files
- `mock_metadata_cache` - Mock metadata cache
- `mock_brisque` - Mock BRISQUE assessor
- `mock_api_manager` - Mock API key manager

## Best Practices

1. **Isolation**: Each test should be independent
2. **Fixtures**: Use fixtures for common setup
3. **Mocking**: Mock external dependencies
4. **Parametrization**: Test multiple scenarios with `@pytest.mark.parametrize`
5. **Markers**: Use markers to categorize tests (`unit`, `integration`, `slow`)

## CI/CD Integration

Tests run automatically on GitHub Actions for:
- Multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Multiple operating systems (Linux, macOS, Windows)
- Code quality checks (flake8, mypy)
- Security scanning (bandit)

## Current Status

The test suite is under active development. Some tests may fail due to incomplete implementations in the main codebase. This is expected as we're building out the functionality.