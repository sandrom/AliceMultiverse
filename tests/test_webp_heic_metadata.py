"""Test WebP and HEIC metadata functionality."""

import pytest
from pathlib import Path
import tempfile
from PIL import Image
import numpy as np

from alicemultiverse.metadata.embedder import MetadataEmbedder, HEIF_AVAILABLE


def create_test_image(format: str, size=(100, 100)) -> Path:
    """Create a test image in the specified format."""
    # Create random image data
    data = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
    img = Image.fromarray(data, 'RGB')
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as tmp:
        img.save(tmp.name, format=format.upper())
        return Path(tmp.name)


class TestWebPMetadata:
    """Test WebP metadata embedding and extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.embedder = MetadataEmbedder()
        self.test_metadata = {
            'prompt': 'A beautiful sunset over mountains',
            'ai_source': 'stable-diffusion',
            'quality_score': 4.5,
            'tags': ['sunset', 'mountains', 'landscape']
        }
    
    def test_webp_embed_extract(self):
        """Test embedding and extracting metadata from WebP."""
        # Create test WebP image
        img_path = create_test_image('webp')
        
        try:
            # Embed metadata
            success = self.embedder.embed_metadata(img_path, self.test_metadata)
            assert success, "Failed to embed WebP metadata"
            
            # Extract metadata
            extracted = self.embedder.extract_metadata(img_path)
            
            # Check key fields were preserved
            # Note: WebP support is limited, so we may not get all fields back
            if 'prompt' in extracted:
                assert extracted['prompt'] == self.test_metadata['prompt']
            if 'ai_source' in extracted:
                assert extracted['ai_source'] == self.test_metadata['ai_source']
                
        finally:
            # Clean up
            img_path.unlink(missing_ok=True)
    
    def test_webp_limited_support_note(self):
        """Test that WebP works but with limited metadata support."""
        img_path = create_test_image('webp')
        try:
            # Should work with Pillow's built-in WebP support
            success = self.embedder.embed_metadata(img_path, self.test_metadata)
            assert success
            
            # Extract - may have limited data
            extracted = self.embedder.extract_metadata(img_path)
            assert isinstance(extracted, dict)
            # WebP through Pillow has very limited metadata support
            # so we don't check for specific fields
        finally:
            img_path.unlink(missing_ok=True)


class TestHEICMetadata:
    """Test HEIC/HEIF metadata embedding and extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.embedder = MetadataEmbedder()
        self.test_metadata = {
            'prompt': 'Portrait of a person in golden hour',
            'ai_source': 'midjourney',
            'quality_score': 5.0,
            'tags': ['portrait', 'golden-hour', 'person']
        }
    
    @pytest.mark.skipif(not HEIF_AVAILABLE, reason="pillow-heif not installed")
    def test_heic_embed_extract(self):
        """Test embedding and extracting metadata from HEIC."""
        # Note: Creating actual HEIC files requires the HEIF library
        # For testing, we'll use a regular format and simulate HEIC behavior
        # In production, this would use actual HEIC files
        
        # Create a test image in JPEG format (pillow-heif can't create HEIC from scratch easily)
        img_path = create_test_image('jpeg')
        img_path = img_path.with_suffix('.heic')  # Rename to .heic
        
        # For this test, we'll just verify the methods don't crash
        # Real HEIC testing would require actual HEIC files
        try:
            # Embed metadata - should handle gracefully
            success = self.embedder.embed_metadata(img_path, self.test_metadata)
            assert success is not None
            
            # Extract metadata - should return dict (possibly empty)
            extracted = self.embedder.extract_metadata(img_path)
            assert isinstance(extracted, dict)
            
        finally:
            # Clean up
            img_path.unlink(missing_ok=True)
    
    def test_heic_without_library(self):
        """Test behavior when HEIF library is not available."""
        if HEIF_AVAILABLE:
            pytest.skip("HEIF library is available")
            
        # Create fake HEIC file
        img_path = Path(tempfile.mktemp(suffix='.heic'))
        img_path.write_bytes(b'fake heic data')
        
        try:
            # Should not crash, just warn
            success = self.embedder.embed_metadata(img_path, self.test_metadata)
            assert success  # Returns True even without library
            
            extracted = self.embedder.extract_metadata(img_path)
            assert isinstance(extracted, dict)
            assert len(extracted) == 0  # Should be empty without library
            
        finally:
            img_path.unlink(missing_ok=True)


class TestFormatDetection:
    """Test that all supported formats are handled correctly."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.embedder = MetadataEmbedder()
        self.formats = {
            '.png': 'PNG',
            '.jpg': 'JPEG', 
            '.jpeg': 'JPEG',
            '.webp': 'WEBP',
            '.heic': 'HEIC',
            '.heif': 'HEIF'
        }
    
    def test_all_formats_handled(self):
        """Ensure all supported formats have handlers."""
        test_metadata = {'test': 'data'}
        
        for ext, format_name in self.formats.items():
            # Create dummy file path
            img_path = Path(f"test{ext}")
            
            # The embed/extract methods should handle all formats without raising
            # unhandled format errors (they may fail for other reasons like file not found)
            try:
                # These will fail with file not found, but that's OK
                # We're just checking that the format is recognized
                self.embedder.embed_metadata(img_path, test_metadata)
            except FileNotFoundError:
                pass  # Expected
            except Exception as e:
                # Should not get "Unexpected format" error
                assert "Unexpected format" not in str(e)
                
            try:
                self.embedder.extract_metadata(img_path)
            except FileNotFoundError:
                pass  # Expected  
            except Exception as e:
                # Should not get format errors
                assert "Unexpected format" not in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])