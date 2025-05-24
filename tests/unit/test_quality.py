"""Unit tests for quality assessment module."""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock, PropertyMock
from PIL import Image

from alicemultiverse.quality.brisque import (
    is_available, 
    calculate_brisque_score,
    get_quality_rating,
    ensure_rgb_image
)


class TestBrisqueAvailability:
    """Test BRISQUE availability detection."""
    
    @pytest.mark.unit
    @patch('alicemultiverse.quality.brisque.image_quality')
    def test_is_available_with_image_quality(self, mock_iq):
        """Test when image-quality package is available."""
        assert is_available() is True
    
    @pytest.mark.unit
    @patch('alicemultiverse.quality.brisque.image_quality', None)
    @patch('alicemultiverse.quality.brisque.pybrisque')
    def test_is_available_with_pybrisque(self, mock_pb):
        """Test when pybrisque package is available."""
        assert is_available() is True
    
    @pytest.mark.unit
    @patch('alicemultiverse.quality.brisque.image_quality', None)
    @patch('alicemultiverse.quality.brisque.pybrisque', None)
    def test_is_available_none(self):
        """Test when no BRISQUE package is available."""
        assert is_available() is False


class TestBrisqueScore:
    """Test BRISQUE score calculation."""
    
    @pytest.mark.unit
    def test_calculate_brisque_score_no_package(self):
        """Test score calculation when no package available."""
        with patch('alicemultiverse.quality.brisque.image_quality', None), \
             patch('alicemultiverse.quality.brisque.pybrisque', None):
            
            score = calculate_brisque_score("dummy_path")
            assert score is None
    
    @pytest.mark.unit
    @patch('alicemultiverse.quality.brisque.image_quality')
    @patch('PIL.Image.open')
    def test_calculate_brisque_score_with_image_quality(self, mock_open, mock_iq):
        """Test score calculation with image-quality package."""
        # Setup mock image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = 'RGB'
        mock_img.size = (100, 100)
        mock_img.width = 100
        mock_img.height = 100
        mock_open.return_value = mock_img
        
        # Setup mock BRISQUE to return score directly
        mock_iq.score.return_value = 25.5
        
        score = calculate_brisque_score("test.png")
        
        assert score == 25.5
        mock_iq.score.assert_called_once()
    
    @pytest.mark.unit
    @patch('alicemultiverse.quality.brisque.image_quality', None)
    @patch('alicemultiverse.quality.brisque.pybrisque')
    @patch('cv2.imread')
    def test_calculate_brisque_score_with_pybrisque(self, mock_imread, mock_pb):
        """Test score calculation with pybrisque package."""
        # Setup mock pybrisque.brisque function
        mock_pb.brisque.return_value = 30.0
        
        score = calculate_brisque_score("test.png")
        
        assert score == 30.0
        mock_pb.brisque.assert_called_once_with("test.png")
    
    @pytest.mark.unit
    @patch('alicemultiverse.quality.brisque.image_quality')
    @patch('PIL.Image.open')
    def test_calculate_brisque_score_with_grayscale(self, mock_open, mock_iq):
        """Test score calculation with grayscale image."""
        # Setup mock grayscale image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = 'L'
        mock_img.width = 100
        mock_img.height = 100
        mock_converted = MagicMock(spec=Image.Image)
        mock_converted.mode = 'RGB'
        mock_converted.width = 100
        mock_converted.height = 100
        mock_img.convert.return_value = mock_converted
        mock_open.return_value = mock_img
        
        # Setup mock BRISQUE
        mock_iq.score.return_value = 40.0
        
        score = calculate_brisque_score("test.png")
        
        assert score == 40.0
        mock_img.convert.assert_called_with('RGB')
    
    @pytest.mark.unit
    @patch('alicemultiverse.quality.brisque.image_quality')
    @patch('PIL.Image.open')
    def test_calculate_brisque_score_error_handling(self, mock_open, mock_iq):
        """Test error handling in score calculation."""
        # Setup image open to raise exception
        mock_open.side_effect = IOError("Cannot open file")
        
        score = calculate_brisque_score("test.png")
        
        assert score is None


