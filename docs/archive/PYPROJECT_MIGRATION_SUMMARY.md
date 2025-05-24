# PyProject.toml Migration Summary

## Changes Made

### 1. Removed setup.py
- Deleted outdated `setup.py` file
- All configuration now in `pyproject.toml`

### 2. Updated pyproject.toml
- Added missing dependencies (sqlalchemy, alembic, pyyaml, click)
- Fixed entry point: `alice = "alicemultiverse.interface.main_cli:main"`
- Added `full` extras combining all optional dependencies
- Added `docs` extras for documentation tools
- Added modern tool configurations (ruff, pytest markers)
- Fixed package discovery configuration

### 3. Created CLI wrapper
- Added `alicemultiverse/cli.py` for backward compatibility
- Simple wrapper that imports from actual CLI location

### 4. Updated Documentation
- Updated installation instructions to use `pip install -e .`
- Added REQUIREMENTS_MIGRATION.md explaining the change
- Fixed references in cleanup_root.py script

### 5. Added Type Support
- Created `py.typed` marker file for PEP 561 compliance

## Benefits

1. **Modern Standard**: Following PEP 517/518
2. **Single Source of Truth**: All metadata in one file
3. **Better Tool Support**: Works with modern Python tools
4. **Cleaner Structure**: No duplicate configuration

## Migration for Users

```bash
# Old way (deprecated)
pip install -r requirements.txt

# New way
pip install -e .
pip install -e ".[quality]"   # With extras
```

## Backward Compatibility

- Entry point `alice` command still works
- requirements*.txt files kept temporarily (remove in v3.0)
- All existing functionality preserved