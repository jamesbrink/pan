"""
Speech Interface Module for PAN (Cross-Platform)

This module provides text-to-speech and speech recognition capabilities for PAN.
It supports both Windows (SAPI) and Linux (espeak) for TTS, and provides robust
speech recognition with Google Speech API.
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

import platform

from pan_config import (
    AMBIENT_NOISE_DURATION,
    ASSISTANT_NAME,
    CONTINUOUS_LISTENING,
    DEFAULT_VOICE_RATE,
    DEFAULT_VOICE_VOLUME,
    ENERGY_THRESHOLD,
    KEYWORD_ACTIVATION_THRESHOLD,
    PHRASE_TIME_LIMIT,
    SPEECH_RECOGNITION_TIMEOUT,
    USE_DYNAMIC_ENERGY_THRESHOLD,
    USE_KEYWORD_ACTIVATION,
)
from pan_emotions import pan_emotions

# Detect OS
is_windows = platform.system().lower() == "windows"
is_linux = platform.system().lower() == "linux"
is_macos = platform.system().lower() == "darwin"

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
        self.exit_requested = False
        self.last_restart_time = 0  # Track last engine restart time
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

        if has_sapi:
            self.sapi_engine = win32com.client.Dispatch("SAPI.SpVoice")
        else:
            self.sapi_engine = None

    def stop(self):
        """
        Stop speech processing cleanly.

        Stops any ongoing speech and signals the background worker thread to exit.
        """
        self.exit_requested = True

        # Clear queue to prevent further processing
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break

        # Stop ongoing speech
        with self.lock:
            try:
                if hasattr(self.engine, "stop"):
                    self.engine.stop()
            except Exception as e:
                print(f"Error stopping speech engine: {e}")

        # Clear speaking flag
        self.speaking_event.clear()

    def _init_engine(self):
        """Initialize the pyttsx3 TTS engine with platform-specific optimizations."""
        print("[SpeakManager] Initializing pyttsx3 engine")

        try:
            if is_macos:
                # On macOS, use the default NSS driver and increase rate
                self.engine = pyttsx3.init()
                # Get available voices and try to find a high-quality voice
                voices = self.engine.getProperty("voices")
                for voice in voices:
                    # Look for higher quality voices - typically ones with "premium" or "enhanced" in the name
                    if (
                        voice.name.lower().find("premium") != -1
                        or voice.name.lower().find("enhanced") != -1
                    ):
                        self.engine.setProperty("voice", voice.id)
                        print(
                            f"[SpeakManager] Using enhanced macOS voice: {voice.name}"
                        )
                        break
            elif is_windows:
                self.engine = pyttsx3.init(driverName="sapi5")
                if has_sapi:
                    self.sapi_engine = win32com.client.Dispatch("SAPI.SpVoice")
                else:
                    self.sapi_engine = None
            elif is_linux:
                self.engine = pyttsx3.init(driverName="espeak")
            else:
                self.engine = pyttsx3.init()  # Default cross-platform
        except (ImportError, RuntimeError, ValueError) as e:
            print(f"Failed to init TTS engine: {e}")
            self._create_dummy_engine()

    def set_voice_by_mood(self, mood=None):
        if not mood:
            mood = pan_emotions.get_mood()
        settings = emotion_voices.get(mood, emotion_voices["neutral"])
        self.engine.setProperty("rate", settings["rate"])
        self.engine.setProperty("volume", settings["volume"])

    def _chunk_text(self, text):
        """
        Split long text into smaller chunks for better TTS processing.
        Optimized with platform-specific chunk sizes.

        Args:
            text (str): The text to split into chunks

        Returns:
            list: A list of text chunks optimized for the current platform
        """
        import re

        # Use platform-specific chunk sizes
        # macOS NSSpeechSynthesizer performs better with larger chunks
        chunk_size = 300 if is_macos else MAX_CHUNK_LENGTH

        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?]) +", text)

        # Fast path for short text (no chunking needed)
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) <= chunk_size:
                current += sentence + " "
            else:
                # If we have content to add, add it
                if current:
                    chunks.append(current.strip())

                # If the sentence itself is too long, we need to split it further
                if len(sentence) > chunk_size:
                    # Split on commas and other natural pauses for very long sentences
                    subparts = re.split(r"(?<=,|;|:) +", sentence)
                    subcurrent = ""
                    for part in subparts:
                        if len(subcurrent) + len(part) <= chunk_size:
                            subcurrent += part + " "
                        else:
                            if subcurrent:
                                chunks.append(subcurrent.strip())
                            subcurrent = part + " "
                    if subcurrent:
                        chunks.append(subcurrent.strip())
                else:
                    current = sentence + " "
        if current:
            chunks.append(current.strip())

        return chunks

    def _create_dummy_engine(self):
        class DummyEngine:
            def say(self, text):
                print(f"[TTS FALLBACK] Speaking: {text}")

            def runAndWait(self):
                pass

            def stop(self):
                pass

            def setProperty(self, prop, value):
                pass

        self.engine = DummyEngine()
        print("[SpeakManager] Using fallback dummy TTS engine")

    def _speak_chunk(self, chunk, mood):
        """
        Speak a single chunk of text with the given mood.

        Uses platform-specific optimizations and falls back if needed.

        Args:
            chunk (str): The text chunk to speak
            mood (str): The emotional mood to apply to the voice
        """
        # Use Windows SAPI if available
        if self.sapi_engine:
            try:
                print("[SpeakManager] Using Windows SAPI for TTS chunk.")
                self.sapi_engine.Speak(chunk)
                return
            except (AttributeError, RuntimeError) as sapi_error:
                print(f"SAPI TTS failed: {sapi_error}")

        # macOS-specific optimizations
        if is_macos:
            try:
                # We already set the voice parameters in the worker, no need to call set_voice_by_mood each time
                # This avoids the overhead of changing properties for each chunk
                self.engine.say(chunk)
                
                # Handle the "run loop already started" error that can occur when
                # multiple speech requests come in quickly
                try:
                    self.engine.runAndWait()
                except RuntimeError as loop_error:
                    if "run loop already started" in str(loop_error):
                        print("[SpeakManager] Detected run loop error, using alternative approach")
                        # Give a small delay to let the previous runAndWait finish
                        time.sleep(0.5)
                        # Use a safer approach for TTS when run loop is already started
                        try:
                            # Instead of restarting the engine, create a fallback text output
                            print(f"[SpeakManager] TTS Fallback: {chunk}")
                            # Wait a moment to let any pending speech complete
                            time.sleep(1.0)
                            # Only try to init a new engine if we've waited long enough
                            if hasattr(self, "last_restart_time"):
                                time_since_restart = time.time() - self.last_restart_time
                                if time_since_restart > 5.0:  # Only restart every 5 seconds
                                    self._init_engine()
                                    self.last_restart_time = time.time()
                            else:
                                self.last_restart_time = time.time()
                        except Exception as restart_error:
                            print(f"TTS fallback approach failed: {restart_error}")
                    else:
                        print(f"macOS TTS runAndWait error: {loop_error}")
            except (AttributeError, RuntimeError) as tts_error:
                print(f"macOS TTS error in chunk: {tts_error}")
                traceback.print_exc()
        else:
            # For non-macOS platforms
            try:
                # We set this in the worker, but some engines might need it per chunk
                self.set_voice_by_mood(mood)
                self.engine.say(chunk)
                
                # Handle the "run loop already started" error
                try:
                    self.engine.runAndWait()
                except RuntimeError as loop_error:
                    if "run loop already started" in str(loop_error):
                        print("[SpeakManager] Detected run loop error, using alternative approach")
                        # Give a small delay to let the previous runAndWait finish
                        time.sleep(0.5)
                        # Use a safer approach for TTS when run loop is already started
                        try:
                            # Instead of restarting the engine, create a fallback text output
                            print(f"[SpeakManager] TTS Fallback: {chunk}")
                            # Wait a moment to let any pending speech complete
                            time.sleep(1.0)
                            # Only try to init a new engine if we've waited long enough
                            if hasattr(self, "last_restart_time"):
                                time_since_restart = time.time() - self.last_restart_time
                                if time_since_restart > 5.0:  # Only restart every 5 seconds
                                    self._init_engine()
                                    self.last_restart_time = time.time()
                            else:
                                self.last_restart_time = time.time()
                        except Exception as restart_error:
                            print(f"TTS fallback approach failed: {restart_error}")
                    else:
                        print(f"TTS runAndWait error: {loop_error}")
            except (AttributeError, RuntimeError) as tts_error:
                print(f"TTS error in chunk: {tts_error}")
                traceback.print_exc()

    def _worker(self):
        """
        Background worker that processes speech tasks from the queue.

        Runs in a separate thread to avoid blocking the main program
        while speech synthesis is occurring. Checks for exit_requested
        flag to allow clean shutdown.
        """
        while not self.exit_requested:
            try:
                # Use a timeout to periodically check for exit requests
                try:
                    text, mood = self.queue.get(timeout=0.5)
                except queue.Empty:
                    # No items in queue, just check for exit_requested and continue
                    continue

                # If we got a task but exit was requested, skip processing
                if self.exit_requested:
                    self.queue.task_done()
                    continue

                try:
                    with self.lock:
                        # Don't reinitialize the engine for every speech - this is a major
                        # performance issue especially on macOS
                        # Only stop the engine if it's already speaking
                        if hasattr(self.engine, "isBusy") and self.engine.isBusy():
                            self.engine.stop()

                        print("[SpeakManager] Speaking started")
                        self.speaking_event.set()

                        # Set voice parameters once before speaking
                        self.set_voice_by_mood(mood)

                        chunks = self._chunk_text(text)
                        for chunk in chunks:
                            # Check for exit request between chunks
                            if self.exit_requested:
                                break

                            self._speak_chunk(chunk, mood)
                            # Reduced sleep time for macOS to improve responsiveness
                            time.sleep(0.01 if is_macos else 0.05)

                        self.speech_count += 1
                        print("[SpeakManager] Speaking ended")

                except (AttributeError, RuntimeError, IOError) as worker_error:
                    print(f"TTS error occurred in worker: {worker_error}")
                    traceback.print_exc()
                finally:
                    self.speaking_event.clear()

                self.queue.task_done()

            except Exception as e:
                # Catch any other exceptions to prevent thread crashes
                print(f"Unexpected error in speech worker thread: {e}")
                traceback.print_exc()

        print("[SpeakManager] Speech worker thread exiting cleanly.")

    def speak(self, text, mood_override=None):
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
    to the current ambient noise conditions. It uses chunked calibration
    to ensure the process is interruptible with CTRL+C.

    Returns:
        bool: True if recalibration was successful, False otherwise
    """
    try:
        recognizer = sr.Recognizer()

        try:
            mic = sr.Microphone()
        except (OSError, IOError) as e:
            print(f"Error initializing microphone: {e}")
            return False

        print("Recalibrating microphone...")
        print("Please remain quiet for a moment...")

        with mic as source:
            # Use a longer duration for explicit recalibration
            total_duration = max(AMBIENT_NOISE_DURATION * 2, 5.0)

            # Break into smaller chunks to allow for interruption
            chunk_size = 0.5  # seconds
            num_chunks = int(total_duration / chunk_size)

            # Perform calibration in interruptible chunks
            for i in range(num_chunks):
                try:
                    print(f"Calibration progress: {i+1}/{num_chunks}", end="\r")
                    recognizer.adjust_for_ambient_noise(source, duration=chunk_size)
                except KeyboardInterrupt:
                    print("\nCalibration interrupted by user")
                    raise
                except Exception as e:
                    print(f"\nError during calibration chunk {i+1}: {e}")
                    # Continue with other chunks

            print(
                "\nCalibration complete. Energy threshold: "
                f"{recognizer.energy_threshold:.1f}"
            )
            return True

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected during microphone recalibration")
        raise
    except (sr.RequestError, sr.WaitTimeoutError, OSError, IOError) as e:
        # Catch specific exceptions instead of broad Exception
        print(f"Error during microphone recalibration: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during microphone recalibration: {e}")
        return False


