"""Tests for pan_speech module."""

import unittest
from unittest import mock

import speech_recognition as sr

from pan_config import (
    AMBIENT_NOISE_DURATION,
    ENERGY_THRESHOLD,
    PHRASE_TIME_LIMIT,
    SPEECH_RECOGNITION_TIMEOUT,
    USE_DYNAMIC_ENERGY_THRESHOLD,
)
from pan_speech import listen_to_user, recalibrate_microphone


class TestPanSpeechConfig(unittest.TestCase):
    """Test configuration loading for speech recognition settings."""

    def test_config_values_loaded(self):
        """Test that configuration values are loaded from environment."""
        # Verify config values are of correct type
        self.assertIsInstance(AMBIENT_NOISE_DURATION, float)
        self.assertIsInstance(USE_DYNAMIC_ENERGY_THRESHOLD, bool)
        self.assertIsInstance(ENERGY_THRESHOLD, int)
        self.assertIsInstance(SPEECH_RECOGNITION_TIMEOUT, int)
        self.assertIsInstance(PHRASE_TIME_LIMIT, int)

        # Verify config values are in sensible ranges
        self.assertGreater(AMBIENT_NOISE_DURATION, 0)
        self.assertGreater(ENERGY_THRESHOLD, 0)
        self.assertGreater(SPEECH_RECOGNITION_TIMEOUT, 0)
        self.assertGreater(PHRASE_TIME_LIMIT, 0)


class TestListenToUser(unittest.TestCase):
    """Test the listen_to_user function."""

    @mock.patch('speech_recognition.Recognizer')
    @mock.patch('speech_recognition.Microphone')
    def test_timeout_parameter(self, mock_mic, mock_recognizer):
        """Test that the timeout parameter is used correctly."""
        # Setup mocks
        mock_recognizer_instance = mock.MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_source = mock.MagicMock()
        mock_mic.return_value.__enter__.return_value = mock_source

        # Default timeout from config
        listen_to_user()
        mock_recognizer_instance.listen.assert_called_with(
            mock_source, timeout=SPEECH_RECOGNITION_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT
        )

        # Custom timeout
        listen_to_user(timeout=10)
        mock_recognizer_instance.listen.assert_called_with(
            mock_source, timeout=10, phrase_time_limit=PHRASE_TIME_LIMIT
        )

    @mock.patch('speech_recognition.Recognizer')
    @mock.patch('speech_recognition.Microphone')
    def test_recalibrate_parameter(self, mock_mic, mock_recognizer):
        """Test that the recalibrate parameter extends calibration time."""
        # Setup mocks
        mock_recognizer_instance = mock.MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_source = mock.MagicMock()
        mock_mic.return_value.__enter__.return_value = mock_source

        # Without recalibration
        listen_to_user(recalibrate=False)
        mock_recognizer_instance.adjust_for_ambient_noise.assert_called_with(
            mock_source, duration=AMBIENT_NOISE_DURATION
        )

        # With recalibration - should use longer duration
        listen_to_user(recalibrate=True)
        last_call = mock_recognizer_instance.adjust_for_ambient_noise.call_args
        self.assertGreaterEqual(last_call[1]['duration'], AMBIENT_NOISE_DURATION)
        

class TestRecalibrateMicrophone(unittest.TestCase):
    """Test the recalibrate_microphone function."""
    
    @mock.patch('speech_recognition.Recognizer')
    @mock.patch('speech_recognition.Microphone')
    def test_recalibration(self, mock_mic, mock_recognizer):
        """Test that recalibration function calls adjust_for_ambient_noise with extended duration."""
        # Setup mocks
        mock_recognizer_instance = mock.MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_source = mock.MagicMock()
        mock_mic.return_value.__enter__.return_value = mock_source
        
        # Call recalibration function
        result = recalibrate_microphone()
        
        # Verify it succeeded
        self.assertTrue(result)
        
        # Verify it used a longer duration than the default
        last_call = mock_recognizer_instance.adjust_for_ambient_noise.call_args
        self.assertGreaterEqual(last_call[1]['duration'], AMBIENT_NOISE_DURATION * 2)