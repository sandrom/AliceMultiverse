# Contributing to AliceMultiverse

Thank you for your interest in contributing to AliceMultiverse! This guide will help you get started.

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) for clear and automated versioning.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature (triggers MINOR version bump)
- `fix`: A bug fix (triggers PATCH version bump)
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools
- `ci`: Changes to CI configuration files and scripts

### Breaking Changes

Add `!` after the type or include `BREAKING CHANGE:` in the footer to trigger a MAJOR version bump.

### Examples

```bash
# Feature
feat: add API key management via CLI

# Bug fix
fix: correct BRISQUE compatibility with scikit-image 0.20+

# Breaking change
feat!: reorganize package structure

BREAKING CHANGE: The main entry point has changed from organizer.py to alice command

# Documentation
docs: update README with alice keys setup commands

# Chore
chore: update dependencies in requirements.txt
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Make your changes
4. Write or update tests as needed
5. Update documentation
6. Commit using conventional commits
7. Push to your fork (`git push origin feat/amazing-feature`)
8. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/AliceMultiverse.git
cd AliceMultiverse

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (REQUIRED)
pip install pre-commit
pre-commit install

# Run tests
pytest
```

## Security Practices

### Pre-commit Hooks

We use pre-commit hooks to prevent sensitive data from entering the repository. These are **mandatory** for all contributors.

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

### What Gets Scanned

Our security hooks check for:
- API keys, tokens, and passwords
- Private SSH keys and certificates
- Personal information (emails, phone numbers, SSNs)
- Hardcoded local paths (e.g., `/Users/username/`)
- Database credentials and connection strings
- AWS keys and other cloud provider secrets

### Best Practices

1. **Never commit sensitive data**
   - Use environment variables for secrets
   - Store API keys in `.env` files (which are gitignored)
   - Use generic paths in documentation (e.g., `~/Documents` not `/Users/john/Documents`)

2. **Use placeholders in examples**
   ```python
   # Good
   api_key = os.environ.get("ANTHROPIC_API_KEY")
   
   # Bad
   api_key = "sk-ant-123456789"
   ```

3. **Check before committing**
   ```bash
   # Run security scan manually
   python scripts/security/check_sensitive_patterns.py *.py
   
   # Let pre-commit do it for you
   git add .
   git commit -m "feat: add new feature"  # pre-commit runs automatically
   ```

4. **If a secret is accidentally committed**
   - Do NOT just remove it in a new commit
   - Contact maintainers immediately
   - The secret must be rotated/invalidated
   - The commit history may need to be rewritten

### Pull Request Security Checks

All PRs undergo automated security scanning:
- **Gitleaks**: Detects secrets in code
- **TruffleHog**: Deep secret scanning with entropy analysis
- **Bandit**: Python security vulnerabilities
- **Safety**: Checks dependencies for known vulnerabilities
- **CodeQL**: Advanced security analysis
- **Custom checks**: Project-specific sensitive patterns

PRs with security issues will be automatically blocked until resolved.

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to all public functions and classes
- Keep functions focused and small

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage

## Questions?

Feel free to open an issue for any questions or discussions!