def listen_for_keyword(timeout=3):
    """
    Listen for the wake keyword (assistant name) in ambient audio.
    
    Continuously monitors audio input for the assistant's name to be spoken,
    using a simpler recognition approach for better responsiveness.
    
    Args:
        timeout (int, optional): Timeout for each listening attempt in seconds
    
    Returns:
        bool: True if keyword was detected, False otherwise
        
    Raises:
        KeyboardInterrupt: Propagates keyboard interrupt for proper handling
    """
    assistant_name_lower = ASSISTANT_NAME.lower()
    
    # Create a recognizer specifically for keyword detection
    recognizer = sr.Recognizer()
    
    # Initialize the microphone
    try:
        mic = sr.Microphone()
    except (OSError, IOError) as e:
        print(f"Error initializing microphone for keyword detection: {e}")
        return False
    
    try:
        with mic as source:
            # Shorter ambient noise adjustment to be more responsive
            try:
                # Use a shorter ambient noise duration for wake word detection
                # to make it more responsive
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception as e:
                print(f"Error during keyword calibration: {e}")
            
            # Use more sensitive settings for keyword detection
            # Lower energy threshold makes it more sensitive to quiet speech
            recognizer.dynamic_energy_threshold = True
            recognizer.energy_threshold = max(ENERGY_THRESHOLD - 50, 200)  # More sensitive
            
            try:
                print("Listening for wake word...")
                # Use a shorter phrase time limit for quicker detection
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=2)
            except sr.WaitTimeoutError:
                return False
            except KeyboardInterrupt:
                print("\nKeyboard interrupt detected during keyword listening")
                raise
            except Exception as e:
                print(f"Error during keyword listening: {e}")
                return False
        
        try:
            # Use Google's speech recognition for better accuracy
            text = recognizer.recognize_google(audio).lower()
            print(f"Heard: {text}")
            
            # Check if the assistant name is in the recognized text
            # We look for exact matches or close matches (like "hey pan" or "ok pan")
            words = text.split()
            if assistant_name_lower in text:
                print(f"Wake word '{ASSISTANT_NAME}' detected!")
                return True
            
            # Also detect if the assistant name is at the beginning or end of any word
            # This helps catch cases where words run together
            for word in words:
                if (word.startswith(assistant_name_lower) or 
                    word.endswith(assistant_name_lower) or 
                    assistant_name_lower in word):
                    print(f"Wake word '{ASSISTANT_NAME}' detected in word: {word}!")
                    return True
            
            return False
        except sr.UnknownValueError:
            # This is normal for keyword detection - silent periods, unclear speech, etc.
            return False
        except sr.RequestError as e:
            print(f"Could not request results for keyword detection; {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during keyword recognition: {e}")
            return False
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected during keyword recognition")
        raise
    except Exception as e:
        print(f"Unexpected error in keyword recognition: {e}")
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

    # Create a separate recognizer for each session to avoid issues with interrupted instances
    recognizer = sr.Recognizer()

    # Initialize the microphone in a try block to handle potential errors
    try:
        mic = sr.Microphone()
    except (OSError, IOError) as e:
        print(f"Error initializing microphone: {e}")
        return None

    # Make audio capture interruptible with a short timeout
    # This ensures CTRL+C can interrupt even during long operations
    try:
        with mic as source:
            print("Listening...")

            # Use configurable noise sampling duration for better filtering
            calibrate_duration = AMBIENT_NOISE_DURATION
            if recalibrate:
                # Use a longer duration for explicit recalibration
                calibrate_duration = max(AMBIENT_NOISE_DURATION, 5.0)
                print(f"Recalibrating microphone for {calibrate_duration} seconds...")

            # Use shorter durations for ambient noise calibration to ensure interruptibility
            calibration_chunk_size = 0.5  # seconds
            chunks_needed = int(calibrate_duration / calibration_chunk_size)

            # Break calibration into smaller chunks that can be interrupted
            for i in range(chunks_needed):
                try:
                    recognizer.adjust_for_ambient_noise(
                        source, duration=calibration_chunk_size
                    )
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt detected during calibration")
                    raise
                except Exception as e:
                    print(f"Error during calibration chunk {i+1}: {e}")
                    # Continue with other chunks

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
            except Exception as e:
                print(f"Error during listening: {e}")
                return None

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
        except Exception as e:
            print(f"Unexpected error during recognition: {e}")
            return None
    except KeyboardInterrupt:
        # Re-raise for proper exit handling
        print("\nKeyboard interrupt detected during speech recognition")
        raise
    except Exception as e:
        print(f"Unexpected error in speech recognition: {e}")
        return None
