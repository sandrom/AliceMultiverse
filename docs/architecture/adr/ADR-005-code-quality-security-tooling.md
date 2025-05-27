# ADR-005: Code Quality and Security Tooling

**Status**: Accepted  
**Date**: 2025-01-27  
**Context**: Development Practices and Security

## Context

As AliceMultiverse grows in complexity and prepares for production use, we need consistent code quality standards and security practices. The codebase had accumulated technical debt with:
- Inconsistent formatting across 137+ files
- Security vulnerabilities (MD5 usage, missing timeouts)
- Silent exception handling (`except: pass`)
- No automated quality checks
- No security scanning

## Decision

Implement a comprehensive suite of code quality and security tools:

### Primary Tools
- **ruff**: Fast Python linter combining multiple tools (flake8, isort, etc.)
- **black**: Opinionated code formatter for consistency
- **bandit**: Security vulnerability scanner
- **mypy**: Static type checker
- **yamllint**: YAML file linter
- **safety**: Dependency vulnerability scanner
- **detect-secrets**: Prevent secrets in code

### Configuration Strategy
- Configure tools in `pyproject.toml` for centralized management
- Set appropriate ignore rules for expected patterns
- Use per-file ignores for tests and generated code
- Enforce 100-character line length
- Target Python 3.12

## Rationale

### Why These Tools

1. **ruff**: Fastest Python linter, replaces 10+ tools
   - Combines pycodestyle, pyflakes, isort, and more
   - 10-100x faster than traditional tools
   - Consistent with modern Python practices

2. **black**: Zero-configuration formatting
   - Eliminates style debates
   - Ensures consistent codebase
   - Integrates with all major editors

3. **bandit**: Security-focused analysis
   - Catches common security mistakes
   - Identifies hardcoded passwords
   - Prevents insecure practices

4. **Type checking and validation**:
   - mypy for type safety
   - yamllint for configuration files
   - Catches errors before runtime

### Configuration Decisions

1. **Global Ignores**:
   - `G004`: f-strings in logging (readable and our logging is not performance-critical)
   - `TID252`: Relative imports (valid within package structure)
   - `S101`: Assert in tests (expected pattern)

2. **Per-file Ignores**:
   - Tests: Allow magic values, unused variables, subprocess calls
   - Scripts: Allow print statements, implicit namespaces
   - Migrations: Allow unused imports

3. **Exception Handling**:
   - No `except: pass` - always log at minimum
   - Use specific exception types where possible
   - Add comments for legitimate pass cases (e.g., CancelledError)

## Consequences

### Positive
- Consistent code style across entire codebase
- Early detection of security vulnerabilities
- Reduced bugs through type checking
- Faster code reviews (style is automated)
- Better debugging with proper exception logging

### Negative
- Initial cleanup effort (6071 → 204 issues)
- Learning curve for new contributors
- Some legitimate patterns need ignore comments
- Slightly slower pre-commit hooks

### Migration Results

1. **Security Fixes**:
   - Fixed MD5 usage with `usedforsecurity=False`
   - Added timeouts to all HTTP requests
   - Replaced bare except clauses

2. **Code Quality**:
   - Reformatted 137 files with black
   - Fixed 4987 issues automatically with ruff
   - Standardized imports and line lengths

3. **Ongoing Issues** (204 remaining):
   - Mostly import organization and line length
   - Can be addressed incrementally
   - Non-critical to functionality

## Implementation Guidelines

1. **Development Workflow**:
   ```bash
   # Before committing
   ruff check .
   black .
   mypy .
   bandit -r alicemultiverse
   ```

2. **CI/CD Integration**:
   - Add to GitHub Actions
   - Block PRs that fail quality checks
   - Run security scans on schedule

3. **Editor Integration**:
   - Configure black as formatter
   - Enable ruff linting
   - Set up pre-commit hooks

4. **Exception Handling**:
   ```python
   # Bad
   try:
       operation()
   except:
       pass
   
   # Good
   try:
       operation()
   except SpecificError as e:
       logger.debug(f"Expected error: {e}")
   ```

## References

- [ruff documentation](https://docs.astral.sh/ruff/)
- [black documentation](https://black.readthedocs.io/)
- [bandit documentation](https://bandit.readthedocs.io/)
- PEP 8 - Style Guide for Python Code
- instructions.md - Project development guidelines