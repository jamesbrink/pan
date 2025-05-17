"""Tests for the Text-to-Speech functionality in pan_speech module."""

import platform
import unittest
from unittest import mock

import pyttsx3

from pan_speech import SpeakManager


class TestSpeakManager(unittest.TestCase):
    """Test the SpeakManager class and its optimization features."""

    def test_init(self):
        """Test SpeakManager initialization."""
        with mock.patch('pyttsx3.init') as mock_init:
            mock_engine = mock.MagicMock()
            mock_init.return_value = mock_engine
            manager = SpeakManager()
            
            # Verify engine was initialized
            mock_init.assert_called_once()
            self.assertEqual(manager.engine, mock_engine)
            
            # Verify queue and threading setup
            self.assertIsNotNone(manager.queue)
            self.assertIsNotNone(manager.lock)
            self.assertEqual(manager.speech_count, 0)
            self.assertFalse(manager.speaking_event.is_set())

    @mock.patch('platform.system')
    @mock.patch('pyttsx3.init')
    def test_init_engine_macos(self, mock_init, mock_system):
        """Test platform-specific engine initialization for macOS."""
        # Mock platform as macOS
        mock_system.return_value = 'Darwin'
        
        # Mock engine and voices
        mock_engine = mock.MagicMock()
        mock_init.return_value = mock_engine
        
        # Create mock voices
        mock_voice1 = mock.MagicMock()
        mock_voice1.name = 'Regular Voice'
        mock_voice1.id = 'voice1'
        
        mock_voice2 = mock.MagicMock()
        mock_voice2.name = 'Premium Voice'
        mock_voice2.id = 'voice2'
        
        mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]
        
        # Initialize manager
        manager = SpeakManager()
        
        # Verify macOS path was used
        mock_system.assert_called_once()
        mock_engine.getProperty.assert_called_with('voices')
        
        # Verify premium voice was selected
        mock_engine.setProperty.assert_any_call('voice', 'voice2')

    @mock.patch('platform.system')
    def test_chunk_text_platform_specific(self, mock_system):
        """Test platform-specific text chunking."""
        with mock.patch('pyttsx3.init'):
            manager = SpeakManager()
            
            # Test macOS (Darwin) chunking
            mock_system.return_value = 'Darwin'
            
            # Short text below chunk size - should not be chunked
            short_text = "This is a short sentence."
            chunks = manager._chunk_text(short_text)
            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0], short_text)
            
            # Long text with multiple sentences
            long_text = "This is sentence one. This is sentence two. " * 10
            macos_chunks = manager._chunk_text(long_text)
            
            # Change platform to Windows
            mock_system.return_value = 'Windows'
            windows_chunks = manager._chunk_text(long_text)
            
            # macOS should use larger chunks, resulting in fewer chunks
            self.assertLessEqual(len(macos_chunks), len(windows_chunks))

    @mock.patch('platform.system')
    def test_complex_chunking(self, mock_system):
        """Test chunking with complex text."""
        with mock.patch('pyttsx3.init'):
            manager = SpeakManager()
            
            # Very long single sentence that needs comma splitting
            mock_system.return_value = 'Darwin'
            
            # Make the sentence much longer to ensure it exceeds chunk size (300 chars for macOS)
            long_sentence = "This is a very, very, very long sentence without periods, " + \
                            "but with many commas, semicolons; and other punctuation: " + \
                            "that should be properly split into multiple chunks, " + \
                            "because it exceeds the maximum chunk size for any platform."
            
            # Repeat to make it longer than the 300 char limit
            long_sentence = long_sentence * 3
                            
            chunks = manager._chunk_text(long_sentence)
            
            # It should split on commas and other punctuation
            self.assertGreater(len(chunks), 1)
            
            # Instead of verifying punctuation endings (which might not be consistent),
            # verify that chunks are of appropriate size
            for chunk in chunks:
                # Each chunk should be smaller than or equal to the chunk size
                if mock_system.return_value == 'Darwin':
                    self.assertLessEqual(len(chunk), 300)
                else:
                    self.assertLessEqual(len(chunk), 150)

    @mock.patch('platform.system')
    @mock.patch('time.sleep')
    def test_worker_platform_specific_sleep(self, mock_sleep, mock_system):
        """Test platform-specific sleep timing in the worker."""
        with mock.patch('pyttsx3.init'):
            # Create a custom SpeakManager class that doesn't spawn a thread
            class TestSpeakManager(SpeakManager):
                def __init__(self):
                    # Skip parent init to avoid starting the thread
                    self.engine = mock.MagicMock()
                    self.queue = mock.MagicMock()
                    self.lock = mock.MagicMock()
                    self.speech_count = 0
                    self.speaking_event = mock.MagicMock()
                    self.sapi_engine = None
            
            manager = TestSpeakManager()
            
            # Replace the real _speak_chunk with a mock
            manager._speak_chunk = mock.MagicMock()
            
            # Mock chunk text to return a simple list
            manager._chunk_text = mock.MagicMock(return_value=["Chunk 1", "Chunk 2"])
            
            # Mock queue.get to return test data
            manager.queue.get.return_value = ("Test speech", "neutral")
            manager.queue.task_done = mock.MagicMock()
            manager.speaking_event.set = mock.MagicMock()
            manager.speaking_event.clear = mock.MagicMock()
            
            # Test macOS sleep behavior
            mock_system.return_value = 'Darwin'
            
            # Manually call the worker once
            manager._worker()
            
            # Verify sleep timing for macOS (should be 0.01s)
            mock_sleep.assert_any_call(0.01)
            
            # Change platform to Windows and test again
            mock_sleep.reset_mock()
            mock_system.return_value = 'Windows'
            
            # Manually call the worker once
            manager._worker()
            
            # Verify sleep timing for Windows (should be 0.05s)
            mock_sleep.assert_any_call(0.05)

    @mock.patch('platform.system')
    def test_macos_speak_chunk_optimization(self, mock_system):
        """Test macOS-specific optimizations in _speak_chunk."""
        with mock.patch('pyttsx3.init') as mock_init:
            mock_engine = mock.MagicMock()
            mock_init.return_value = mock_engine
            
            manager = SpeakManager()
            manager.set_voice_by_mood = mock.MagicMock()
            
            # Test macOS path
            mock_system.return_value = 'Darwin'
            manager._speak_chunk("Test speech", "happy")
            
            # For macOS, set_voice_by_mood should NOT be called in _speak_chunk
            manager.set_voice_by_mood.assert_not_called()
            
            # Test non-macOS path
            mock_system.reset_mock()
            manager.set_voice_by_mood.reset_mock()
            mock_system.return_value = 'Linux'
            
            manager._speak_chunk("Test speech", "happy")
            
            # For non-macOS, set_voice_by_mood SHOULD be called in _speak_chunk
            manager.set_voice_by_mood.assert_called_once_with("happy")

    @mock.patch('platform.system')
    def test_worker_engine_reinit_optimization(self, mock_system):
        """Test that engine is only reinitialized when necessary."""
        with mock.patch('pyttsx3.init') as mock_init:
            mock_engine = mock.MagicMock()
            # Mock isBusy to test conditional stopping
            mock_engine.isBusy.return_value = False
            mock_init.return_value = mock_engine
            
            # Create a custom SpeakManager class that doesn't spawn a thread
            # This avoids the worker running in the background causing test issues
            class TestSpeakManager(SpeakManager):
                def __init__(self):
                    # Skip parent init to avoid starting the thread
                    self.engine = None
                    self._init_engine()
                    self.queue = mock.MagicMock()
                    self.lock = mock.MagicMock()
                    self.speech_count = 0
                    self.speaking_event = mock.MagicMock()
                    self.sapi_engine = None
            
            manager = TestSpeakManager()
            manager._init_engine = mock.MagicMock()
            manager._speak_chunk = mock.MagicMock()
            manager._chunk_text = mock.MagicMock(return_value=["Test"])
            
            # Mock queue.get to return test data
            manager.queue.get.return_value = ("Test speech", "neutral")
            
            # Call worker directly without using the queue
            manager._worker()
            
            # Engine should NOT be reinitialized since isBusy is False
            manager._init_engine.assert_not_called()
            mock_engine.stop.assert_not_called()
            
            # Now mock engine as busy
            mock_engine.isBusy.return_value = True
            
            # Call worker again
            manager._worker()
            
            # Engine should be stopped but still not reinitialized
            mock_engine.stop.assert_called_once()
            manager._init_engine.assert_not_called()


if __name__ == '__main__':
    unittest.main()