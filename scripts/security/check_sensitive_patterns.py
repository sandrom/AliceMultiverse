#!/usr/bin/env python3
"""Check for sensitive patterns in files before commit."""

import re
import sys
from pathlib import Path
from re import Pattern

# Patterns to detect sensitive information
SENSITIVE_PATTERNS: list[tuple[str, Pattern]] = [
    # API Keys and Tokens
    (
        "API Key",
        re.compile(
            r'(?i)(api[_\s-]?key|apikey|api[_\s-]?token|access[_\s-]?token)\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
            re.IGNORECASE,
        ),
    ),
    (
        "AWS Key",
        re.compile(
            r'(?i)(aws[_\s-]?access[_\s-]?key[_\s-]?id|aws[_\s-]?secret[_\s-]?access[_\s-]?key)\s*[:=]\s*["\']?[A-Z0-9]{20,}["\']?'
        ),
    ),
    ("Private Key", re.compile(r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----")),
    # Passwords
    ("Password", re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?[^"\']{8,}["\']?')),
    (
        "Database URL",
        re.compile(r"(?i)(mysql|postgresql|postgres|mongodb|redis)://[^:]+:[^@]+@[^/]+"),
    ),
    # Personal Information
    (
        "Email",
        re.compile(
            r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|org|net|edu|gov|mil|int|co\.[a-z]{2})\b"
        ),
    ),
    ("Phone", re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # Local Paths (Mac specific)
    ("Home Directory", re.compile(r"/Users/[a-zA-Z0-9_-]+/(?!Documents/AI/AliceMultiverse)")),
    ("Private Directory", re.compile(r"(?i)/private/|/tmp/|/var/folders/")),
    # Secrets in URLs
    ("Secret in URL", re.compile(r"https?://[^:]+:[^@]+@[^/]+")),
    ("Token in URL", re.compile(r"(?i)(token|key|secret)=[a-zA-Z0-9_\-]{16,}")),
]

# Whitelist patterns (things that look like secrets but aren't)
WHITELIST_PATTERNS = [
    re.compile(r"(?i)example\.com"),
    re.compile(r"(?i)localhost"),
    re.compile(r"(?i)127\.0\.0\.1"),
    re.compile(r"(?i)placeholder"),
    re.compile(r"(?i)your[_\s-]?api[_\s-]?key"),
    re.compile(r"(?i)xxx+"),
    re.compile(r"(?i)<[^>]+>"),  # Template variables
    re.compile(r"(?i)sk-ant-\.\.\.|user,secret"),  # Documentation examples
]

# File-specific exclusions
EXCLUDE_CHECKS = {
    "API_KEYS.md": ["API Key", "AWS Key"],  # Documentation about API keys
    ".env.example": ["API Key", "Password", "Database URL"],  # Example env file
    "test_": ["Password", "API Key"],  # Test files may have mock secrets
}


def is_whitelisted(match: str) -> bool:
    """Check if a match is whitelisted."""
    return any(pattern.search(match) for pattern in WHITELIST_PATTERNS)


def check_file(filepath: str) -> list[tuple[int, str, str]]:
    """Check a single file for sensitive patterns."""
    path = Path(filepath)
    if not path.exists() or not path.is_file():
        return []

    findings = []
    filename = path.name

    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError):
        # Skip binary files or files we can't read
        return []

    for line_num, line in enumerate(lines, 1):
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith(("#", "//", "/*", "*")):
            continue

        for pattern_name, pattern in SENSITIVE_PATTERNS:
            # Check if this pattern should be excluded for this file
            for exclude_prefix, excluded_patterns in EXCLUDE_CHECKS.items():
                if filename.startswith(exclude_prefix) and pattern_name in excluded_patterns:
                    continue

            matches = pattern.finditer(line)
            for match in matches:
                matched_text = match.group(0)

                # Skip whitelisted matches
                if is_whitelisted(matched_text):
                    continue

                # Truncate long matches for display
                if len(matched_text) > 50:
                    display_text = matched_text[:47] + "..."
                else:
                    display_text = matched_text

                findings.append((line_num, pattern_name, display_text))

    return findings


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: check_sensitive_patterns.py <file1> [file2] ...")
        sys.exit(1)

    all_findings = []

    for filepath in sys.argv[1:]:
        findings = check_file(filepath)
        if findings:
            all_findings.extend([(filepath, *finding) for finding in findings])

    if all_findings:
        print("\n❌ SENSITIVE DATA DETECTED!")
        print("=" * 80)

        for filepath, line_num, pattern_type, matched_text in all_findings:
            print(f"\n📄 {filepath}:{line_num}")
            print(f"   Type: {pattern_type}")
            print(f"   Found: {matched_text}")

        print("\n" + "=" * 80)
        print("⚠️  Please remove sensitive data before committing!")
        print("\nSuggestions:")
        print("- Use environment variables for API keys")
        print("- Replace real paths with generic ones (e.g., ~/Documents)")
        print("- Use .env files (and add to .gitignore)")
        print("- For examples, use placeholders like 'your-api-key-here'")

        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
