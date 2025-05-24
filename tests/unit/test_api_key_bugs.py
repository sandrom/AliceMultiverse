"""Unit tests for API key management bugs that were fixed."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import getpass
import keyring

from alicemultiverse.core.keys.manager import APIKeyManager
from alicemultiverse.core.keys.cli import run_keys_command, _handle_setup, _handle_list


class TestAPIKeyBugs:
    """Test for API key management bugs."""
    
    @pytest.mark.unit
    def test_anthropic_key_shows_in_list(self):
        """Test that anthropic_api_key is properly listed."""
        manager = APIKeyManager()
        
        # Mock keyring to simulate stored keys
        with patch('keyring.get_password') as mock_get:
            # Setup mock to return keys for specific names
            def get_password_side_effect(service, key_name):
                if service == "AliceMultiverse":
                    if key_name == 'anthropic_api_key':
                        return 'sk-ant-test-key'
                    elif key_name == 'sightengine_user':
                        return 'test-user'
                    elif key_name == 'sightengine_secret':
                        return 'test-secret'
                return None
            
            mock_get.side_effect = get_password_side_effect
            
            # Get list of keys
            keys = manager.list_api_keys()
            
            # Verify anthropic_api_key is in the list
            assert any('anthropic_api_key' in key for key in keys)
            assert any('sightengine_user' in key for key in keys)
            assert any('sightengine_secret' in key for key in keys)
    
    @pytest.mark.unit
    def test_anthropic_key_environment_variable(self):
        """Test that ANTHROPIC_API_KEY environment variable is properly detected."""
        manager = APIKeyManager()
        
        # Mock environment variable
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-env-key'}):
            # Get the key
            key = manager.get_api_key('anthropic_api_key')
            assert key == 'sk-ant-env-key'
            
            # List should show it's from environment
            keys = manager.list_api_keys()
            assert any('anthropic_api_key (environment)' in key for key in keys)
    
    @pytest.mark.unit
    def test_handle_setup_function_exists(self):
        """Test that _handle_setup function exists and works."""
        # Create mock args
        mock_args = Mock()
        mock_args.keys_command = 'setup'
        
        # Mock user input and getpass
        with patch('builtins.input') as mock_input, \
             patch('getpass.getpass') as mock_getpass, \
             patch('keyring.set_password') as mock_set:
            
            # Simulate user selecting Anthropic (option 2) then exit (option 3)
            mock_input.side_effect = ['2', 'sk-ant-test-key', '3']
            mock_getpass.return_value = 'sk-ant-test-key'
            
            manager = APIKeyManager()
            result = _handle_setup(manager)
            
            # Should return 0 (success)
            assert result == 0
            
            # Verify keyring was called with correct parameters
            mock_set.assert_called_with('AliceMultiverse', 'anthropic_api_key', 'sk-ant-test-key')
    
    @pytest.mark.unit
    def test_keys_set_accepts_anthropic_api_key(self):
        """Test that 'keys set' command accepts anthropic_api_key."""
        mock_args = Mock()
        mock_args.keys_command = 'set'
        mock_args.key_name = 'anthropic_api_key'
        mock_args.method = 'keychain'
        
        with patch('getpass.getpass') as mock_getpass, \
             patch('keyring.set_password') as mock_set:
            
            mock_getpass.return_value = 'sk-ant-test-key'
            
            # Run the command
            result = run_keys_command(mock_args)
            
            # Should succeed
            assert result == 0
            
            # Verify keyring was called
            mock_set.assert_called_with('AliceMultiverse', 'anthropic_api_key', 'sk-ant-test-key')
    
    @pytest.mark.unit
    def test_keys_get_accepts_anthropic_api_key(self):
        """Test that 'keys get' command accepts anthropic_api_key."""
        mock_args = Mock()
        mock_args.keys_command = 'get'
        mock_args.key_name = 'anthropic_api_key'
        
        with patch('keyring.get_password') as mock_get:
            mock_get.return_value = 'sk-ant-test-key'
            
            # Run the command
            result = run_keys_command(mock_args)
            
            # Should succeed
            assert result == 0
            
            # Verify keyring was called
            mock_get.assert_called_with('AliceMultiverse', 'anthropic_api_key')
    
    @pytest.mark.unit 
    def test_keys_delete_accepts_anthropic_api_key(self):
        """Test that 'keys delete' command accepts anthropic_api_key."""
        mock_args = Mock()
        mock_args.keys_command = 'delete'
        mock_args.key_name = 'anthropic_api_key'
        
        with patch('keyring.delete_password') as mock_delete:
            # Run the command
            result = run_keys_command(mock_args)
            
            # Should succeed
            assert result == 0
            
            # Verify keyring was called
            mock_delete.assert_called_with('AliceMultiverse', 'anthropic_api_key')
    
    @pytest.mark.unit
    def test_menu_based_setup_wizard(self):
        """Test the menu-based setup wizard interface."""
        manager = APIKeyManager()
        
        # Mock user interactions for SightEngine setup
        with patch('builtins.input') as mock_input, \
             patch('keyring.set_password') as mock_set:
            
            # Select SightEngine (1), provide credentials, then exit (3)
            mock_input.side_effect = [
                '1',  # Select SightEngine
                'user123',  # API user
                'secret456',  # API secret
                '3'  # Exit
            ]
            
            result = _handle_setup(manager)
            
            # Should succeed
            assert result == 0
            
            # Verify both SightEngine keys were set
            assert mock_set.call_count == 2
            calls = mock_set.call_args_list
            assert calls[0] == (('AliceMultiverse', 'sightengine_user', 'user123'),)
            assert calls[1] == (('AliceMultiverse', 'sightengine_secret', 'secret456'),)
    
    @pytest.mark.unit
    def test_no_storage_method_selection(self):
        """Test that storage method selection has been removed."""
        mock_args = Mock(spec=['keys_command', 'key_name'])  # Use spec to limit attributes
        mock_args.keys_command = 'set'
        mock_args.key_name = 'anthropic_api_key'
        
        # The old code would have a --method parameter
        # Verify it doesn't exist
        assert not hasattr(mock_args, 'method')
        
        with patch('getpass.getpass') as mock_getpass, \
             patch('keyring.set_password') as mock_set:
            
            mock_getpass.return_value = 'sk-ant-test-key'
            
            # Run the command
            result = run_keys_command(mock_args)
            
            # Should succeed and always use keychain
            assert result == 0
            mock_set.assert_called_with('AliceMultiverse', 'anthropic_api_key', 'sk-ant-test-key')


class TestLegacyKeyNames:
    """Test that legacy key names still work for backward compatibility."""
    
    @pytest.mark.unit
    def test_claude_key_backward_compatibility(self):
        """Test that 'claude' key name still works for backward compatibility."""
        manager = APIKeyManager()
        
        # Mock keyring with a key stored under 'claude' 
        with patch('keyring.get_password') as mock_get:
            def get_password_side_effect(service, key_name):
                if service == "AliceMultiverse" and key_name == 'claude':
                    return 'sk-ant-legacy-key'
                return None
            
            mock_get.side_effect = get_password_side_effect
            
            # Getting 'claude' should work
            key = manager.get_api_key('claude')
            assert key == 'sk-ant-legacy-key'
            
            # List should show claude key
            keys = manager.list_api_keys()
            assert any('claude' in key for key in keys)
    
    @pytest.mark.unit
    def test_environment_variable_mappings(self):
        """Test that environment variable mappings work correctly."""
        manager = APIKeyManager()
        
        # Test various environment variable scenarios
        test_cases = [
            ('ANTHROPIC_API_KEY', 'anthropic_api_key', 'sk-ant-env'),
            ('SIGHTENGINE_API_USER', 'sightengine_user', 'user-env'),
            ('SIGHTENGINE_API_SECRET', 'sightengine_secret', 'secret-env'),
        ]
        
        for env_var, key_name, value in test_cases:
            with patch.dict('os.environ', {env_var: value}):
                # Get key should return the env value
                key = manager.get_api_key(key_name)
                assert key == value
                
                # List should show it's from environment
                keys = manager.list_api_keys()
                assert any(f'{key_name} (environment)' in k for k in keys)


class TestSetupWizardEdgeCases:
    """Test edge cases in the setup wizard."""
    
    @pytest.mark.unit
    def test_setup_wizard_invalid_choice(self):
        """Test setup wizard handles invalid choices gracefully."""
        manager = APIKeyManager()
        
        with patch('builtins.input') as mock_input, \
             patch('keyring.set_password'):
            
            # Invalid choice, then exit
            mock_input.side_effect = ['99', '3']
            
            result = _handle_setup(manager)
            
            # Should still succeed
            assert result == 0
    
    @pytest.mark.unit
    def test_setup_wizard_empty_credentials(self):
        """Test setup wizard handles empty credentials."""
        manager = APIKeyManager()
        
        with patch('builtins.input') as mock_input, \
             patch('getpass.getpass') as mock_getpass, \
             patch('keyring.set_password') as mock_set:
            
            # Select Anthropic but provide empty key
            mock_input.side_effect = ['2', '3']  # Exit after
            mock_getpass.return_value = ''  # Empty password
            
            result = _handle_setup(manager)
            
            # Should succeed but not set anything
            assert result == 0
            mock_set.assert_not_called()
    
    @pytest.mark.unit
    def test_setup_wizard_keyring_error(self):
        """Test setup wizard handles keyring errors gracefully."""
        manager = APIKeyManager()
        
        with patch('builtins.input') as mock_input, \
             patch('getpass.getpass') as mock_getpass, \
             patch('keyring.set_password') as mock_set:
            
            # Setup to raise an exception
            mock_input.side_effect = ['2', '3']
            mock_getpass.return_value = 'sk-ant-test'
            mock_set.side_effect = Exception("Keyring error")
            
            # Should not crash
            result = _handle_setup(manager)
            assert result == 0