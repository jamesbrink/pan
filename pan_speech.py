"""
Speech Interface Module for PAN (Cross-Platform)

This module provides text-to-speech and speech recognition capabilities for PAN.
On Windows, it uses SAPI5 directly for maximum stability. On Linux, it uses espeak.
For speech recognition, it uses Google Speech API by default and falls back to VOSK (offline).
"""

import platform
import queue
import threading
import time
import traceback

import speech_recognition as sr

from pan_config import DEFAULT_VOICE_VOLUME
from pan_emotions import pan_emotions

# Import Windows-specific modules conditionally
try:
    import win32com.client  # For SAPI5 on Windows
except ImportError:
    # Not on Windows or module not installed
    win32com = None

# Import VOSK conditionally for offline recognition if needed
# (currently not used but kept for potential future implementation)
try:
    pass  # from vosk import KaldiRecognizer, Model
except ImportError:
    pass  # VOSK not installed - local recognition will not be available

# Detect OS
is_windows = platform.system().lower() == "windows"
is_linux = platform.system().lower() == "linux"

# Path to the VOSK model (adjust to your directory)
VOSK_MODEL_PATH = "vosk_model"

# Voice parameters for different emotional states
emotion_voices = {
    "happy": {"rate": 0, "volume": DEFAULT_VOICE_VOLUME + 0.1},
    "neutral": {"rate": 0, "volume": DEFAULT_VOICE_VOLUME},
    "sad": {"rate": -1, "volume": DEFAULT_VOICE_VOLUME - 0.2},
    "angry": {"rate": 1, "volume": DEFAULT_VOICE_VOLUME + 0.1},
}


class SpeakManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self._init_engine()
        self.interrupt_speaking = (
            threading.Event()
        )  # Interrupt Event for stopping speech
        self.speech_count = 0
        self.speaking_event = threading.Event()

    def _init_engine(self):
        print("[SpeakManager] Initializing TTS engine...")
        if is_windows and win32com is not None:
            self.engine = win32com.client.Dispatch("SAPI.SpVoice")
            print("[SpeakManager] Using SAPI5 (Windows)")
        elif is_linux:
            import pyttsx3

            self.engine = pyttsx3.init(driverName="espeak")
            print("[SpeakManager] Using espeak (Linux)")
        else:
            # Fallback for non-Windows/Linux or when win32com not available
            import pyttsx3

            self.engine = pyttsx3.init()
            print("[SpeakManager] Using pyttsx3 fallback")

            # On macOS, select the best available voice
            if platform.system() == "Darwin":
                # Try to get voices
                voices = self.engine.getProperty("voices")
                if voices and len(voices) > 1:
                    # Find a premium voice (usually second in the list)
                    self.engine.setProperty("voice", voices[1].id)

    def set_voice_by_mood(self, mood=None):
        """Adjust TTS voice settings based on mood."""
        if not mood:
            mood = pan_emotions.get_mood()
        settings = emotion_voices.get(mood, emotion_voices["neutral"])

        if is_windows:
            # SAPI5 Rate (-2 to +2) - Stable range
            scaled_rate = max(-2, min(2, settings["rate"]))
            self.engine.Rate = scaled_rate
            self.engine.Volume = int(settings["volume"] * 100)
            print(
                f"[SpeakManager] SAPI5 Rate (Corrected): {self.engine.Rate}, Volume: {self.engine.Volume}"
            )

        elif is_linux:
            # espeak (150 for natural speed)
            adjusted_rate = int(150 + (settings["rate"] * 10))
            self.engine.setProperty("rate", adjusted_rate)
            self.engine.setProperty("volume", settings["volume"])
            print(
                f"[SpeakManager] espeak Rate: {adjusted_rate}, Volume: {settings['volume']}"
            )

    def speak(self, text, mood_override=None):
        """Queue text for speaking."""
        self.queue.put((text, mood_override or pan_emotions.get_mood()))

    def stop(self):
        """Immediately stop any ongoing speech."""
        self.interrupt_speaking.set()  # Trigger interrupt event
        with self.lock:
            if is_windows and win32com is not None:
                self.engine.Speak("", 3)  # SAPI5: Immediate stop
            else:
                # For Linux and fallback case
                self.engine.stop()  # Stop current speech
        print("[SpeakManager] Speech interrupted.")

    def _worker(self):
        """TTS Worker Thread - Continuous Processing"""
        while True:
            text, mood = self.queue.get()
            self.interrupt_speaking.clear()  # Reset interrupt flag
            try:
                self._speak_with_recovery(text, mood)
            except AttributeError as e:
                print(f"[TTS ERROR] TTS engine not properly initialized: {e}")
                traceback.print_exc()
                self._init_engine()  # Re-initialize on failure
            except NotImplementedError as e:
                print(f"[TTS ERROR] TTS method not available for this platform: {e}")
                traceback.print_exc()
                # Try to initialize with fallback method
                self._init_engine()
            except RuntimeError as e:
                print(f"[TTS ERROR] Runtime error in TTS engine: {e}")
                traceback.print_exc()
                self._init_engine()  # Re-initialize on failure
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"[TTS ERROR] Unexpected error in TTS Worker: {e}")
                traceback.print_exc()
                self._init_engine()  # Re-initialize on failure
            finally:
                self.queue.task_done()

    def _process_long_sentence(self, sentence, max_chunk_size):
        """Process a long sentence by splitting on commas"""
        chunks = []
        comma_parts = sentence.split(",")
        sub_chunk = ""

        for part in comma_parts:
            if len(sub_chunk) + len(part) <= max_chunk_size:
                sub_chunk += part + ","
            else:
                if sub_chunk:
                    chunks.append(sub_chunk.strip())
                sub_chunk = part + ","

        if sub_chunk:
            chunks.append(sub_chunk.strip())
        return chunks

    def _process_sentences_into_chunks(self, sentences, max_chunk_size):
        """Process sentences into appropriately sized chunks"""
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += " " + sentence
            else:
                # If current chunk is not empty, add it to chunks
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If sentence is longer than max_chunk_size, split by commas
                if len(sentence) > max_chunk_size:
                    chunks.extend(self._process_long_sentence(sentence, max_chunk_size))
                else:
                    current_chunk = sentence

        # Add any remaining text in current_chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    def _chunk_text(self, text):
        """
        Break long text into smaller, speakable chunks.

        Args:
            text (str): The text to chunk

        Returns:
            list: List of text chunks to speak
        """
        # Check if text needs to be chunked at all
        if not text:
            return []

        # Platform-specific chunk size
        max_chunk_size = 300 if platform.system() == "Darwin" else 500

        # If text is shorter than max chunk size, return as single chunk
        if len(text) <= max_chunk_size:
            return [text]

        # First, split by common end-of-sentence punctuation
        sentences = []

        # Split into sentences first (by . ! ?)
        for sentence in text.replace("!", ".").replace("?", ".").split("."):
            if sentence.strip():
                sentences.append(sentence.strip() + ".")

        return self._process_sentences_into_chunks(sentences, max_chunk_size)

    def _speak_chunk(self, chunk, _):  # Using _ for unused mood parameter
        """Speak a single chunk of text"""
        if is_windows and win32com is not None:
            self.engine.Speak(chunk)
        else:
            # For Linux and fallback case
            self.engine.say(chunk)
            self.engine.runAndWait()

        # After speaking, calculate sleep time based on platform
        if platform.system() == "Darwin":
            # macOS needs less time between chunks
            time.sleep(0.1)
        else:
            time.sleep(0.2)

    def _speak_with_recovery(self, text, mood):
        """Speak with Automatic Recovery and Interruptibility"""
        with self.lock:
            self.set_voice_by_mood(mood)
            print(f"[SpeakManager] Speaking with mood: {mood}")

            # Set speaking event
            self.speaking_event.set()

            # Chunk text for better control and smoother speech
            chunks = self._chunk_text(text)

            for chunk in chunks:
                # Check if speech should be interrupted
                if self.interrupt_speaking.is_set():
                    print("[SpeakManager] Speech interrupted mid-chunking.")
                    break

                self._speak_chunk(chunk, mood)
                self.speech_count += 1

            # Clear speaking event when done
            self.speaking_event.clear()


# Global instance of SpeakManager
speak_manager = SpeakManager()


def speak(text, mood_override=None):
    """Public function to speak text."""
    speak_manager.speak(text, mood_override)


def stop_speaking():
    """Public function to immediately stop speaking."""
    speak_manager.stop()


def test_microphone():
    """
    Test if the microphone is available and properly working.

    This function tests if the microphone can be initialized,
    checks calibration, and ensures proper permissions.

    Returns:
        bool: True if the microphone is working properly, False otherwise
    """
    print("Testing microphone...")

    # First, check if microphones are available
    try:
        microphone_names = sr.Microphone.list_microphone_names()
        if not microphone_names:
            print("[ERROR] No microphones detected.")
            return False
        print(
            f"Detected {len(microphone_names)} microphone(s): {', '.join(microphone_names[:3])}"
        )

        # Try to initialize a microphone
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Microphone initialized successfully.")

            # Try to calibrate
            print("Calibrating microphone...")
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print(
                f"Calibration complete. Energy threshold: {recognizer.energy_threshold}"
            )
            return True

    except OSError as e:
        print(f"[ERROR] Microphone error: {e}")
        print(
            "This could be a permissions issue. Make sure to grant microphone access."
        )
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[ERROR] Unexpected error testing microphone: {e}")
        return False


