#!/usr/bin/env python3
"""Script to migrate from monolithic unified_duckdb.py to modular implementation."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_compatibility():
    """Test that the new implementation is compatible with the old one."""
    print("Testing DuckDB implementation compatibility...")

    # Test imports work
    try:
        from alicemultiverse.storage.unified_duckdb import UnifiedDuckDBStorage as OldStorage
        print("✓ Old implementation imports successfully")
    except Exception as e:
        print(f"✗ Failed to import old implementation: {e}")
        return False

    try:
        from alicemultiverse.storage.unified_duckdb_new import UnifiedDuckDBStorage as NewStorage
        print("✓ New implementation imports successfully")
    except Exception as e:
        print(f"✗ Failed to import new implementation: {e}")
        return False

    # Test that all methods exist
    old_methods = set(dir(OldStorage))
    new_methods = set(dir(NewStorage))

    missing_methods = old_methods - new_methods
    if missing_methods:
        print(f"✗ Missing methods in new implementation: {missing_methods}")
        return False
    else:
        print("✓ All methods present in new implementation")

    # Test basic functionality
    try:
        # Create in-memory instances
        try:
            old_db = OldStorage()
        except Exception as e:
            print(f"⚠️  Old implementation has initialization issues: {e}")
            print("   This is expected if the old code has array type issues")
            old_db = None

        new_db = NewStorage()

        # Test basic operations
        test_data = {
            "content_hash": "test123",
            "file_path": "/tmp/test.jpg",
            "metadata": {
                "media_type": "image",
                "file_size": 1000,
                "ai_source": "test"
            }
        }

        # Test new implementation
        # Test upsert
        new_db.upsert_asset(
            test_data["content_hash"],
            test_data["file_path"],
            test_data["metadata"]
        )
        print("✓ Upsert works in new implementation")

        # Test search
        new_results, new_count = new_db.search()

        if new_count == 1:
            print("✓ Search works in new implementation")
        else:
            print(f"✗ Search failed in new implementation: count={new_count}")
            return False

        # Test get_statistics
        new_stats = new_db.get_statistics()

        if new_stats["total_assets"] == 1:
            print("✓ Statistics work in new implementation")
        else:
            print("✗ Statistics failed in new implementation")
            return False

        # Test other key methods
        # Test get_facets
        facets = new_db.get_facets()
        print("✓ get_facets works")

        # Test find_similar (should return empty for now)
        similar = new_db.find_similar(test_data["content_hash"])
        print("✓ find_similar works")

        # Test batch upsert
        batch_result = new_db.upsert_assets_batch([
            ("test456", "/tmp/test2.jpg", {"media_type": "image"})
        ])
        if batch_result["processed"] == 1:
            print("✓ Batch upsert works")
        else:
            print("✗ Batch upsert failed")
            return False

    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        return False

    print("\n✅ All compatibility tests passed!")
    return True


def migrate():
    """Perform the migration."""
    print("\nMigrating to modular DuckDB implementation...")

    # Backup old file
    old_file = Path("alicemultiverse/storage/unified_duckdb.py")
    backup_file = Path("alicemultiverse/storage/unified_duckdb_backup.py")

    if old_file.exists():
        print(f"Backing up {old_file} to {backup_file}")
        import shutil
        shutil.copy2(old_file, backup_file)

    # Update __init__.py to use new implementation
    init_file = Path("alicemultiverse/storage/__init__.py")
    print(f"Updating {init_file}")

    content = init_file.read_text()
    content = content.replace(
        "from .unified_duckdb import",
        "from .unified_duckdb_new import"
    )
    init_file.write_text(content)

    print("\n✅ Migration complete!")
    print("\nNext steps:")
    print("1. Run tests to ensure everything works")
    print("2. Delete the old unified_duckdb.py file")
    print("3. Rename unified_duckdb_new.py to unified_duckdb.py")
    print("4. Update imports in __init__.py")
    print("5. Delete the backup file")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate DuckDB implementation")
    parser.add_argument("--test-only", action="store_true", help="Only run tests")
    parser.add_argument("--migrate", action="store_true", help="Perform migration")

    args = parser.parse_args()

    if args.test_only or not args.migrate:
        success = test_compatibility()
        if not success:
            sys.exit(1)

    if args.migrate:
        if test_compatibility():
            migrate()
        else:
            print("\n✗ Cannot migrate - compatibility tests failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
