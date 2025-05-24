"""Basic tests for Asset Processor service."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from asset_processor import (
    AssetAnalyzer,
    QualityPipeline,
    AssetOrganizer,
    AnalyzeResponse,
    QualityAssessResponse,
    OrganizePlanResponse
)
from alice_models import MediaType, QualityRating, SourceType


class TestAssetAnalyzer:
    """Test asset analyzer functionality."""
    
    @pytest.mark.asyncio
    async def test_analyze_image(self, tmp_path):
        """Test analyzing an image file."""
        # Create a test file
        test_file = tmp_path / "test_image.jpg"
        test_file.write_bytes(b"fake image data")
        
        # Mock the utility functions
        with patch('asset_processor.analyzer.compute_file_hash', return_value="abc123"):
            with patch('asset_processor.analyzer.detect_media_type', return_value=MediaType.IMAGE):
                with patch('asset_processor.analyzer.get_file_info') as mock_info:
                    mock_info.return_value = {
                        "name": "test_image.jpg",
                        "size": 100,
                        "created": "2024-01-01T00:00:00",
                        "modified": "2024-01-01T00:00:00"
                    }
                    
                    with patch('asset_processor.analyzer.extract_image_metadata') as mock_metadata:
                        mock_metadata.return_value = {
                            "width": 1024,
                            "height": 768,
                            "info": {
                                "parameters": "a beautiful landscape, Steps: 20, Sampler: DPM++, CFG scale: 7.5"
                            }
                        }
                        
                        analyzer = AssetAnalyzer()
                        result = await analyzer.analyze(test_file)
                        
                        assert isinstance(result, AnalyzeResponse)
                        assert result.content_hash == "abc123"
                        assert result.media_type == MediaType.IMAGE
                        assert result.dimensions == {"width": 1024, "height": 768}
                        assert result.ai_source == SourceType.STABLE_DIFFUSION
                        assert "steps" in result.generation_params
                        assert result.generation_params["steps"] == 20


class TestQualityPipeline:
    """Test quality assessment pipeline."""
    
    @pytest.mark.asyncio
    async def test_assess_basic(self, tmp_path):
        """Test basic quality assessment."""
        # Create a test file
        test_file = tmp_path / "test_image.jpg"
        test_file.write_bytes(b"fake image data")
        
        # Mock BRISQUE
        with patch('asset_processor.quality.BRISQUE_AVAILABLE', True):
            with patch('asset_processor.quality.QualityPipeline._assess_brisque') as mock_brisque:
                mock_brisque.return_value = 25.0  # Good quality
                
                pipeline = QualityPipeline()
                result = await pipeline.assess(test_file, "abc123", "basic")
                
                assert isinstance(result, QualityAssessResponse)
                assert result.brisque_score == 25.0
                assert result.combined_score == 0.75  # 1 - (25/100)
                assert result.star_rating == QualityRating.FOUR_STAR
                assert "brisque" in result.stages_completed


class TestAssetOrganizer:
    """Test asset organization planning."""
    
    @pytest.mark.asyncio
    async def test_plan_organization(self, tmp_path):
        """Test organization planning."""
        # Create a test file
        test_file = tmp_path / "projects" / "my_project" / "test_image.jpg"
        test_file.parent.mkdir(parents=True)
        test_file.write_bytes(b"fake image data")
        
        organizer = AssetOrganizer()
        
        # Mock sequence number lookup
        with patch.object(organizer, '_get_next_sequence_number', return_value=42):
            result = await organizer.plan_organization(
                test_file,
                "abc123",
                {
                    "created": "2024-03-15T10:00:00",
                    "ai_source": SourceType.STABLE_DIFFUSION
                },
                QualityRating.FIVE_STAR
            )
            
            assert isinstance(result, OrganizePlanResponse)
            assert result.date_folder == "2024-03-15"
            assert result.project_name == "my_project"
            assert result.source_type == "stable-diffusion"
            assert result.quality_folder == "5-star"
            assert result.sequence_number == 42
            assert result.suggested_filename == "my_project-00042.jpg"
            assert "2024-03-15/my_project/stable-diffusion/5-star" in result.destination_path


@pytest.mark.asyncio
async def test_service_integration():
    """Test service components work together."""
    # This would test the FastAPI endpoints
    # For now, just verify imports work
    from asset_processor.main import app
    assert app is not None