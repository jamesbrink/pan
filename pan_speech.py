"""
Speech Interface Module for PAN

This module provides text-to-speech and speech recognition capabilities for PAN.
It adjusts speech parameters based on emotional state, handles chunking of long
utterances, and provides robust speech recognition with error handling.
"""

import queue
import threading
import time
import traceback
import warnings

import pyttsx3

# Suppress deprecation warnings for speech_recognition library dependencies
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import speech_recognition as sr

from pan_config import (
    AMBIENT_NOISE_DURATION,
    DEFAULT_VOICE_RATE,
    DEFAULT_VOICE_VOLUME,
    ENERGY_THRESHOLD,
    PHRASE_TIME_LIMIT,
    SPEECH_RECOGNITION_TIMEOUT,
    USE_DYNAMIC_ENERGY_THRESHOLD,
)
from pan_emotions import pan_emotions

# Try to import Windows SAPI for better speech synthesis on Windows
try:
    import win32com.client

    has_sapi = True
except ImportError:
    has_sapi = False

# Voice parameters for different emotional states
emotion_voices = {
    "happy": {"rate": DEFAULT_VOICE_RATE + 20, "volume": DEFAULT_VOICE_VOLUME + 0.1},
    "excited": {"rate": DEFAULT_VOICE_RATE + 40, "volume": DEFAULT_VOICE_VOLUME + 0.1},
    "neutral": {"rate": DEFAULT_VOICE_RATE, "volume": DEFAULT_VOICE_VOLUME},
    "sad": {"rate": DEFAULT_VOICE_RATE - 20, "volume": DEFAULT_VOICE_VOLUME - 0.2},
    "angry": {"rate": DEFAULT_VOICE_RATE + 40, "volume": DEFAULT_VOICE_VOLUME + 0.1},
    "scared": {"rate": DEFAULT_VOICE_RATE - 30, "volume": DEFAULT_VOICE_VOLUME - 0.3},
    "calm": {"rate": DEFAULT_VOICE_RATE - 10, "volume": DEFAULT_VOICE_VOLUME - 0.1},
    "curious": {"rate": DEFAULT_VOICE_RATE + 10, "volume": DEFAULT_VOICE_VOLUME},
}

# Maximum length of each speech chunk to ensure smooth TTS
MAX_CHUNK_LENGTH = 150


class SpeakManager:
    """
    Manages text-to-speech operations with emotion-based voice modulation.

    This class handles background text-to-speech processing in a separate thread,
    manages chunking of long responses, and applies appropriate voice parameters
    based on PAN's current emotional state. It also handles fallback between
    Windows SAPI (if available) and cross-platform pyttsx3.

    If all TTS engines fail, the class creates a dummy engine that prints text
    to the console as a fallback mechanism.
    """

    def __init__(self):
        """
        Initialize the SpeakManager with necessary components for TTS.

        Sets up the TTS engine, creates a queue for speech requests,
        and starts a background worker thread to process speech tasks.
        """
        self.engine = None  # Initialize engine attribute
        self._init_engine()
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.speech_count = 0
        self.speaking_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

        if has_sapi:
            self.sapi_engine = win32com.client.Dispatch("SAPI.SpVoice")
        else:
            self.sapi_engine = None

    def _init_engine(self):
        """Initialize the pyttsx3 TTS engine."""
        print("[SpeakManager] Initializing pyttsx3 engine")
        try:
            # Try to use espeak driver explicitly first
            self.engine = pyttsx3.init(driverName="espeak")
        except (ImportError, RuntimeError, ValueError) as engine_error:
            print(f"Failed to init with espeak driver: {engine_error}")
            try:
                # Fall back to default initialization
                self.engine = pyttsx3.init()
            except (ImportError, RuntimeError, ValueError) as init_error:
                print(f"Failed to init TTS engine: {init_error}")
                # Create dummy engine if all else fails
                self._create_dummy_engine()

    def set_voice_by_mood(self, mood=None):
        """
        Set voice parameters based on the current emotional state.

        Args:
            mood (str, optional): The mood to set the voice for. If None,
                                  uses PAN's current mood.
        """
        if not mood:
            mood = pan_emotions.get_mood()
        settings = emotion_voices.get(mood, emotion_voices["neutral"])
        self.engine.setProperty("rate", settings["rate"])
        self.engine.setProperty("volume", settings["volume"])

    def _chunk_text(self, text):
        """
        Split long text into smaller chunks for better TTS processing.

        Args:
            text (str): The text to split into chunks

        Returns:
            list: A list of text chunks, each below MAX_CHUNK_LENGTH
        """
        import re

        sentences = re.split(r"(?<=[.!?]) +", text)
        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) <= MAX_CHUNK_LENGTH:
                current += sentence + " "
            else:
                chunks.append(current.strip())
                current = sentence + " "
        if current:
            chunks.append(current.strip())
        return chunks

    def _create_dummy_engine(self):
        """Create a dummy engine that just prints text when TTS fails."""

        class DummyEngine:
            """Dummy TTS engine that prints text instead of speaking."""

            def say(self, text):
                """Print text instead of speaking it."""
                print(f"[TTS FALLBACK] Speaking: {text}")

            def runAndWait(self):
                """Dummy implementation of runAndWait."""
                return

            def stop(self):
                """Dummy implementation of stop."""
                return

            def setProperty(self, _, __):
                """Dummy implementation of setProperty."""
                return

        self.engine = DummyEngine()
        print("[SpeakManager] Using fallback dummy TTS engine")

    def _speak_chunk(self, chunk, mood):
        """
        Speak a single chunk of text with the given mood.

        Attempts to use Windows SAPI if available, falling back to pyttsx3.

        Args:
            chunk (str): The text chunk to speak
            mood (str): The emotional mood to apply to the voice
        """
        if self.sapi_engine:
            try:
                print("[SpeakManager] Using Windows SAPI for TTS chunk.")
                self.sapi_engine.Speak(chunk)
                return
            except (AttributeError, RuntimeError) as sapi_error:
                print(f"SAPI TTS failed: {sapi_error}")
        try:
            self.set_voice_by_mood(mood)
            self.engine.say(chunk)
            self.engine.runAndWait()
        except (AttributeError, RuntimeError) as tts_error:
            print(f"TTS error in chunk: {tts_error}")
            traceback.print_exc()

    def _worker(self):
        """
        Background worker that processes speech tasks from the queue.

        Runs in a separate thread to avoid blocking the main program
        while speech synthesis is occurring.
        """
        while True:
            text, mood = self.queue.get()
            try:
                with self.lock:
                    self.engine.stop()
                    self._init_engine()

                    print("[SpeakManager] Speaking started")
                    self.speaking_event.set()

                    chunks = self._chunk_text(text)
                    for chunk in chunks:
                        self._speak_chunk(chunk, mood)
                        time.sleep(0.05)

                    self.speech_count += 1
                    print("[SpeakManager] Speaking ended")

            except (AttributeError, RuntimeError, IOError) as worker_error:
                print(f"TTS error occurred in worker: {worker_error}")
                traceback.print_exc()
            finally:
                self.speaking_event.clear()
            self.queue.task_done()

    def speak(self, text, mood_override=None):
        """
        Add text to the speech queue to be spoken with the given mood.

        Args:
            text (str): The text to speak
            mood_override (str, optional): Override the current mood with this one
        """
        self.queue.put((text, mood_override))


