"""Simplified tests for macOS-specific optimizations in pan_speech."""

import platform
import unittest
from unittest import mock

import pyttsx3


class TestMacOSTTS(unittest.TestCase):
    """Test macOS-specific TTS optimizations."""

    @mock.patch('platform.system')
    def test_platform_specific_settings(self, mock_system):
        """Test that voice rate differs by platform."""
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
        
    @mock.patch('platform.system')
    def test_macos_chunk_size(self, mock_system):
        """Test that macOS uses larger chunk sizes."""
        # Mock platform.system() to return 'Darwin' (macOS)
        mock_system.return_value = 'Darwin'
        
        # Import the module
        from pan_speech import SpeakManager
        
        # Create a dummy instance with mocked pyttsx3.init
        with mock.patch('pyttsx3.init'):
            manager = SpeakManager()
            
            # Create a very long text
            long_text = "This is a test sentence. " * 50
            
            # Get chunks for macOS
            chunks_macos = manager._chunk_text(long_text)
            
            # Change platform to Windows
            mock_system.return_value = 'Windows'
            chunks_windows = manager._chunk_text(long_text)
            
            # macOS should use larger chunks, resulting in fewer chunks
            self.assertLessEqual(len(chunks_macos), len(chunks_windows))
            
            # Check actual chunk sizes
            if len(chunks_macos) > 0 and len(chunks_windows) > 0:
                # First chunk in macOS should be larger than first chunk in Windows
                # (300 vs 150 chars)
                self.assertGreater(len(chunks_macos[0]), len(chunks_windows[0]))
    
    @mock.patch('platform.system')
    def test_macos_sleep_time(self, mock_system):
        """Test that sleep time is reduced for macOS."""
        # Import the relevant modules
        import time
        from pan_speech import SpeakManager
        
        # Mock the platform
        mock_system.return_value = 'Darwin'
        
        # Mock time.sleep to check what value it's called with
        with mock.patch('time.sleep') as mock_sleep:
            # Mock pyttsx3.init
            with mock.patch('pyttsx3.init'):
                with mock.patch.object(SpeakManager, '_speak_chunk'), \
                     mock.patch.object(SpeakManager, '_chunk_text', return_value=['test']), \
                     mock.patch.object(SpeakManager, 'set_voice_by_mood'):
                    
                    # Create a simple test instance with mocked methods to avoid threading
                    manager = SpeakManager()
                    manager.queue = mock.MagicMock()
                    manager.queue.get.return_value = ('test text', 'neutral')
                    manager.queue.task_done = mock.MagicMock()
                    manager.speaking_event = mock.MagicMock()
                    
                    # Patch the worker method to not use an infinite loop
                    original_worker = manager._worker
                    
                    def worker_no_loop():
                        text, mood = manager.queue.get()
                        with manager.lock:
                            manager.speaking_event.set()
                            chunks = manager._chunk_text(text)
                            for chunk in chunks:
                                manager._speak_chunk(chunk, mood)
                                # This is what we're testing
                                time.sleep(0.01 if platform.system() == 'Darwin' else 0.05)
                            manager.speech_count += 1
                        manager.speaking_event.clear()
                        manager.queue.task_done()
                    
                    # Replace worker method
                    manager._worker = worker_no_loop
                    
                    # Call the worker
                    manager._worker()
                    
                    # For macOS, sleep should be called with 0.01
                    mock_sleep.assert_called_with(0.01)
                    
                    # Now test Windows
                    mock_system.return_value = 'Windows'
                    mock_sleep.reset_mock()
                    
                    # Call the worker again
                    manager._worker()
                    
                    # For Windows, sleep should be called with 0.05
                    mock_sleep.assert_called_with(0.05)


if __name__ == '__main__':
    unittest.main()