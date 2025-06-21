"""Unit tests for CLI module."""

from unittest.mock import MagicMock, patch

import pytest

from alicemultiverse.interface.main_cli import (
    apply_cli_args_to_config,
    create_parser,
    main,
    parse_cli_overrides,
)


class TestCLIParsing:
    """Test command-line argument parsing."""

    @pytest.mark.unit
    def test_create_parser_structure(self):
        """Test that parser is created with expected structure."""
        parser = create_parser()

        # Check parser has expected attributes
        assert parser.description
        assert parser.epilog

        # Parse empty args should work
        args = parser.parse_args([])
        assert hasattr(args, "command")

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "args,expected",
        [
            (["--inbox", "/test/path"], {"inbox": "/test/path"}),
            (["-i", "/test/path"], {"inbox": "/test/path"}),
            (["--output", "/out/path"], {"output": "/out/path"}),
            (["-o", "/out/path"], {"output": "/out/path"}),
            (["--quality"], {"quality": True}),
            (["-Q"], {"quality": True}),
            (["--watch"], {"watch": True}),
            (["-w"], {"watch": True}),
            (["--move"], {"move": True}),
            (["-m"], {"move": True}),
            (["--dry-run"], {"dry_run": True}),
            (["-n"], {"dry_run": True}),
        ],
    )
    def test_parse_arguments(self, args, expected):
        """Test parsing various command-line arguments."""
        parser = create_parser()
        parsed = parser.parse_args(args)

        for key, value in expected.items():
            assert getattr(parsed, key, None) == value

    @pytest.mark.unit
    def test_parse_keys_subcommand(self):
        """Test parsing keys subcommand."""
        parser = create_parser()

        # Test keys setup
        args = parser.parse_args(["keys", "setup"])
        assert args.command == "keys"
        assert args.keys_command == "setup"

        # Test keys set
        args = parser.parse_args(["keys", "set", "anthropic_api_key", "--method", "keychain"])
        assert args.command == "keys"
        assert args.keys_command == "set"
        assert args.key_name == "anthropic_api_key"
        assert args.method == "keychain"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "cli_args,expected_overrides",
        [
            (["--paths.inbox=/test"], ["paths.inbox=/test"]),
            (["--quality.thresholds.3_star.max=70"], ["quality.thresholds.3_star.max=70"]),
            (
                ["--paths.inbox=/test", "--processing.quality=true"],
                ["paths.inbox=/test", "processing.quality=true"],
            ),
            (["--pipeline", "basic"], []),  # Regular args shouldn't be in overrides
            (["-i", "/test"], []),  # Short form args shouldn't be in overrides
        ],
    )
    def test_parse_cli_overrides(self, cli_args, expected_overrides):
        """Test extraction of OmegaConf-style overrides."""
        overrides = parse_cli_overrides(cli_args)
        assert overrides == expected_overrides

    @pytest.mark.unit
    def test_apply_cli_args_to_config(self):
        """Test applying CLI arguments to configuration."""
        from alicemultiverse.core.config_dataclass import Config
        
        # Create a dataclass config
        config = Config()
        
        # Create mock args with concrete values
        class MockArgs:
            pass
        
        args = MockArgs()
        args.inbox = "/cli/inbox"
        args.output = "/cli/output"
        args.move = True
        args.quality = True
        args.watch = True
        args.dry_run = True
        args.force_reindex = True
        args.understand = True
        args.providers = None
        args.pipeline = None
        args.stages = None
        args.cost_limit = None
        args.enhanced_metadata = None
        args.openai_api_key = None
        args.anthropic_api_key = None
        args.google_ai_api_key = None
        args.deepseek_api_key = None
        args.detailed = None
        args.verbose = None
        args.debug = None
        args.quiet = None
        args.json = None
        args.log_file = None
        args.no_color = None

        apply_cli_args_to_config(config, args)

        assert config.paths.inbox == "/cli/inbox"
        assert config.paths.organized == "/cli/output"
        assert config.processing.copy_mode is False  # move = True means copy_mode = False
        assert config.processing.quality is True
        assert config.processing.watch is True
        assert config.processing.dry_run is True
        assert config.processing.force_reindex is True
        assert config.understanding.enabled is True


