"""Tests for MediaOrganizer class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from alicemultiverse.core.types import MediaType
from alicemultiverse.organizer.media_organizer import MediaOrganizer


class TestMediaOrganizer:
    """Test MediaOrganizer functionality."""

    def test_project_folder_detection(self, omega_config, temp_dir):
        """Test that only top-level folders are treated as projects."""
        # Setup
        inbox = temp_dir / "inbox"
        project = inbox / "alice-1"
        subfolder = project / "renders" / "final"
        subfolder.mkdir(parents=True)

        # Create files at different levels
        files = [
            project / "image1.jpg",
            project / "renders" / "image2.jpg",
            subfolder / "image3.jpg",
            inbox / "loose_file.jpg",  # File directly in inbox
        ]

        for f in files:
            f.write_text("fake image")

        # Configure
        omega_config.paths.inbox = str(inbox)
        omega_config.paths.organized = str(temp_dir / "organized")

        # Mock quality assessor
        with patch(
            "alicemultiverse.organizer.media_organizer.brisque_available", return_value=False
        ):
            organizer = MediaOrganizer(omega_config)

            # Process files
            results = []
            for f in files[:-1]:  # First 3 files in alice-1
                result = organizer._process_file(f)
                results.append(result)
                assert (
                    result["project_folder"] == "alice-1"
                ), f"File {f} should be in alice-1 project"

            # Process loose file
            result = organizer._process_file(files[-1])
            assert result["project_folder"] == "uncategorized", "Loose file should be uncategorized"

    def test_find_media_files(self, omega_config, temp_dir):
        """Test media file discovery."""
        # Setup directory structure
        inbox = temp_dir / "inbox"
        project1 = inbox / "project1"
        project2 = inbox / "project2"
        hidden = inbox / ".hidden"

        for d in [project1, project2, hidden]:
            d.mkdir(parents=True)

        # Create various files
        (project1 / "image.jpg").write_text("fake")
        (project1 / "video.mp4").write_text("fake")
        (project2 / "image.png").write_text("fake")
        (hidden / "hidden.jpg").write_text("fake")  # Should be ignored
        (inbox / "readme.txt").write_text("text")  # Should be ignored

        omega_config.paths.inbox = str(inbox)

        with patch(
            "alicemultiverse.organizer.media_organizer.brisque_available", return_value=False
        ):
            organizer = MediaOrganizer(omega_config)
            files = organizer._find_media_files()

        # Should find 3 media files, not hidden or non-media
        assert len(files) == 3
        filenames = [f.name for f in files]
        assert "image.jpg" in filenames
        assert "video.mp4" in filenames
        assert "image.png" in filenames
        assert "hidden.jpg" not in filenames
        assert "readme.txt" not in filenames

    def test_media_type_detection(self, omega_config):
        """Test media type detection."""
        with patch(
            "alicemultiverse.organizer.media_organizer.brisque_available", return_value=False
        ):
            organizer = MediaOrganizer(omega_config)

        # Test supported extensions
        assert organizer._get_media_type(Path("test.jpg")) == MediaType.IMAGE
        assert organizer._get_media_type(Path("test.JPG")) == MediaType.IMAGE
        assert organizer._get_media_type(Path("test.png")) == MediaType.IMAGE
        assert organizer._get_media_type(Path("test.mp4")) == MediaType.VIDEO
        assert organizer._get_media_type(Path("test.MP4")) == MediaType.VIDEO
        assert organizer._get_media_type(Path("test.mov")) == MediaType.VIDEO

        # Test unsupported formats
        assert organizer._get_media_type(Path("test.gif")) == MediaType.UNKNOWN
        assert organizer._get_media_type(Path("test.webp")) == MediaType.UNKNOWN
        assert organizer._get_media_type(Path("test.txt")) == MediaType.UNKNOWN

    def test_duplicate_prevention_quality_mode(self, omega_config, temp_dir):
        """Test that switching between quality modes doesn't create duplicates."""
        # Setup
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        project = inbox / "test-project"
        project.mkdir(parents=True)

        # Create a test image
        test_image = project / "image.jpg"
        test_image.write_bytes(b"fake image data")

        omega_config.paths.inbox = str(inbox)
        omega_config.paths.organized = str(organized)

        # Mock file operations and quality
        with patch(
            "alicemultiverse.organizer.media_organizer.brisque_available", return_value=True
        ):
            with patch("alicemultiverse.organizer.media_organizer.BRISQUEAssessor") as mock_brisque:
                # First run without quality
                omega_config.processing.quality = False
                organizer = MediaOrganizer(omega_config)

                # Mock the file handler to track operations
                with patch.object(organizer.file_handler, "move_file") as mock_move:
                    with patch.object(organizer.file_handler, "copy_file") as mock_copy:
                        with patch.object(
                            organizer.file_handler, "files_are_identical", return_value=True
                        ):
                            # Process without quality
                            result1 = organizer._process_file(test_image)
                            assert result1["status"] == "success"

                            # Now process with quality (should move existing file)
                            mock_assessor = MagicMock()
                            mock_assessor.assess_quality.return_value = (30.0, 4)
                            mock_brisque.return_value = mock_assessor
                            omega_config.processing.quality = True

                            organizer2 = MediaOrganizer(omega_config)
                            organizer2.quality_assessor = mock_assessor
                            organizer2.quality_enabled = True

                            # Should find and move the existing file
                            result2 = organizer2._process_file(test_image)

                            # Verify it tried to move the existing file to quality folder
                            if result2["quality_stars"] is not None:
                                # Should have detected the need to move
                                assert mock_move.called or mock_copy.called
