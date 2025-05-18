"""
Speech Interface Module for PAN (Cross-Platform)

This module provides text-to-speech and speech recognition capabilities for PAN.
On Windows, it uses SAPI5 directly for maximum stability. On Linux, it uses espeak.
For speech recognition, it uses Google Speech API by default and falls back to VOSK (offline).
"""

import speech_recognition as sr
import threading
import queue
import time
import traceback
import platform
from pan_emotions import pan_emotions
from pan_config import DEFAULT_VOICE_RATE, DEFAULT_VOICE_VOLUME
import win32com.client  # For SAPI5 on Windows
from vosk import Model, KaldiRecognizer
import json
import os

# Detect OS
is_windows = platform.system().lower() == "windows"
is_linux = platform.system().lower() == "linux"

# Path to the VOSK model (adjust to your directory)
VOSK_MODEL_PATH = "vosk_model"

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

class SpeakManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.speaking_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self._init_engine()

    def _init_engine(self):
        """Initialize the TTS engine."""
        print("[SpeakManager] Initializing TTS engine...")
        try:
            if is_windows:
                self.engine = win32com.client.Dispatch("SAPI.SpVoice")
                print("[SpeakManager] Using SAPI5 (Windows)")
            elif is_linux:
                import pyttsx3
                self.engine = pyttsx3.init(driverName='espeak')
                print("[SpeakManager] Using espeak (Linux)")
            else:
                print("[TTS ERROR] Unsupported platform.")
                self.engine = None
        except Exception as e:
            print(f"[TTS ERROR] Failed to initialize TTS engine: {e}")
            self.engine = None

    def set_voice_by_mood(self, mood=None):
        """Adjust TTS voice settings based on mood."""
        if not mood:
            mood = pan_emotions.get_mood()
        settings = emotion_voices.get(mood, emotion_voices['neutral'])
        
        if is_windows:
            self.engine.Rate = settings['rate'] - 10  # SAPI uses different rate scale
            self.engine.Volume = int(settings['volume'] * 100)
        elif is_linux:
            self.engine.setProperty('rate', settings['rate'])
            self.engine.setProperty('volume', settings['volume'])

    def speak(self, text, mood_override=None):
        """Queue text for speaking."""
        self.queue.put((text, mood_override or pan_emotions.get_mood()))

    def _worker(self):
        """TTS worker thread - always running."""
        while True:
            text, mood = self.queue.get()
            try:
                self._speak_with_recovery(text, mood)
            except Exception as e:
                print(f"[TTS ERROR] Fatal Error in TTS Worker: {e}")
                traceback.print_exc()
                self._init_engine()  # Re-initialize on failure
            finally:
                self.queue.task_done()

    def _speak_with_recovery(self, text, mood):
        """Speak with automatic recovery."""
        with self.lock:
            self.set_voice_by_mood(mood)
            print(f"[SpeakManager] Speaking with mood: {mood}")
            if is_windows:
                self.engine.Speak(text)
            elif is_linux:
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                print(f"[TTS ERROR] Unsupported platform.")

# Global instance of SpeakManager to be used throughout the application
speak_manager = SpeakManager()

def speak(text, mood_override=None):
    """Public function to speak text."""
    try:
        speak_manager.speak(text, mood_override)
    except Exception as e:
        print(f"[TTS ERROR] Reinitializing TTS due to error: {e}")
        speak_manager._init_engine()
        speak_manager.speak(text, mood_override)

def listen_to_user(timeout=5, phrase_time_limit=10):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("Processing audio...")
            try:
                text = recognizer.recognize_google(audio)
                print(f"You said (Google): {text}")
                return text
            except:
                print("[INFO] Google failed, using VOSK (offline)...")
                if not os.path.exists(VOSK_MODEL_PATH):
                    print("VOSK model not found. Please download the VOSK model.")
                    return None

                model = Model(VOSK_MODEL_PATH)
                recognizer_vosk = KaldiRecognizer(model, 16000)
                recognizer_vosk.AcceptWaveform(audio.get_raw_data())
                result = json.loads(recognizer_vosk.Result())
                text = result.get("text", "")
                print(f"You said (VOSK): {text}")
                return text
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start.")
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
        return None
