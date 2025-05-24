#!/usr/bin/env python3
"""Test the asset processor service."""

import asyncio
import sys
from pathlib import Path

# Add the interface module to path
sys.path.insert(0, str(Path(__file__).parent / "alicemultiverse"))

from alicemultiverse.interface.asset_processor_client import AssetProcessorClient


async def test_service():
    """Test the asset processor service."""
    print("Testing Asset Processor Service...")
    
    async with AssetProcessorClient("http://localhost:8001") as client:
        # Test health check
        print("\n1. Testing health check...")
        healthy = await client.health_check()
        print(f"   Service healthy: {healthy}")
        
        if not healthy:
            print("   Service is not running. Please start it with:")
            print("   cd services/asset-processor && python start_service.py")
            return
        
        # Create a test file
        test_file = Path("/tmp/test_image.jpg")
        test_file.write_bytes(b"fake image data for testing")
        
        # Test analysis
        print("\n2. Testing asset analysis...")
        try:
            result = await client.analyze(test_file)
            print(f"   Analysis result:")
            print(f"   - Content hash: {result.get('content_hash', 'N/A')}")
            print(f"   - Media type: {result.get('media_type', 'N/A')}")
            print(f"   - File size: {result.get('file_size', 'N/A')}")
            print(f"   - AI source: {result.get('ai_source', 'N/A')}")
        except Exception as e:
            print(f"   Analysis failed: {e}")
        
        # Test quality assessment
        print("\n3. Testing quality assessment...")
        try:
            result = await client.assess_quality(
                test_file, 
                "abc123",
                pipeline_mode="basic"
            )
            print(f"   Quality result:")
            print(f"   - Star rating: {result.get('star_rating', 'N/A')}")
            print(f"   - Combined score: {result.get('combined_score', 'N/A')}")
            print(f"   - BRISQUE score: {result.get('brisque_score', 'N/A')}")
        except Exception as e:
            print(f"   Quality assessment failed: {e}")
        
        # Test organization planning
        print("\n4. Testing organization planning...")
        try:
            result = await client.plan_organization(
                test_file,
                "abc123",
                {"created": "2024-03-15T10:00:00", "ai_source": "stable-diffusion"},
                quality_rating=5
            )
            print(f"   Organization plan:")
            print(f"   - Destination: {result.get('destination_path', 'N/A')}")
            print(f"   - Date folder: {result.get('date_folder', 'N/A')}")
            print(f"   - Project name: {result.get('project_name', 'N/A')}")
            print(f"   - Quality folder: {result.get('quality_folder', 'N/A')}")
        except Exception as e:
            print(f"   Organization planning failed: {e}")
        
        # Clean up
        test_file.unlink(missing_ok=True)
        
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(test_service())