"""Tests for microphone diagnostics and permission checking functionality."""

import unittest
from unittest import mock
import platform
import sys
import os

from pan_speech import test_microphone
import pan_speech

# Import main only within test cases to avoid circular imports
# from main import check_macos_microphone_permissions

# This is a dummy function just for testing
def _dummy_test_microphone():
    """Dummy test to avoid warnings in test suite."""
    pass


class TestMicrophoneTest(unittest.TestCase):
    """Test the microphone test function."""

    @mock.patch('pan_speech.sr.Microphone')
    @mock.patch('pan_speech.sr.Recognizer')
    @mock.patch('platform.system')
    @mock.patch('platform.python_version')
    def test_successful_microphone_test(self, mock_python_version, mock_system, 
                                       mock_recognizer, mock_microphone):
        """Test the microphone test function with successful microphone access."""
        # Mock platform info
        mock_system.return_value = "Darwin"
        mock_python_version.return_value = "3.12.0"
        
        # Mock microphone listing
        mock_microphone.list_microphone_names.return_value = ["Built-in Microphone", "External Mic"]
        
        # Mock microphone instance
        mock_mic_instance = mock.MagicMock()
        mock_microphone.return_value = mock_mic_instance
        
        # Mock recognizer
        mock_recognizer_instance = mock.MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.energy_threshold = 300
        
        # Mock recording and recognition
        mock_audio = mock.MagicMock()
        mock_recognizer_instance.record.return_value = mock_audio
        mock_recognizer_instance.recognize_google.return_value = "test speech"
        
        # Run the test
        result = test_microphone()
        
        # Verify result
        self.assertTrue(result)
        mock_microphone.list_microphone_names.assert_called_once()
        mock_microphone.assert_called_once()
        mock_recognizer_instance.adjust_for_ambient_noise.assert_called_once()
        mock_recognizer_instance.record.assert_called_once()
        mock_recognizer_instance.recognize_google.assert_called_once()

    @mock.patch('pan_speech.sr.Microphone')
    @mock.patch('platform.system')
    def test_no_microphones_available(self, mock_system, mock_microphone):
        """Test microphone test when no microphones are available."""
        # Mock platform info
        mock_system.return_value = "Darwin"
        
        # Mock empty microphone list
        mock_microphone.list_microphone_names.return_value = []
        
        # Run the test
        result = test_microphone()
        
        # Verify result
        self.assertFalse(result)
        mock_microphone.list_microphone_names.assert_called_once()
        # We don't check if the constructor was called because the implementation still tries 
        # to create a microphone instance even when no microphones are available

    @mock.patch('pan_speech.sr.Microphone')
    @mock.patch('platform.system')
    def test_microphone_initialization_error(self, mock_system, mock_microphone):
        """Test microphone test when microphone initialization fails."""
        # Mock platform info
        mock_system.return_value = "Darwin"
        
        # Mock microphone listing
        mock_microphone.list_microphone_names.return_value = ["Built-in Microphone"]
        
        # Mock microphone initialization error
        mock_microphone.side_effect = OSError("Permission denied")
        
        # Run the test
        result = test_microphone()
        
        # Verify result
        self.assertFalse(result)
        mock_microphone.list_microphone_names.assert_called_once()
        mock_microphone.assert_called_once()

    @mock.patch('pan_speech.sr.Microphone')
    @mock.patch('pan_speech.sr.Recognizer')
    @mock.patch('platform.system')
    def test_calibration_error(self, mock_system, mock_recognizer, mock_microphone):
        """Test microphone test when calibration fails."""
        # Mock platform info
        mock_system.return_value = "Darwin"
        
        # Mock microphone listing
        mock_microphone.list_microphone_names.return_value = ["Built-in Microphone"]
        
        # Mock microphone instance
        mock_mic_instance = mock.MagicMock()
        mock_microphone.return_value = mock_mic_instance
        
        # Mock recognizer with calibration error
        mock_recognizer_instance = mock.MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.adjust_for_ambient_noise.side_effect = Exception("Calibration error")
        
        # Run the test
        result = test_microphone()
        
        # Verify result
        self.assertFalse(result)
        mock_microphone.list_microphone_names.assert_called_once()
        mock_microphone.assert_called_once()
        mock_recognizer_instance.adjust_for_ambient_noise.assert_called_once()