class TestQualityRating:
    """Test quality rating determination."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("score,expected_stars", [
        (10.0, 5),   # Excellent
        (20.0, 5),   # Still 5-star
        (25.0, 4),   # Good
        (40.0, 4),   # Still 4-star
        (45.0, 3),   # Average
        (60.0, 3),   # Still 3-star
        (65.0, 2),   # Below average
        (75.0, 2),   # Still 2-star
        (80.0, 1),   # Poor
        (95.0, 1),   # Still 1-star
        (None, None),  # No score
    ])
    def test_get_quality_rating(self, score, expected_stars):
        """Test quality rating based on BRISQUE score."""
        # Create mock config with default thresholds
        config = {
            "quality": {
                "thresholds": {
                    "5_star": {"min": 0, "max": 25},
                    "4_star": {"min": 25, "max": 45},
                    "3_star": {"min": 45, "max": 65},
                    "2_star": {"min": 65, "max": 80},
                    "1_star": {"min": 80, "max": 100}
                }
            }
        }
        
        stars = get_quality_rating(score, config)
        assert stars == expected_stars
    
    @pytest.mark.unit
    def test_get_quality_rating_custom_thresholds(self):
        """Test quality rating with custom thresholds."""
        config = {
            "quality": {
                "thresholds": {
                    "5_star": {"min": 0, "max": 30},
                    "4_star": {"min": 30, "max": 50},
                    "3_star": {"min": 50, "max": 70},
                    "2_star": {"min": 70, "max": 85},
                    "1_star": {"min": 85, "max": 100}
                }
            }
        }
        
        assert get_quality_rating(25.0, config) == 5
        assert get_quality_rating(35.0, config) == 4
        assert get_quality_rating(55.0, config) == 3
        assert get_quality_rating(75.0, config) == 2
        assert get_quality_rating(90.0, config) == 1


class TestImageConversion:
    """Test image conversion utilities."""
    
    @pytest.mark.unit
    def test_ensure_rgb_image_already_rgb(self):
        """Test RGB image passes through unchanged."""
        img = MagicMock(spec=Image.Image)
        img.mode = 'RGB'
        
        result = ensure_rgb_image(img)
        
        assert result == img
        img.convert.assert_not_called()
    
    @pytest.mark.unit
    @pytest.mark.parametrize("mode", ['L', 'LA', 'P', 'CMYK'])
    def test_ensure_rgb_image_conversion(self, mode):
        """Test non-RGB images are converted."""
        img = MagicMock(spec=Image.Image)
        img.mode = mode
        converted = MagicMock(spec=Image.Image)
        converted.mode = 'RGB'
        img.convert.return_value = converted
        
        result = ensure_rgb_image(img)
        
        assert result == converted
        img.convert.assert_called_once_with('RGB')
    
    @pytest.mark.unit
    def test_ensure_rgb_image_rgba_handling(self):
        """Test RGBA image handling with alpha channel."""
        img = MagicMock(spec=Image.Image)
        img.mode = 'RGBA'
        img.size = (100, 100)
        
        # Mock the split to return alpha channel
        alpha_channel = MagicMock()
        img.split.return_value = [MagicMock(), MagicMock(), MagicMock(), alpha_channel]
        
        # Mock the creation of white background
        with patch('PIL.Image.new') as mock_new:
            background = MagicMock(spec=Image.Image)
            background.mode = 'RGB'
            mock_new.return_value = background
            
            result = ensure_rgb_image(img)
            
            mock_new.assert_called_once_with('RGB', (100, 100), (255, 255, 255))
            background.paste.assert_called_once_with(img, mask=alpha_channel)
            assert result == background