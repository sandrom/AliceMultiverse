#!/usr/bin/env python3
"""Test script to verify project folder handling."""

import tempfile
import shutil
from pathlib import Path
from alicemultiverse.core.config import load_config
from alicemultiverse.organizer.media_organizer import MediaOrganizer

def test_project_structure():
    """Test that only top-level folders are treated as projects."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        inbox = Path(tmpdir) / "inbox"
        organized = Path(tmpdir) / "organized"
        
        # Create a project with subfolders
        project = inbox / "alice-1"
        subfolder1 = project / "renders"
        subfolder2 = project / "exports" / "final"
        
        # Create directories
        subfolder1.mkdir(parents=True)
        subfolder2.mkdir(parents=True)
        
        # Create test files in various locations
        files = [
            project / "image1.jpg",
            subfolder1 / "image2.jpg",
            subfolder2 / "image3.jpg",
        ]
        
        for f in files:
            f.write_text("fake image")
        
        # Load config and update paths
        config = load_config()
        config.paths.inbox = str(inbox)
        config.paths.organized = str(organized)
        config.processing.dry_run = True
        
        # Run organizer
        organizer = MediaOrganizer(config)
        organizer.organize()
        
        # Check results
        print("\nTest Structure Created:")
        print(f"  Project: alice-1")
        print(f"  - Direct file: image1.jpg")
        print(f"  - Subfolder 'renders': image2.jpg")
        print(f"  - Nested 'exports/final': image3.jpg")
        
        print("\nExpected behavior:")
        print("  All files should be organized under 'alice-1' project")
        print("  Subfolders should be ignored in organization")
        
        # The stats should show all files under 'alice-1' project
        stats = organizer.stats
        print(f"\nStats by project: {dict(stats['by_project'])}")
        
        # All files should be under alice-1
        assert stats['by_project']['alice-1'] == 3, f"Expected 3 files in alice-1, got {stats['by_project']['alice-1']}"
        print("\n✓ Test passed: All files correctly assigned to top-level project")

if __name__ == "__main__":
    test_project_structure()