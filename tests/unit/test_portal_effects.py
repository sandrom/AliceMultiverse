"""
Unit tests for portal effect detection.
"""

import pytest
import numpy as np
from PIL import Image
import tempfile
from pathlib import Path
import cv2
import json

from alicemultiverse.transitions.portal_effects import (
    Portal,
    PortalMatch,
    PortalDetector,
    PortalEffectGenerator,
    PortalEffectAnalysis,
    export_portal_effect
)


@pytest.fixture
def portal_images():
    """Create test images with portal shapes."""
    images = []
    
    # Image 1: Dark circle (good portal)
    img1 = np.ones((480, 640, 3), dtype=np.uint8) * 200
    cv2.circle(img1, (320, 240), 100, (50, 50, 50), -1)
    cv2.circle(img1, (320, 240), 102, (0, 0, 0), 3)  # Edge
    
    # Image 2: Dark rectangle (doorway)
    img2 = np.ones((480, 640, 3), dtype=np.uint8) * 180
    cv2.rectangle(img2, (270, 100), (370, 380), (30, 30, 30), -1)
    cv2.rectangle(img2, (268, 98), (372, 382), (0, 0, 0), 2)  # Edge
    
    # Image 3: Arch shape
    img3 = np.ones((480, 640, 3), dtype=np.uint8) * 220
    # Create arch using ellipse
    cv2.ellipse(img3, (320, 300), (120, 150), 0, 180, 360, (40, 40, 40), -1)
    cv2.rectangle(img3, (200, 300), (440, 480), (40, 40, 40), -1)
    
    # Save to temporary files
    for i, img in enumerate([img1, img2, img3]):
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        Image.fromarray(img).save(tmp.name)
        images.append(Path(tmp.name))
        tmp.close()
    
    yield images
    
    # Cleanup
    for img_path in images:
        img_path.unlink(missing_ok=True)


class TestPortal:
    """Test Portal dataclass."""
    
    def test_portal_creation(self):
        """Test creating a portal."""
        portal = Portal(
            shape_type="circle",
            center=(0.5, 0.5),
            size=(0.3, 0.3),
            confidence=0.9,
            darkness_ratio=0.8,
            edge_strength=0.7
        )
        
        assert portal.shape_type == "circle"
        assert portal.center == (0.5, 0.5)
        assert portal.size == (0.3, 0.3)
        assert portal.confidence == 0.9
        assert portal.darkness_ratio == 0.8
        assert portal.edge_strength == 0.7
    
    def test_portal_area(self):
        """Test portal area calculation."""
        # Circle portal
        circle = Portal(
            shape_type="circle",
            center=(0.5, 0.5),
            size=(0.4, 0.4),  # diameter
            confidence=1.0,
            darkness_ratio=1.0,
            edge_strength=1.0
        )
        
        expected_area = np.pi * 0.2 * 0.2  # radius = diameter/2
        assert abs(circle.area - expected_area) < 0.01
        
        # Rectangle portal
        rect = Portal(
            shape_type="rectangle",
            center=(0.5, 0.5),
            size=(0.4, 0.6),
            confidence=1.0,
            darkness_ratio=1.0,
            edge_strength=1.0
        )
        
        assert rect.area == 0.24  # 0.4 * 0.6
    
    def test_portal_quality_score(self):
        """Test portal quality score calculation."""
        # High quality portal
        good_portal = Portal(
            shape_type="circle",
            center=(0.5, 0.5),
            size=(0.5, 0.5),  # 25% of image
            confidence=0.9,
            darkness_ratio=0.8,
            edge_strength=0.9
        )
        
        assert 0.7 < good_portal.quality_score < 1.0
        
        # Low quality portal
        bad_portal = Portal(
            shape_type="circle",
            center=(0.5, 0.5),
            size=(0.05, 0.05),  # Too small
            confidence=0.5,
            darkness_ratio=0.2,
            edge_strength=0.3
        )
        
        assert bad_portal.quality_score < 0.3


class TestPortalDetector:
    """Test PortalDetector functionality."""
    
    def test_initialization(self):
        """Test detector initialization."""
        detector = PortalDetector()
        assert detector.min_portal_size == 0.05
        assert detector.max_portal_size == 0.5
        assert detector.darkness_threshold == 0.3
        assert detector.edge_threshold == 100
    
    def test_detect_portals(self, portal_images):
        """Test portal detection in images."""
        detector = PortalDetector()
        
        # Test circle detection
        portals = detector.detect_portals(portal_images[0])
        assert len(portals) > 0
        
        circles = [p for p in portals if p.shape_type == "circle"]
        assert len(circles) > 0
        
        # Test rectangle detection
        portals = detector.detect_portals(portal_images[1])
        rectangles = [p for p in portals if p.shape_type == "rectangle"]
        assert len(rectangles) > 0
    
    def test_portal_quality(self, portal_images):
        """Test that detected portals have quality scores."""
        detector = PortalDetector()
        
        portals = detector.detect_portals(portal_images[0])
        
        for portal in portals:
            assert 0 <= portal.quality_score <= 1
            assert 0 <= portal.darkness_ratio <= 1
            assert 0 <= portal.edge_strength <= 1
            assert 0 <= portal.confidence <= 1


