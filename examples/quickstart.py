#!/usr/bin/env python3
"""
AliceMultiverse Quick Start Example

This example shows the simplest way to organize AI-generated media files.
It will:
1. Look for images in your ~/Downloads folder
2. Detect which AI tool created them (Midjourney, DALL-E, etc.)
3. Organize them into dated folders

No API keys or complex configuration required!
"""

import os
from pathlib import Path
from alicemultiverse.interface import AliceOrchestrator

def main():
    # Set up paths - you can change these to your preferred locations
    downloads_folder = Path.home() / "Downloads"
    organized_folder = Path.home() / "Pictures" / "AI-Organized"
    
    print("🎨 AliceMultiverse Quick Start")
    print(f"📥 Looking for AI images in: {downloads_folder}")
    print(f"📤 Will organize them to: {organized_folder}")
    print()
    
    # Create the orchestrator with minimal configuration
    alice = AliceOrchestrator(
        inbox_path=str(downloads_folder),
        organized_path=str(organized_folder)
    )
    
    # Process the files
    print("🔍 Scanning for AI-generated images...")
    results = alice.process()
    
    # Show what we found
    if results.get('processed_count', 0) > 0:
        print(f"\n✅ Organized {results['processed_count']} files!")
        print(f"📁 Check your organized folder: {organized_folder}")
        
        # Show a sample of what was organized
        if 'by_source' in results:
            print("\n📊 Files organized by AI source:")
            for source, count in results['by_source'].items():
                print(f"   • {source}: {count} files")
    else:
        print("\n💡 No AI-generated images found in Downloads folder.")
        print("   Try saving some images from Midjourney, DALL-E, or Stable Diffusion!")
    
    print("\n🎯 Next steps:")
    print("   • Run 'alice --help' to see all options")
    print("   • Add '--quality' flag to enable quality assessment")
    print("   • Use '--watch' to continuously monitor for new files")

if __name__ == "__main__":
    main()