"""
Speech Interface Module for PAN

This module provides text-to-speech and speech recognition capabilities for PAN.
It adjusts speech parameters based on emotional state, handles chunking of long
utterances, and provides robust speech recognition with error handling.
"""

import pyttsx3
import speech_recognition as sr
import threading
import queue
import time
import traceback
from pan_emotions import pan_emotions
from pan_config import DEFAULT_VOICE_RATE, DEFAULT_VOICE_VOLUME

# Try to import Windows SAPI for better speech synthesis on Windows
try:
    import win32com.client
    has_sapi = True
except ImportError:
    has_sapi = False

# Voice parameters for different emotional states
emotion_voices = {
    'happy': {'rate': DEFAULT_VOICE_RATE + 20, 'volume': DEFAULT_VOICE_VOLUME + 0.1},
    'excited': {'rate': DEFAULT_VOICE_RATE + 40, 'volume': DEFAULT_VOICE_VOLUME + 0.1},
    'neutral': {'rate': DEFAULT_VOICE_RATE, 'volume': DEFAULT_VOICE_VOLUME},
    'sad': {'rate': DEFAULT_VOICE_RATE - 20, 'volume': DEFAULT_VOICE_VOLUME - 0.2},
    'angry': {'rate': DEFAULT_VOICE_RATE + 40, 'volume': DEFAULT_VOICE_VOLUME + 0.1},
    'scared': {'rate': DEFAULT_VOICE_RATE - 30, 'volume': DEFAULT_VOICE_VOLUME - 0.3},
    'calm': {'rate': DEFAULT_VOICE_RATE - 10, 'volume': DEFAULT_VOICE_VOLUME - 0.1},
    'curious': {'rate': DEFAULT_VOICE_RATE + 10, 'volume': DEFAULT_VOICE_VOLUME},
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
            self.engine = pyttsx3.init(driverName='espeak')
        except Exception as e:
            print(f"Failed to init with espeak driver: {e}")
            try:
                # Fall back to default initialization
                self.engine = pyttsx3.init()
            except Exception as e:
                print(f"Failed to init TTS engine: {e}")
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
        settings = emotion_voices.get(mood, emotion_voices['neutral'])
        self.engine.setProperty('rate', settings['rate'])
        self.engine.setProperty('volume', settings['volume'])

    def _chunk_text(self, text):
        """
        Split long text into smaller chunks for better TTS processing.
        
        Args:
            text (str): The text to split into chunks
            
        Returns:
            list: A list of text chunks, each below MAX_CHUNK_LENGTH
        """
        import re
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) <= MAX_CHUNK_LENGTH:
                current += (sentence + " ")
            else:
                chunks.append(current.strip())
                current = sentence + " "
        if current:
            chunks.append(current.strip())
        return chunks

    def _create_dummy_engine(self):
        """Create a dummy engine that just prints text when TTS fails."""
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
            except Exception as e:
                print(f"SAPI TTS failed: {e}")
        try:
            self.set_voice_by_mood(mood)
            self.engine.say(chunk)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS error in chunk: {e}")
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

            except Exception:
                print("TTS error occurred in worker:")
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
    # For now, we'll just return an empty string
    return ""


def listen_to_user(timeout=5):
    """
    Listen for user speech input and convert it to text.
    
    Uses the speech_recognition library to capture audio from the microphone,
    then uses Google's speech recognition service to convert it to text.
    
    Args:
        timeout (int): Maximum seconds to wait for speech to begin
        
    Returns:
        str or None: Transcribed speech text if successful, None if unsuccessful
        
    Raises:
        KeyboardInterrupt: Propagates keyboard interrupt for proper handling
    """
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    try:
        with mic as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1.5)
            try:
                audio = recognizer.listen(source, timeout=timeout)
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase to start")
                return None
            except KeyboardInterrupt:
                # Re-raise for proper exit handling
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
        raise