class TestPortalMatch:
    """Test PortalMatch functionality."""
    
    def test_portal_match_creation(self):
        """Test creating portal match."""
        p1 = Portal("circle", (0.3, 0.5), (0.2, 0.2), 0.9, 0.8, 0.7)
        p2 = Portal("circle", (0.7, 0.5), (0.2, 0.2), 0.9, 0.8, 0.7)
        
        match = PortalMatch(
            portal1=p1,
            portal2=p2,
            alignment_score=0.6,
            size_compatibility=0.9,
            transition_type="zoom_through"
        )
        
        assert match.portal1 == p1
        assert match.portal2 == p2
        assert match.alignment_score == 0.6
        assert match.size_compatibility == 0.9
        assert match.transition_type == "zoom_through"
    
    def test_overall_score(self):
        """Test overall match score calculation."""
        p1 = Portal("circle", (0.5, 0.5), (0.3, 0.3), 0.9, 0.8, 0.9)
        p2 = Portal("circle", (0.5, 0.5), (0.3, 0.3), 0.9, 0.8, 0.9)
        
        match = PortalMatch(
            portal1=p1,
            portal2=p2,
            alignment_score=1.0,  # Perfect alignment
            size_compatibility=1.0,  # Same size
            transition_type="direct_portal"
        )
        
        # Should have high overall score
        assert match.overall_score > 0.8


class TestPortalEffectGenerator:
    """Test PortalEffectGenerator functionality."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = PortalEffectGenerator()
        assert hasattr(generator, 'detector')
        assert isinstance(generator.detector, PortalDetector)
    
    def test_analyze_portal_transition(self, portal_images):
        """Test analyzing portal transition between images."""
        generator = PortalEffectGenerator()
        
        # Analyze transition from circle to rectangle portal
        analysis = generator.analyze_portal_transition(
            portal_images[0],  # Circle portal
            portal_images[1]   # Rectangle portal
        )
        
        assert isinstance(analysis, PortalEffectAnalysis)
        assert len(analysis.portals_shot1) > 0
        assert len(analysis.portals_shot2) > 0
        assert analysis.recommended_effect in [
            "direct_portal", "zoom_spiral", "zoom_blur", "portal_wipe", "cross_fade"
        ]
    
    def test_portal_matching(self, portal_images):
        """Test portal matching between shots."""
        generator = PortalEffectGenerator()
        
        # Use same image for perfect match
        analysis = generator.analyze_portal_transition(
            portal_images[0],
            portal_images[0]
        )
        
        if analysis.best_match:
            # Should have high alignment for same image
            assert analysis.best_match.alignment_score > 0.9
    
    def test_transition_mask_generation(self):
        """Test transition mask generation."""
        generator = PortalEffectGenerator()
        
        portal = Portal(
            shape_type="circle",
            center=(0.5, 0.5),
            size=(0.4, 0.4),
            confidence=1.0,
            darkness_ratio=0.8,
            edge_strength=0.9
        )
        
        mask = generator._generate_transition_mask(
            portal,
            (480, 640)
        )
        
        assert mask.shape == (480, 640)
        assert mask.dtype == np.float32
        assert np.max(mask) <= 1.0
        assert np.min(mask) >= 0.0
        
        # Center should be brightest
        center_value = mask[240, 320]
        assert center_value > 0.8
    
    def test_analysis_to_dict(self, portal_images):
        """Test serialization of portal analysis."""
        generator = PortalEffectGenerator()
        
        analysis = generator.analyze_portal_transition(
            portal_images[0],
            portal_images[1]
        )
        
        data = analysis.to_dict()
        
        assert "shot1_portals" in data
        assert "shot2_portals" in data
        assert "best_match" in data
        assert "recommended_effect" in data
        assert "total_matches" in data
        
        # Check structure
        assert isinstance(data["shot1_portals"], list)
        assert isinstance(data["shot2_portals"], list)


class TestPortalExport:
    """Test export functionality."""
    
    def test_export_after_effects(self, portal_images):
        """Test After Effects export."""
        generator = PortalEffectGenerator()
        
        analysis = generator.analyze_portal_transition(
            portal_images[0],
            portal_images[1]
        )
        
        with tempfile.NamedTemporaryFile(suffix='.jsx', delete=False) as tmp:
            export_portal_effect(analysis, Path(tmp.name), format='after_effects')
            
            # Verify file was created
            assert Path(tmp.name).exists()
            
            content = Path(tmp.name).read_text()
            assert "Portal Effect Transition" in content
            assert "AliceMultiverse" in content
            
            if analysis.best_match:
                assert "portal1_center" in content
                assert "portal2_center" in content
                assert "effect_type" in content
            
            # Cleanup
            Path(tmp.name).unlink()
    
    def test_export_json(self, portal_images):
        """Test JSON export."""
        generator = PortalEffectGenerator()
        
        analysis = generator.analyze_portal_transition(
            portal_images[0],
            portal_images[1]
        )
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_portal_effect(analysis, Path(tmp.name), format='json')
            
            # Verify file was created and is valid JSON
            assert Path(tmp.name).exists()
            
            with open(tmp.name) as f:
                data = json.load(f)
            
            assert "shot1_portals" in data
            assert "shot2_portals" in data
            
            # Cleanup
            Path(tmp.name).unlink()