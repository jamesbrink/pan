"""
Speech Interface Module for PAN (Cross-Platform)

This module provides text-to-speech and speech recognition capabilities for PAN.
It supports both Windows (SAPI) and Linux (espeak) for TTS, and provides robust
speech recognition with Google Speech API.
"""

import os
import platform
import queue
import sys
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
    ASSISTANT_NAME,
    DEFAULT_VOICE_RATE,
    DEFAULT_VOICE_VOLUME,
    ENERGY_THRESHOLD,
    PHRASE_TIME_LIMIT,
    SPEECH_RECOGNITION_TIMEOUT,
    USE_DYNAMIC_ENERGY_THRESHOLD,
    # The following imports are used in functions that are called from main.py
    # but pylint doesn't detect this usage
    # pylint: disable=unused-import
    CONTINUOUS_LISTENING,  # Used in listen_for_keyword when called from main.py
    KEYWORD_ACTIVATION_THRESHOLD,  # Used in listen_for_keyword when called from main.py
    USE_KEYWORD_ACTIVATION,  # Used in listen_for_keyword when called from main.py
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

        # TTS reliability tracking
        self.last_restart_time = time.time()  # Track last engine restart time
        self.tts_attempt_count = 0  # Track consecutive TTS failures
        self.last_tts_attempt_time = time.time()  # Time of last TTS attempt

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

    def _try_system_command_tts(self, text):
        """
        Try to use system commands for TTS as a more reliable fallback.

        Args:
            text (str): The text to speak

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if is_macos:
                # Use macOS 'say' command which is very reliable
                import subprocess

                subprocess.run(["say", text], check=True)
                return True
            elif is_linux:
                # Try espeak on Linux
                import subprocess

                subprocess.run(["espeak", text], check=True)
                return True
            elif is_windows and self.sapi_engine:
                # Already handled in _speak_chunk
                return False
            return False
        except Exception as e:
            print(f"System command TTS failed: {e}")
            return False

    def _speak_chunk(self, chunk, mood):
        """
        Speak a single chunk of text with the given mood.

        Uses platform-specific optimizations and fallbacks as needed.

        Args:
            chunk (str): The text chunk to speak
            mood (str): The emotional mood to apply to the voice
        """
        # Track attempts to avoid infinite retry loops
        if not hasattr(self, "tts_attempt_count"):
            self.tts_attempt_count = 0

        # Reset attempt count if it's been a while
        if hasattr(self, "last_tts_attempt_time"):
            if time.time() - self.last_tts_attempt_time > 10:
                self.tts_attempt_count = 0
        self.last_tts_attempt_time = time.time()

        # Increment attempt count
        self.tts_attempt_count += 1

        # If we've tried several times, go directly to fallback
        if self.tts_attempt_count > 3:
            # Use regular string instead of f-string since there's no interpolation
            print("[SpeakManager] Too many failed TTS attempts, using system fallback")
            if self._try_system_command_tts(chunk):
                self.tts_attempt_count = 0
                return
            else:
                print(f"[SpeakManager] TTS Fallback (text only): {chunk}")
                self.tts_attempt_count = 0
                return

        # Use Windows SAPI if available
        if is_windows and self.sapi_engine:
            try:
                print("[SpeakManager] Using Windows SAPI for TTS chunk.")
                self.sapi_engine.Speak(chunk)
                self.tts_attempt_count = 0  # Reset on success
                return
            except (AttributeError, RuntimeError) as sapi_error:
                print(f"SAPI TTS failed: {sapi_error}")
                # Fall through to next attempt

        # Try with our regular engine
        try:
            if hasattr(self, "engine") and self.engine is not None:
                # Add the text to the engine
                self.engine.say(chunk)

                # Try to run the speech
                try:
                    self.engine.runAndWait()
                    self.tts_attempt_count = 0  # Reset on success
                    return
                except RuntimeError as loop_error:
                    if "run loop already started" in str(loop_error):
                        print(
                            "[SpeakManager] Detected run loop error, trying system fallback"
                        )
                        # Try system command TTS which is more reliable
                        if self._try_system_command_tts(chunk):
                            self.tts_attempt_count = 0  # Reset on success
                            return
                    else:
                        print(f"TTS runAndWait error: {loop_error}")
            else:
                print("[SpeakManager] Engine not available")
        except Exception as tts_error:
            print(f"TTS error: {tts_error}")

        # If we get here, try to recreate the engine and try again, but only if
        # it's been more than 5 seconds since our last engine init
        current_time = time.time()
        should_reinit = False

        if hasattr(self, "last_restart_time"):
            if current_time - self.last_restart_time > 5.0:
                should_reinit = True
        else:
            should_reinit = True

        if should_reinit:
            print("[SpeakManager] Reinitializing speech engine")
            try:
                self._init_engine()
                self.last_restart_time = current_time

                # Try one more time with the new engine
                if hasattr(self, "engine") and self.engine is not None:
                    self.set_voice_by_mood(mood)
                    self.engine.say(chunk)
                    try:
                        self.engine.runAndWait()
                        self.tts_attempt_count = 0  # Reset on success
                        return
                    except Exception as retry_error:
                        print(f"TTS retry failed: {retry_error}")
            except Exception as init_error:
                print(f"Engine reinitialization failed: {init_error}")

        # If all else fails, use system TTS or just print
        if self._try_system_command_tts(chunk):
            self.tts_attempt_count = 0  # Reset on success
        else:
            # Last resort: just print the text
            print(f"[SpeakManager] TTS Fallback (text only): {chunk}")

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

    # Initialize the microphone with better error handling
    try:
        # On macOS, check if we've already listed microphones during startup
        # If not, provide diagnostics here as well
        if is_macos and not hasattr(sr.Microphone, "_checked_macos_permissions"):
            print("Checking available microphones for keyword detection:")
            mic_list = sr.Microphone.list_microphone_names()

            # Store a flag to avoid repeating this check
            sr.Microphone._checked_macos_permissions = True

            if not mic_list:
                print("No microphones detected! Check system permissions.")
                print("\n*** MACOS PERMISSION ERROR ***")
                print(
                    "You need to grant microphone permissions for wake word detection."
                )
                print(
                    "1. Open System Preferences > Security & Privacy > Privacy > Microphone"
                )
                print(
                    "2. Make sure Terminal or your IDE has permission to access the microphone"
                )
                print("3. Restart the application after granting permissions")
                print("*****************************\n")
                return False

        # Attempt to initialize the microphone
        mic = sr.Microphone()
    except (OSError, IOError) as e:
        print(f"Error initializing microphone for keyword detection: {e}")

        if is_macos:
            print("\n*** MACOS PERMISSION ERROR ***")
            print("This error often occurs when macOS has denied microphone access.")
            print(
                "1. Open System Preferences > Security & Privacy > Privacy > Microphone"
            )
            print(
                "2. Make sure Terminal or your IDE has permission to access the microphone"
            )
            print("3. Restart the application after granting permissions")
            print("*****************************\n")
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
            recognizer.energy_threshold = max(
                ENERGY_THRESHOLD - 50, 200
            )  # More sensitive

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
                if (
                    word.startswith(assistant_name_lower)
                    or word.endswith(assistant_name_lower)
                    or assistant_name_lower in word
                ):
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


def listen_to_user(timeout=None, recalibrate=False, quiet_mode=False):
    """
    Listen for user speech input and convert it to text.

    Uses the speech_recognition library to capture audio from the microphone,
    then uses Google's speech recognition service to convert it to text.

    Args:
        timeout (int, optional): Maximum seconds to wait for speech to begin.
                               If None, uses SPEECH_RECOGNITION_TIMEOUT from config.
        recalibrate (bool): Force recalibration of ambient noise levels
        quiet_mode (bool): Reduce console output for retry attempts

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
        # Only check microphones once per session by using a class flag
        if not hasattr(listen_to_user, "_microphone_checked"):
            listen_to_user._microphone_checked = True

            # List available microphones to help with diagnostics
            if is_macos:
                print("Checking available microphones:")
                mic_list = sr.Microphone.list_microphone_names()
                if mic_list:
                    for i, mic_name in enumerate(mic_list):
                        print(f"  {i}: {mic_name}")
                    print(f"Using default microphone: {mic_list[0]}")
                else:
                    print("No microphones detected! Check system permissions.")
                    print("\n*** MACOS PERMISSION ERROR ***")
                    print(
                        "If you're on macOS, you may need to grant microphone permissions."
                    )
                    print(
                        "1. Open System Preferences > Security & Privacy > Privacy > Microphone"
                    )
                    print(
                        "2. Make sure Terminal or your IDE has permission to access the microphone"
                    )
                    print("3. Restart the application after granting permissions")
                    print("*****************************\n")
                    return None

        # Attempt to initialize the microphone
        mic = sr.Microphone()
    except (OSError, IOError) as e:
        print(f"Error initializing microphone: {e}")

        if is_macos:
            print("\n*** MACOS PERMISSION ERROR ***")
            print("This error often occurs when macOS has denied microphone access.")
            print(
                "1. Open System Preferences > Security & Privacy > Privacy > Microphone"
            )
            print(
                "2. Make sure Terminal or your IDE has permission to access the microphone"
            )
            print("3. Restart the application after granting permissions")
            print("*****************************\n")
        return None

    # Make audio capture interruptible with a short timeout
    # This ensures CTRL+C can interrupt even during long operations
    try:
        with mic as source:
            if not quiet_mode:
                print("Listening...")

            # Use configurable noise sampling duration for better filtering
            calibrate_duration = AMBIENT_NOISE_DURATION
            if recalibrate:
                # Use a longer duration for explicit recalibration
                calibrate_duration = max(AMBIENT_NOISE_DURATION, 5.0)
                # Only show this message on explicit recalibration to avoid excessive output
                if not quiet_mode:
                    print(
                        f"Recalibrating microphone for {calibrate_duration} seconds..."
                    )

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
                    if not quiet_mode:
                        print(f"Error during calibration chunk {i+1}: {e}")

                    # On macOS, this is often a permission issue
                    if (
                        is_macos and i == 0 and not quiet_mode
                    ):  # Only show on first error and not in quiet mode
                        print("\n*** MACOS MICROPHONE CALIBRATION ERROR ***")
                        print(
                            "This error might be caused by microphone permission issues."
                        )
                        print(
                            "1. Open System Preferences > Security & Privacy > Privacy > Microphone"
                        )
                        print(
                            "2. Make sure Terminal or your IDE has permission to access the microphone"
                        )
                        print(
                            "3. Check your microphone is not being used by another application"
                        )
                        print(
                            "4. Try unplugging and reconnecting any external microphones"
                        )
                        print(
                            "5. Try restarting the application after fixing permissions"
                        )
                        print("*****************************\n")

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
                if not quiet_mode:
                    print("Listening timed out while waiting for phrase to start")
                return None
            except KeyboardInterrupt:
                # Re-raise for proper exit handling
                print("\nKeyboard interrupt detected during listening")
                raise
            except Exception as e:
                if not quiet_mode:
                    print(f"Error during listening: {e}")
                return None

        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            if not quiet_mode:
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