def recalibrate_microphone(calibrate_duration=5.0):
    """
    Perform a thorough microphone calibration to improve recognition accuracy.

    This function performs multiple calibration steps in small chunks to improve
    the microphone's energy threshold and noise cancellation.

    Args:
        calibrate_duration (float): Total duration in seconds for calibration

    Returns:
        bool: True if calibration succeeded, False if it failed
    """
    print(f"Recalibrating microphone (duration: {calibrate_duration}s)...")

    # Make sure we calibrate for at least 5 seconds
    calibrate_duration = max(calibrate_duration, 5.0)

    # Use small chunks (0.5 seconds each) for more granular calibration
    chunk_size = 0.5
    num_chunks = int(calibrate_duration / chunk_size)

    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            initial_threshold = recognizer.energy_threshold
            print(
                f"Starting calibration. Initial energy threshold: {initial_threshold}"
            )

            # Perform calibration in chunks
            for i in range(num_chunks):
                print(f"Calibration step {i+1}/{num_chunks}...")
                recognizer.adjust_for_ambient_noise(source, duration=chunk_size)
                print(f"Current energy threshold: {recognizer.energy_threshold}")

            final_threshold = recognizer.energy_threshold
            print(f"Calibration complete. Final energy threshold: {final_threshold}")
            return True

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[ERROR] Calibration failed: {e}")
        return False


def _check_macos_microphone_permissions():
    """Check microphone permissions specifically on macOS systems"""
    # Only check on macOS systems
    if platform.system() != "Darwin":
        return True
    # Check if we've already verified permissions in this session
    if not hasattr(sr.Microphone, "_checked_macos_permissions"):
        try:
            microphone_names = sr.Microphone.list_microphone_names()
            if not microphone_names:
                print("[ERROR] No microphones detected. MACOS PERMISSION ERROR.")
                print("Please grant microphone permissions in System Preferences.")
                sr.Microphone._checked_macos_permissions = False
                return False
            # Set class attribute to avoid repeated checking
            sr.Microphone._checked_macos_permissions = True
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Microphone permission error: {e}")
            print("Please grant microphone permissions in System Preferences.")
            sr.Microphone._checked_macos_permissions = False
            return False
    return True


def _listen_and_detect_keyword():
    """Core implementation of keyword detection logic"""
    result = False
    # Initialize recognizer
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for keyword...")
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        try:
            # Listen for audio
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            # Convert to text
            text = recognizer.recognize_google(audio).lower()
            print(f"Heard: {text}")
            # Check if keyword/wake word is in the text
            from pan_config import ASSISTANT_NAME

            keyword = ASSISTANT_NAME.lower()
            result = keyword in text
        except sr.WaitTimeoutError:
            print("Keyword listening timed out.")
        except sr.UnknownValueError:
            print("No speech detected.")
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Unexpected error in keyword detection: {e}")
    return result


def listen_for_keyword():
    """
    Listen specifically for the wake word/keyword.

    This function listens for a keyword (typically the assistant name)
    and checks if microphone permissions are properly set up on macOS.

    Returns:
        bool: True if keyword was detected, False otherwise
    """
    # First check permissions on macOS
    if not _check_macos_microphone_permissions():
        return False
    # Then perform the actual listening and keyword detection
    return _listen_and_detect_keyword()


def listen_to_user(timeout=5, phrase_time_limit=10, recalibrate=False):
    """
    Listen for user speech and convert to text.

    Args:
        timeout (int): Maximum time to wait for speech to start (seconds)
        phrase_time_limit (int): Maximum speech duration (seconds)
        recalibrate (bool): Whether to perform detailed microphone calibration

    Returns:
        str or None: Recognized text or None if recognition failed
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")

        # Calibrate microphone - either quick or thorough calibration
        calibrate_duration = 5.0 if recalibrate else 1.5

        # Do calibration in small chunks for better results
        chunk_size = 0.5
        num_chunks = int(calibrate_duration / chunk_size)
        for _ in range(num_chunks):
            recognizer.adjust_for_ambient_noise(source, duration=chunk_size)

        try:
            audio = recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
            print("Processing audio...")
            text = recognizer.recognize_google(audio)
            print(f"You said (Google): {text}")
            return text
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start.")
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
        return None
