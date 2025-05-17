"""Tests for assistant name configuration."""

import os
import unittest
from unittest import mock


class TestAssistantName(unittest.TestCase):
    """Test assistant name configuration."""

    @mock.patch('dotenv.load_dotenv')
    @mock.patch.dict(os.environ, {'ASSISTANT_NAME': 'TestBot'})
    def test_custom_assistant_name(self, mock_load_dotenv):
        """Test that ASSISTANT_NAME is loaded from environment variables."""
        # Mock dotenv.load_dotenv to avoid loading from .env file
        mock_load_dotenv.return_value = None
        
        # Clear any imported modules to force reload
        import sys
        if 'pan_config' in sys.modules:
            del sys.modules['pan_config']
            
        # Import after setting environment variable
        import pan_config
        self.assertEqual(pan_config.ASSISTANT_NAME, 'TestBot')
        
        # Check get_config() method
        config = pan_config.get_config()
        self.assertEqual(config['assistant']['name'], 'TestBot')

    @mock.patch('dotenv.load_dotenv')
    @mock.patch.dict(os.environ, {}, clear=True)  # Empty env dict, and clear others
    def test_default_assistant_name(self, mock_load_dotenv):
        """Test that default assistant name is used when not in environment."""
        # Mock dotenv.load_dotenv to avoid loading from .env file
        mock_load_dotenv.return_value = None
        
        # Clear any imported modules to force reload
        import sys
        if 'pan_config' in sys.modules:
            del sys.modules['pan_config']
            
        # Let's directly check the os.getenv behavior
        self.assertIsNone(os.getenv('ASSISTANT_NAME'))
        
        # Import with no environment variable to test default
        import pan_config
        
        # Since there's no environment variable, the default 'Pan' should be used
        self.assertEqual(pan_config.ASSISTANT_NAME, 'Pan')
        
        # Check get_config() method
        config = pan_config.get_config()
        self.assertEqual(config['assistant']['name'], 'Pan')


if __name__ == '__main__':
    unittest.main()