class TestMacOSPermissionsCheck(unittest.TestCase):
    """Test macOS permissions check function."""

    @mock.patch('platform.system')
    def test_non_macos_skips_check(self, mock_system):
        """Test that permissions check is skipped on non-macOS platforms."""
        # Mock platform as non-macOS
        mock_system.return_value = "Linux"
        
        # Import the function and reload to ensure mocks take effect
        import importlib
        import sys
        if 'main' in sys.modules:
            del sys.modules['main']
        # Patch speech_recognition before importing main
        with mock.patch('speech_recognition.Microphone') as mock_microphone:
            import main
            importlib.reload(main)
            
            # Run the check
            main.check_macos_microphone_permissions()
            
            # Should not attempt to check microphones
            mock_microphone.list_microphone_names.assert_not_called()

    @mock.patch('platform.system')
    def test_macos_with_microphones(self, mock_system):
        """Test permissions check on macOS with microphones available."""
        # Mock platform as macOS
        mock_system.return_value = "Darwin"
        
        # Import the function and reload to ensure mocks take effect
        import importlib
        import sys
        if 'main' in sys.modules:
            del sys.modules['main']
        # Patch speech_recognition before importing main
        with mock.patch('speech_recognition.Microphone') as mock_microphone:
            mock_microphone.list_microphone_names.return_value = ["Built-in Microphone"]
            
            import main
            importlib.reload(main)
            
            # Run the check (should complete without error)
            main.check_macos_microphone_permissions()
            
            # Should check microphones
            mock_microphone.list_microphone_names.assert_called_once()

    @mock.patch('platform.system')
    def test_macos_no_microphones(self, mock_system):
        """Test permissions check on macOS with no microphones available."""
        # Mock platform as macOS
        mock_system.return_value = "Darwin"
        
        # Import the function and reload to ensure mocks take effect
        import importlib
        import sys
        import io
        from contextlib import redirect_stdout
        
        if 'main' in sys.modules:
            del sys.modules['main']
        # Patch speech_recognition before importing main
        with mock.patch('speech_recognition.Microphone') as mock_microphone:
            # Mock no microphones available
            mock_microphone.list_microphone_names.return_value = []
            
            import main
            importlib.reload(main)
            
            # Capture stdout to verify warning is printed
            f = io.StringIO()
            with redirect_stdout(f):
                main.check_macos_microphone_permissions()
            
            output = f.getvalue()
            
            # Verify warning is in output
            self.assertIn("MACOS MICROPHONE PERMISSION ALERT", output)
            self.assertIn("No microphones were detected", output)
            
            # Should check microphones
            mock_microphone.list_microphone_names.assert_called_once()

    @mock.patch('platform.system')
    def test_macos_permission_error(self, mock_system):
        """Test permissions check on macOS when microphone listing raises error."""
        # Mock platform as macOS
        mock_system.return_value = "Darwin"
        
        # Import the function and reload to ensure mocks take effect
        import importlib
        import sys
        if 'main' in sys.modules:
            del sys.modules['main']
        # Patch speech_recognition before importing main
        with mock.patch('speech_recognition.Microphone') as mock_microphone:
            # Mock error when listing microphones
            mock_microphone.list_microphone_names.side_effect = OSError("Permission denied")
            
            import main
            importlib.reload(main)
            
            # Run the check (should handle error gracefully)
            main.check_macos_microphone_permissions()
            
            # Should attempt to check microphones
            mock_microphone.list_microphone_names.assert_called_once()


class TestListenForKeyword(unittest.TestCase):
    """Test keyword detection function with additional diagnostic improvements."""

    @mock.patch('pan_speech.sr.Microphone')
    @mock.patch('pan_speech.sr.Recognizer')
    @mock.patch('platform.system')
    def test_macos_microphone_listing(self, mock_system, mock_recognizer, mock_microphone):
        """Test that macOS microphone listing works correctly."""
        # Mock platform as macOS
        mock_system.return_value = "Darwin"
        
        # Mock microphone listing
        mock_microphone.list_microphone_names.return_value = ["Built-in Microphone"]
        
        # Reset the class attribute if it exists
        if hasattr(pan_speech.sr.Microphone, '_checked_macos_permissions'):
            delattr(pan_speech.sr.Microphone, '_checked_macos_permissions')
        
        # Mock microphone instance
        mock_mic_instance = mock.MagicMock()
        mock_microphone.return_value = mock_mic_instance
        
        # Mock recognizer
        mock_recognizer_instance = mock.MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.return_value = "pan help me"
        
        # Call function
        result = pan_speech.listen_for_keyword()
        
        # Verify microphone listing was called
        mock_microphone.list_microphone_names.assert_called_once()
        
        # Verify class attribute was set to avoid repeated checking
        self.assertTrue(hasattr(pan_speech.sr.Microphone, '_checked_macos_permissions'))
        self.assertTrue(pan_speech.sr.Microphone._checked_macos_permissions)

    @mock.patch('pan_speech.sr.Microphone')
    @mock.patch('platform.system')
    def test_macos_no_microphones(self, mock_system, mock_microphone):
        """Test keyword detection when no microphones are available on macOS."""
        # Mock platform as macOS
        mock_system.return_value = "Darwin"
        
        # Reset the class attribute if it exists
        if hasattr(pan_speech.sr.Microphone, '_checked_macos_permissions'):
            delattr(pan_speech.sr.Microphone, '_checked_macos_permissions')
        
        # Mock empty microphone list
        mock_microphone.list_microphone_names.return_value = []
        
        # Capture stdout to verify warning is printed
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            result = pan_speech.listen_for_keyword()
        
        output = f.getvalue()
        
        # Verify result and warning
        self.assertFalse(result)
        self.assertIn("No microphones detected", output)
        self.assertIn("MACOS PERMISSION ERROR", output)


if __name__ == '__main__':
    unittest.main()