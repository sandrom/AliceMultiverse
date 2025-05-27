#!/bin/bash
# Cleanup script to remove temporary and unnecessary files

echo "AliceMultiverse Project Cleanup"
echo "==============================="
echo

# Function to show file sizes
show_size() {
    if [ -d "$1" ]; then
        echo "  - $1/ ($(du -sh "$1" 2>/dev/null | cut -f1))"
    elif [ -f "$1" ]; then
        echo "  - $1 ($(ls -lh "$1" 2>/dev/null | awk '{print $5}'))"
    fi
}

# Files and directories to clean
TEMP_FILES=(
    "__pycache__"
    "*.pyc"
    ".pytest_cache"
    ".coverage"
    "htmlcov"
    "dist"
    "build"
    "*.egg-info"
    ".DS_Store"
    "Thumbs.db"
)

# Find and show what will be removed
echo "The following temporary files will be removed:"
total_size=0
for pattern in "${TEMP_FILES[@]}"; do
    if [[ "$pattern" == "__pycache__" ]] || [[ "$pattern" == ".pytest_cache" ]] || [[ "$pattern" == "htmlcov" ]] || [[ "$pattern" == "dist" ]] || [[ "$pattern" == "build" ]]; then
        # Directory patterns
        find . -type d -name "$pattern" 2>/dev/null | while read -r dir; do
            show_size "$dir"
        done
    else
        # File patterns
        find . -type f -name "$pattern" 2>/dev/null | while read -r file; do
            show_size "$file"
        done
    fi
done

echo
read -p "Remove temporary files? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    echo "✓ Removed __pycache__ directories"
    
    # Remove .pyc files
    find . -type f -name "*.pyc" -delete
    echo "✓ Removed .pyc files"
    
    # Remove pytest cache
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
    echo "✓ Removed .pytest_cache directories"
    
    # Remove coverage files
    rm -rf .coverage htmlcov
    echo "✓ Removed coverage files"
    
    # Remove build artifacts
    rm -rf dist build *.egg-info
    echo "✓ Removed build artifacts"
    
    # Remove OS-specific files
    find . -type f -name ".DS_Store" -delete
    find . -type f -name "Thumbs.db" -delete
    echo "✓ Removed OS-specific files"
    
    echo
    echo "Cleanup complete!"
else
    echo "Cleanup cancelled."
fi

# Optional: Show disk usage after cleanup
echo
echo "Current project size: $(du -sh . | cut -f1)"