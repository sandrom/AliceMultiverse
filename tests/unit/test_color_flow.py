"""
Unit tests for color flow transitions.
"""

import pytest
import numpy as np
from PIL import Image
import tempfile
import json
from pathlib import Path

from alicemultiverse.transitions.color_flow import (
    ColorFlowAnalyzer,
    ColorPalette,
    LightingInfo,
    GradientTransition,
    ColorFlowAnalysis,
    analyze_sequence,
    export_analysis_for_editor
)


@pytest.fixture
def sample_images():
    """Create sample test images with different color properties."""
    images = []
    
    # Image 1: Warm, bright image (sunset)
    img1 = Image.new('RGB', (640, 480), color=(255, 150, 50))  # Orange
    draw1 = np.array(img1)
    # Add gradient for lighting detection
    for y in range(480):
        for x in range(640):
            draw1[y, x] = [
                min(255, 255 - y // 3),  # R decreases vertically
                min(255, 150 - y // 4),  # G decreases vertically
                min(255, 50 + x // 5)    # B increases horizontally
            ]
    img1 = Image.fromarray(draw1.astype(np.uint8))
    
    # Image 2: Cool, darker image (night)
    img2 = Image.new('RGB', (640, 480), color=(50, 50, 150))  # Blue
    draw2 = np.array(img2)
    # Add different gradient pattern
    for y in range(480):
        for x in range(640):
            draw2[y, x] = [
                min(255, 50 + y // 8),   # R increases vertically
                min(255, 50 + y // 8),   # G increases vertically
                min(255, 150 + x // 6)   # B increases horizontally
            ]
    img2 = Image.fromarray(draw2.astype(np.uint8))
    
    # Image 3: Neutral, medium brightness
    img3 = Image.new('RGB', (640, 480), color=(128, 128, 128))  # Gray
    draw3 = np.array(img3)
    # Add radial gradient
    center_x, center_y = 320, 240
    for y in range(480):
        for x in range(640):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            intensity = max(0, 255 - int(dist / 2))
            draw3[y, x] = [intensity, intensity, intensity]
    img3 = Image.fromarray(draw3.astype(np.uint8))
    
    # Save to temporary files
    for i, img in enumerate([img1, img2, img3]):
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(tmp.name)
        images.append(tmp.name)
        tmp.close()
    
    yield images
    
    # Cleanup
    for img_path in images:
        Path(img_path).unlink(missing_ok=True)


class TestColorFlowAnalyzer:
    """Test ColorFlowAnalyzer functionality."""
    
    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = ColorFlowAnalyzer(n_colors=5)
        assert analyzer.n_colors == 5
    
    def test_analyze_shot_pair(self, sample_images):
        """Test analyzing a pair of shots."""
        analyzer = ColorFlowAnalyzer()
        analysis = analyzer.analyze_shot_pair(
            sample_images[0], 
            sample_images[1],
            transition_duration=30
        )
        
        assert isinstance(analysis, ColorFlowAnalysis)
        assert analysis.compatibility_score >= 0.0
        assert analysis.compatibility_score <= 1.0
        assert len(analysis.suggested_effects) > 0
        assert analysis.gradient_transition.duration_frames == 30
    
    def test_color_palette_extraction(self, sample_images):
        """Test color palette extraction."""
        analyzer = ColorFlowAnalyzer()
        img = analyzer._load_image(sample_images[0])
        palette = analyzer._extract_color_palette(img)
        
        assert isinstance(palette, ColorPalette)
        assert len(palette.dominant_colors) == analyzer.n_colors
        assert len(palette.color_weights) == analyzer.n_colors
        assert 0.0 <= palette.average_brightness <= 1.0
        assert 0.0 <= palette.average_saturation <= 1.0
        assert 0.0 <= palette.color_temperature <= 1.0
        assert sum(palette.color_weights) == pytest.approx(1.0, rel=0.01)
    
    def test_lighting_analysis(self, sample_images):
        """Test lighting analysis."""
        analyzer = ColorFlowAnalyzer()
        img = analyzer._load_image(sample_images[0])
        lighting = analyzer._analyze_lighting(img)
        
        assert isinstance(lighting, LightingInfo)
        assert len(lighting.direction) == 2
        assert -1.0 <= lighting.direction[0] <= 1.0
        assert -1.0 <= lighting.direction[1] <= 1.0
        assert 0.0 <= lighting.intensity <= 1.0
        assert lighting.type in ['directional', 'ambient', 'mixed']
        assert 0.0 <= lighting.shadow_density <= 1.0
    
    def test_gradient_transition_creation(self, sample_images):
        """Test gradient transition creation."""
        analyzer = ColorFlowAnalyzer()
        
        # Get palettes and lighting
        img1 = analyzer._load_image(sample_images[0])
        img2 = analyzer._load_image(sample_images[1])
        palette1 = analyzer._extract_color_palette(img1)
        palette2 = analyzer._extract_color_palette(img2)
        lighting1 = analyzer._analyze_lighting(img1)
        lighting2 = analyzer._analyze_lighting(img2)
        
        # Create transition
        gradient = analyzer._create_gradient_transition(
            palette1, palette2, lighting1, lighting2, 30
        )
        
        assert isinstance(gradient, GradientTransition)
        assert len(gradient.start_colors) == 3
        assert len(gradient.end_colors) == 3
        assert gradient.duration_frames == 30
        assert gradient.transition_type in ['linear', 'radial', 'diagonal']
        assert gradient.blend_curve in ['linear', 'ease-in', 'ease-out', 'ease-in-out']
        assert gradient.mask_data is not None
    
    def test_compatibility_calculation(self, sample_images):
        """Test compatibility score calculation."""
        analyzer = ColorFlowAnalyzer()
        
        # Analyze warm to cool transition (should have lower compatibility)
        analysis1 = analyzer.analyze_shot_pair(sample_images[0], sample_images[1])
        
        # Analyze similar images (should have higher compatibility)
        analysis2 = analyzer.analyze_shot_pair(sample_images[2], sample_images[2])
        
        assert analysis1.compatibility_score < analysis2.compatibility_score
        assert 0.0 <= analysis1.compatibility_score <= 1.0
        assert 0.0 <= analysis2.compatibility_score <= 1.0
    
    def test_effect_suggestions(self, sample_images):
        """Test effect suggestions based on analysis."""
        analyzer = ColorFlowAnalyzer()
        
        # Analyze warm to cool transition
        analysis = analyzer.analyze_shot_pair(sample_images[0], sample_images[1])
        
        # Should suggest color temperature shift for warm to cool
        assert 'color_temperature_shift' in analysis.suggested_effects
        
        # Should always suggest gradient wipe and color match
        assert 'gradient_wipe' in analysis.suggested_effects
        assert 'color_match' in analysis.suggested_effects
    
    def test_transition_mask_creation(self):
        """Test transition mask creation."""
        analyzer = ColorFlowAnalyzer()
        
        # Test linear mask
        linear_mask = analyzer._create_transition_mask('linear', (100, 100))
        assert linear_mask.shape == (100, 100)
        assert np.all(linear_mask >= 0.0) and np.all(linear_mask <= 1.0)
        
        # Test radial mask
        radial_mask = analyzer._create_transition_mask('radial', (100, 100))
        assert radial_mask.shape == (100, 100)
        assert np.all(radial_mask >= 0.0) and np.all(radial_mask <= 1.0)
        
        # Test diagonal mask
        diagonal_mask = analyzer._create_transition_mask('diagonal', (100, 100))
        assert diagonal_mask.shape == (100, 100)
        assert np.all(diagonal_mask >= 0.0) and np.all(diagonal_mask <= 1.0)
    
    def test_color_distance_calculation(self):
        """Test color distance calculation."""
        analyzer = ColorFlowAnalyzer()
        
        # Same color should have distance 0
        assert analyzer._color_distance((100, 150, 200), (100, 150, 200)) == 0.0
        
        # Black to white should have maximum distance
        dist = analyzer._color_distance((0, 0, 0), (255, 255, 255))
        assert dist == pytest.approx(441.67, rel=0.01)
    
    def test_to_dict_serialization(self, sample_images):
        """Test serialization to dictionary."""
        analyzer = ColorFlowAnalyzer()
        analysis = analyzer.analyze_shot_pair(sample_images[0], sample_images[1])
        
        # Convert to dict
        data = analysis.to_dict()
        
        # Check structure
        assert 'shot1_palette' in data
        assert 'shot2_palette' in data
        assert 'shot1_lighting' in data
        assert 'shot2_lighting' in data
        assert 'gradient_transition' in data
        assert 'compatibility_score' in data
        assert 'suggested_effects' in data
        
        # Should be JSON serializable
        json_str = json.dumps(data)
        assert len(json_str) > 0


class TestSequenceAnalysis:
    """Test sequence analysis functionality."""
    
    def test_analyze_sequence(self, sample_images):
        """Test analyzing a sequence of images."""
        analyses = analyze_sequence(sample_images, transition_duration=24)
        
        # Should have n-1 transitions for n images
        assert len(analyses) == len(sample_images) - 1
        
        # Each should be a valid analysis
        for analysis in analyses:
            assert isinstance(analysis, ColorFlowAnalysis)
            assert analysis.gradient_transition.duration_frames == 24
    
    def test_sequence_export(self, sample_images):
        """Test exporting sequence analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "sequence.json"
            
            analyses = analyze_sequence(
                sample_images, 
                transition_duration=30,
                export_path=str(export_path)
            )
            
            # Check export file exists
            assert export_path.exists()
            
            # Load and verify structure
            with open(export_path) as f:
                data = json.load(f)
            
            assert 'sequence' in data
            assert 'metadata' in data
            assert data['metadata']['shot_count'] == len(sample_images)
            assert data['metadata']['transition_count'] == len(analyses)


class TestEditorExports:
    """Test editor-specific export functionality."""
    
    def test_resolve_export(self, sample_images):
        """Test DaVinci Resolve export."""
        analyzer = ColorFlowAnalyzer()
        analysis = analyzer.analyze_shot_pair(sample_images[0], sample_images[1])
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_analysis_for_editor(analysis, tmp.name, 'resolve')
            
            # Verify file exists and has correct structure
            with open(tmp.name) as f:
                data = json.load(f)
            
            assert 'ColorFlowTransition' in data
            assert 'SourceColors' in data['ColorFlowTransition']
            assert 'TargetColors' in data['ColorFlowTransition']
            assert 'Duration' in data['ColorFlowTransition']
            assert 'LightingMatch' in data['ColorFlowTransition']
            
            Path(tmp.name).unlink()
    
    def test_premiere_export(self, sample_images):
        """Test Adobe Premiere export."""
        analyzer = ColorFlowAnalyzer()
        analysis = analyzer.analyze_shot_pair(sample_images[0], sample_images[1])
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_analysis_for_editor(analysis, tmp.name, 'premiere')
            
            with open(tmp.name) as f:
                data = json.load(f)
            
            assert 'ColorFlowEffect' in data
            assert 'parameters' in data['ColorFlowEffect']
            assert 'keyframes' in data['ColorFlowEffect']
            
            Path(tmp.name).unlink()
    
    def test_fcpx_export(self, sample_images):
        """Test Final Cut Pro X export."""
        analyzer = ColorFlowAnalyzer()
        analysis = analyzer.analyze_shot_pair(sample_images[0], sample_images[1])
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_analysis_for_editor(analysis, tmp.name, 'fcpx')
            
            with open(tmp.name) as f:
                data = json.load(f)
            
            assert 'generator' in data
            assert 'parameters' in data['generator']
            
            Path(tmp.name).unlink()
    
    def test_fusion_export(self, sample_images):
        """Test Blackmagic Fusion export."""
        analyzer = ColorFlowAnalyzer()
        analysis = analyzer.analyze_shot_pair(sample_images[0], sample_images[1])
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_analysis_for_editor(analysis, tmp.name, 'fusion')
            
            with open(tmp.name) as f:
                data = json.load(f)
            
            assert 'Tools' in data
            assert 'ColorFlowGradient' in data['Tools']
            assert 'ColorCorrector' in data['Tools']
            assert 'Merge' in data['Tools']
            
            Path(tmp.name).unlink()
    
    def test_lut_generation(self, sample_images):
        """Test LUT generation for color matching."""
        analyzer = ColorFlowAnalyzer()
        
        # Create analysis with low compatibility (to trigger LUT generation)
        analysis = analyzer.analyze_shot_pair(sample_images[0], sample_images[1])
        analysis.compatibility_score = 0.5  # Force low score
        
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "transition.json"
            export_analysis_for_editor(analysis, str(export_path), 'resolve')
            
            # Check if LUT was generated
            lut_path = export_path.with_suffix('.cube')
            if analysis.compatibility_score < 0.7:
                assert lut_path.exists()
                
                # Verify LUT format
                with open(lut_path) as f:
                    content = f.read()
                    assert 'TITLE' in content
                    assert 'LUT_3D_SIZE' in content