"""Tests for the pan_config module."""

import os
import platform
import unittest
from unittest import mock


class TestPanConfig(unittest.TestCase):
    """Test the pan_config module and its platform-specific settings."""

    @mock.patch.dict(os.environ, {})
    @mock.patch('platform.system')
    def test_default_voice_rate(self, mock_system):
        """Test that voice rate is platform-specific with correct defaults."""
        # Clear any imported modules to force reload
        import sys
        if 'pan_config' in sys.modules:
            del sys.modules['pan_config']
            
        # Test macOS defaults
        mock_system.return_value = 'Darwin'
        import pan_config
        self.assertEqual(pan_config.DEFAULT_VOICE_RATE, 190)
        
        # Clear imported module again
        del sys.modules['pan_config']
        
        # Test other platform defaults
        mock_system.return_value = 'Linux'
        import pan_config
        self.assertEqual(pan_config.DEFAULT_VOICE_RATE, 160)
    
    @mock.patch.dict(os.environ, {'DEFAULT_VOICE_RATE': '150', 'MACOS_VOICE_RATE': '200'})
    @mock.patch('platform.system')
    def test_custom_voice_rate(self, mock_system):
        """Test that voice rate respects environment variables."""
        # Clear any imported modules to force reload
        import sys
        if 'pan_config' in sys.modules:
            del sys.modules['pan_config']
            
        # Test macOS with custom settings
        mock_system.return_value = 'Darwin'
        import pan_config
        self.assertEqual(pan_config.DEFAULT_VOICE_RATE, 200)
        
        # Clear imported module again
        del sys.modules['pan_config']
        
        # Test other platforms with custom settings
        mock_system.return_value = 'Linux'
        import pan_config
        self.assertEqual(pan_config.DEFAULT_VOICE_RATE, 150)


if __name__ == '__main__':
    unittest.main()