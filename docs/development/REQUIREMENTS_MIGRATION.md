# Requirements Migration Notice

As of version 2.1.0, AliceMultiverse has migrated to using `pyproject.toml` for all dependency management.

## For Users

### Old Method (Deprecated)
```bash
pip install -r requirements.txt
```

### New Method (Recommended)
```bash
pip install -e .               # Basic installation
pip install -e ".[quality]"    # With quality assessment
pip install -e ".[full]"       # All features
```

## For Developers

### Old Method (Deprecated)
```bash
pip install -r requirements-dev.txt
```

### New Method (Recommended)
```bash
pip install -e ".[dev]"        # Development dependencies
pip install -e ".[dev,docs]"   # Dev + documentation tools
```

## Why the Change?

- **Modern Standard**: `pyproject.toml` is the Python standard (PEP 517/518)
- **Single Source**: All project metadata in one file
- **Better Tools**: Works with modern tools like `pip-tools`, `poetry`, `hatch`
- **Cleaner**: No need for separate requirements files

## Legacy Support

The `requirements*.txt` files are kept temporarily for backward compatibility but will be removed in v3.0.

If you have scripts or CI/CD that use these files, please update them to use `pip install -e .` instead.