# Global instance of SpeakManager to be used throughout the application
speak_manager = SpeakManager()


def speak(text, mood_override=None):
    """
    Speak the given text with emotion-based voice modulation.

    A convenience function that delegates to the global SpeakManager instance.

    Args:
        text (str): The text to be spoken
        mood_override (str, optional): Override the current mood with this one
    """
    speak_manager.speak(text, mood_override)


def warn_low_affinity(user_id):
    """
    Generate a warning message if the user has low affinity.

    This function is intended to be replaced with a proper implementation
    that checks the user's affinity score from pan_research module.

    Args:
        user_id (str): The ID of the user to check affinity for

    Returns:
        str: A warning message if affinity is low, empty string otherwise
    """
    # This is a placeholder implementation
    # In actual usage, this would import pan_research module
    # and call pan_research.get_affinity(user_id)
    # Parameter is unused in this placeholder implementation
    _ = user_id  # Mark as used
    # For now, we'll just return an empty string
    return ""


def recalibrate_microphone():
    """
    Recalibrate the microphone for ambient noise.

    This function performs a longer calibration phase to better adjust
    to the current ambient noise conditions.

    Returns:
        bool: True if recalibration was successful, False otherwise
    """
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        print("Recalibrating microphone...")
        print("Please remain quiet for a moment...")

        with mic as source:
            # Use a longer duration for explicit recalibration
            duration = max(AMBIENT_NOISE_DURATION * 2, 5.0)
            recognizer.adjust_for_ambient_noise(source, duration=duration)

        print(
            f"Recalibration complete. Energy threshold: {recognizer.energy_threshold}"
        )
        return True

    except (sr.RequestError, sr.WaitTimeoutError, OSError, IOError) as e:
        # Catch specific exceptions instead of broad Exception
        print(f"Error during microphone recalibration: {e}")
        return False


def listen_to_user(timeout=None, recalibrate=False):
    """
    Listen for user speech input and convert it to text.

    Uses the speech_recognition library to capture audio from the microphone,
    then uses Google's speech recognition service to convert it to text.

    Args:
        timeout (int, optional): Maximum seconds to wait for speech to begin.
                               If None, uses SPEECH_RECOGNITION_TIMEOUT from config.
        recalibrate (bool): Force recalibration of ambient noise levels

    Returns:
        str or None: Transcribed speech text if successful, None if unsuccessful

    Raises:
        KeyboardInterrupt: Propagates keyboard interrupt for proper handling
    """
    if timeout is None:
        timeout = SPEECH_RECOGNITION_TIMEOUT
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    try:
        with mic as source:
            print("Listening...")
            # Use configurable noise sampling duration for better filtering
            calibrate_duration = AMBIENT_NOISE_DURATION
            if recalibrate:
                # Use a longer duration for explicit recalibration
                calibrate_duration = max(AMBIENT_NOISE_DURATION, 5.0)
                print(f"Recalibrating microphone for {calibrate_duration} seconds...")

            recognizer.adjust_for_ambient_noise(source, duration=calibrate_duration)

            # Apply configurable energy threshold settings
            recognizer.dynamic_energy_threshold = USE_DYNAMIC_ENERGY_THRESHOLD
            recognizer.energy_threshold = ENERGY_THRESHOLD

            try:
                # Use configurable phrase time limit
                audio = recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=PHRASE_TIME_LIMIT
                )
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase to start")
                return None
            except KeyboardInterrupt:
                # Re-raise for proper exit handling
                print("\nKeyboard interrupt detected during listening")
                raise

        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None
    except KeyboardInterrupt:
        # Re-raise for proper exit handling
        print("\nKeyboard interrupt detected during speech recognition")
        raise
