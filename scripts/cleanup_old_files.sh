#!/bin/bash
# Cleanup script to remove old files after refactoring

echo "Cleaning up old files after refactoring..."
echo

# Files to remove
OLD_FILES=(
    "organizer.py"              # Old monolithic file - now modularized
    "test_omegaconf.py"         # Test file no longer needed
    "quality_pipeline.py"       # Integrated into package
    "quality_organizer_integration.py"  # Integrated into package
)

# Show what will be removed
echo "The following files will be removed:"
for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file ($(ls -lh "$file" | awk '{print $5}'))"
    fi
done

echo
read -p "Are you sure you want to remove these files? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    for file in "${OLD_FILES[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
            echo "✓ Removed $file"
        fi
    done
    echo
    echo "Cleanup complete!"
    echo
    echo "Note: The refactored code is now in the 'alicemultiverse' package."
    echo "Use 'alice' command after installation with: pip install -e ."
else
    echo "Cleanup cancelled."
fi