def test_microphone():
    """
    Test microphone access and provide detailed diagnostic information.

    This function tests microphone access and prints detailed diagnostic
    information to help troubleshoot permission issues, especially on macOS.

    Returns:
        bool: True if microphone test was successful, False otherwise
    """
    print("\n" + "=" * 60)
    print(" " * 15 + "MICROPHONE ACCESS TEST")
    print("=" * 60)

    # System information
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python version: {platform.python_version()}")

    # Check if running in a virtual environment
    in_virtualenv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    print(f"Running in virtual environment: {in_virtualenv}")

    # Check if we're running in Nix environment
    in_nix = "IN_NIX_SHELL" in os.environ or "NIX_PROFILE" in os.environ
    print(f"Running in Nix environment: {in_nix}")

    success = True
    try:
        # List available microphones
        print("\nAvailable microphones:")
        mic_list = sr.Microphone.list_microphone_names()
        if mic_list:
            for i, mic_name in enumerate(mic_list):
                print(f"  {i}: {mic_name}")
        else:
            print("  No microphones detected!")
            print("\n  >>> ISSUE DETECTED: No microphones available <<<")
            success = False

        # Try to initialize the microphone
        print("\nTrying to initialize microphone...")
        try:
            mic = sr.Microphone()
            print("  Microphone initialized successfully")
        except (OSError, IOError) as e:
            print(f"  ERROR: Could not initialize microphone: {e}")
            print("\n  >>> ISSUE DETECTED: Microphone initialization failed <<<")
            success = False

        # Try to adjust for ambient noise
        if success:
            print("\nTrying to adjust for ambient noise...")
            try:
                recognizer = sr.Recognizer()
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1.0)
                print(f"  Success! Energy threshold: {recognizer.energy_threshold:.1f}")
            except Exception as e:
                print(f"  ERROR: Could not calibrate microphone: {e}")
                print("\n  >>> ISSUE DETECTED: Microphone calibration failed <<<")
                success = False

        # Try to record a short clip
        if success:
            print("\nTrying to record 3 seconds of audio...")
            try:
                recognizer = sr.Recognizer()
                with mic as source:
                    print("  Recording for 3 seconds...")
                    audio = recognizer.record(source, duration=3)
                print("  Successfully recorded audio!")

                # Try to recognize the audio (might be empty)
                try:
                    print("\nTrying to recognize recorded audio...")
                    text = recognizer.recognize_google(audio)
                    print(f"  Recognized: '{text}'")
                except sr.UnknownValueError:
                    print(
                        "  No speech detected in the recording (this is normal for silent environments)"
                    )
                except Exception as e:
                    print(f"  Recognition error: {e}")
            except Exception as e:
                print(f"  ERROR: Could not record audio: {e}")
                print("\n  >>> ISSUE DETECTED: Audio recording failed <<<")
                success = False
    except Exception as e:
        print(f"\nERROR during microphone test: {e}")
        success = False

    # Provide a conclusion
    print("\nTest conclusion:")
    if success:
        print("✅ All microphone tests PASSED!")
        print("   Speech recognition should work correctly.")
    else:
        print("❌ Some microphone tests FAILED!")

        if platform.system() == "Darwin":  # macOS
            print("\nOn macOS, microphone issues are usually permission-related:")
            print(
                "1. Go to System Preferences > Security & Privacy > Privacy > Microphone"
            )
            print("2. Ensure that Terminal or your IDE has microphone access")
            print(
                "3. You may need to quit Terminal/IDE completely and restart after changing permissions"
            )
            print(
                "4. If using Nix, try running the application from a different Terminal window"
            )
            print("5. Check if your microphone is being used by another application")
        else:
            print("\nTroubleshooting tips:")
            print("1. Check if your microphone is properly connected")
            print("2. Check if your microphone is being used by another application")
            print("3. Try a different microphone if available")
            print(
                "4. Check system sound settings to ensure the correct microphone is selected"
            )

    print("=" * 60)
    return success
