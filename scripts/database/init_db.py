#!/usr/bin/env python3
"""Initialize the AliceMultiverse database."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.database.config import DATABASE_URL, init_db


def main():
    """Initialize the database."""
    print(f"Initializing database at: {DATABASE_URL}")

    try:
        init_db()
        print("✓ Database initialized successfully!")

        if DATABASE_URL.startswith("sqlite"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            print(f"✓ SQLite database created at: {db_path}")

    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
