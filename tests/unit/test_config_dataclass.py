"""Unit tests for dataclass configuration module."""

import pytest
from pathlib import Path
import tempfile
import yaml

from alicemultiverse.core.config_dataclass import (
    Config, PathsConfig, ProcessingConfig, load_config, get_default_config
)
from alicemultiverse.core.exceptions import ConfigurationError


class TestDataclassConfig:
    """Test dataclass configuration implementation."""
    
    @pytest.mark.unit
    def test_default_config_structure(self):
        """Test that default config has expected structure."""
        config = get_default_config()
        
        assert isinstance(config, Config)
        assert isinstance(config.paths, PathsConfig)
        assert isinstance(config.processing, ProcessingConfig)
        
        # Check paths
        assert config.paths.inbox == "inbox"
        assert config.paths.organized == "organized"
        
        # Check processing defaults
        assert config.processing.copy_mode is True
        assert config.processing.quality is False
        assert config.processing.watch is False
    
    @pytest.mark.unit
    def test_config_get_method(self):
        """Test the get method with dot notation."""
        config = Config()
        
        # Test simple access
        assert config.get('paths') == config.paths
        assert config.get('processing.quality') is False
        assert config.get('paths.inbox') == 'inbox'
        
        # Test with default
        assert config.get('nonexistent', 'default') == 'default'
        assert config.get('paths.nonexistent', 'default') == 'default'
    
    @pytest.mark.unit
    def test_config_set_method(self):
        """Test the set method with dot notation."""
        config = Config()
        
        # Test simple set
        config.set('processing.quality', True)
        assert config.processing.quality is True
        
        # Test nested set
        config.set('paths.inbox', 'custom_inbox')
        assert config.paths.inbox == 'custom_inbox'
    
    @pytest.mark.unit
    def test_config_to_dict(self):
        """Test conversion to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'paths' in config_dict
        assert 'processing' in config_dict
        assert config_dict['paths']['inbox'] == 'inbox'
    
    @pytest.mark.unit
    def test_config_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'paths': {'inbox': 'custom_inbox', 'organized': 'custom_organized'},
            'processing': {'quality': True, 'dry_run': True},
            'pipeline': {'mode': 'standard'}
        }
        
        config = Config.from_dict(data)
        
        assert config.paths.inbox == 'custom_inbox'
        assert config.paths.organized == 'custom_organized'
        assert config.processing.quality is True
        assert config.processing.dry_run is True
        assert config.pipeline.mode == 'standard'
        # Check that quality.enabled is synced
        assert config.quality.enabled is True
    
    @pytest.mark.unit
    def test_load_config_from_yaml(self):
        """Test loading configuration from YAML file."""
        config_data = {
            'paths': {'inbox': 'test_inbox'},
            'processing': {'quality': True}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            config = load_config(config_path)
            assert config.paths.inbox == 'test_inbox'
            assert config.processing.quality is True
            assert config.quality.enabled is True
        finally:
            config_path.unlink()
    
    @pytest.mark.unit
    def test_cli_overrides(self):
        """Test CLI overrides."""
        config = load_config(cli_overrides=[
            'processing.quality=true',
            'paths.inbox=custom_inbox',
            'processing.watch_interval=10',
            'pipeline.cost_limit=5.5'
        ])
        
        assert config.processing.quality is True
        assert config.paths.inbox == 'custom_inbox'
        assert config.processing.watch_interval == 10
        assert config.pipeline.cost_limit == 5.5
    
    @pytest.mark.unit
    def test_backward_compatibility(self):
        """Test DictConfig wrapper for backward compatibility."""
        from alicemultiverse.core.config_dataclass import DictConfig
        
        config = DictConfig()
        
        # Test dictionary-style access
        assert config['paths'] == config.paths
        config['processing.quality'] = True
        assert config.processing.quality is True