class TestCLIMain:
    """Test main CLI entry point."""

    @pytest.mark.unit
    def test_main_version(self, capsys):
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "1.7.1" in captured.out

    @pytest.mark.unit
    @patch("alicemultiverse.interface.main_cli.handle_keys_command")
    @patch("alicemultiverse.interface.main_cli.load_config")
    def test_main_keys_command(self, mock_load_config, mock_handle_keys):
        """Test keys subcommand routing."""
        from alicemultiverse.core.config_dataclass import Config
        
        mock_load_config.return_value = Config()
        mock_handle_keys.return_value = 0

        result = main(["keys", "list"])

        assert result == 0
        mock_handle_keys.assert_called_once()

    @pytest.mark.unit
    @patch("alicemultiverse.interface.main_cli.check_dependencies")
    def test_main_check_deps(self, mock_check_deps):
        """Test --check-deps flag."""
        mock_check_deps.return_value = True

        result = main(["--check-deps"])

        assert result == 0
        mock_check_deps.assert_called_once()

    @pytest.mark.unit
    @patch("alicemultiverse.interface.main_cli.load_config")
    @patch("alicemultiverse.organizer.run_organizer")
    def test_main_dry_run(self, mock_run_organizer, mock_load_config, omega_config, temp_dir):
        """Test dry run mode."""
        # Setup mocks
        mock_load_config.return_value = omega_config
        mock_run_organizer.return_value = True

        # Create inbox directory
        inbox = temp_dir / "inbox"
        inbox.mkdir()

        result = main(["--debug", "--dry-run"])

        assert result == 0
        mock_run_organizer.assert_called_once()

        # Check that dry_run was set in config
        call_args = mock_run_organizer.call_args[0]
        config = call_args[0]
        assert config.processing.dry_run is True

    @pytest.mark.unit
    def test_main_missing_inbox(self, temp_dir):
        """Test error when inbox directory doesn't exist."""
        result = main(["--inbox", str(temp_dir / "nonexistent")])
        assert result == 1

    @pytest.mark.unit
    @patch("alicemultiverse.interface.main_cli.load_config")
    def test_main_keyboard_interrupt(self, mock_load_config, omega_config, temp_dir):
        """Test handling of keyboard interrupt."""
        inbox = temp_dir / "inbox"
        inbox.mkdir()

        # Setup proper config
        mock_load_config.return_value = omega_config

        with patch("alicemultiverse.organizer.run_organizer", side_effect=KeyboardInterrupt):
            result = main(["--debug", "--inbox", str(inbox)])

        assert result == 130  # Standard exit code for Ctrl+C

    @pytest.mark.unit
    @patch("alicemultiverse.organizer.run_organizer")
    def test_main_pipeline_args(self, mock_run_organizer, omega_config, temp_dir):
        """Test pipeline-related arguments are passed correctly."""
        mock_run_organizer.return_value = True

        inbox = temp_dir / "inbox"
        inbox.mkdir()

        with patch("alicemultiverse.interface.main_cli.load_config", return_value=omega_config):
            result = main(
                [
                    "--debug",
                    "--inbox",
                    str(inbox),
                    "--pipeline",
                    "premium",
                    "--stages",
                    "brisque,sightengine",
                    "--cost-limit",
                    "25.0",
                ]
            )

        assert result == 0

        # Check arguments passed to run_organizer
        call_args = mock_run_organizer.call_args[0]
        assert call_args[1] == "premium"  # pipeline
        assert call_args[2] == "brisque,sightengine"  # stages
        assert call_args[3] == 25.0  # cost_limit
