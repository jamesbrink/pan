"""
Speech Interface Module for PAN (Cross-Platform)

This module provides text-to-speech and speech recognition capabilities for PAN.
It supports both Windows (SAPI) and Linux (espeak) for TTS, and provides robust 
speech recognition with Google Speech API.
"""

import pyttsx3
import speech_recognition as sr
import threading
import queue
import time
import traceback
import platform
from pan_emotions import pan_emotions
from pan_config import DEFAULT_VOICE_RATE, DEFAULT_VOICE_VOLUME

# Detect OS
is_windows = platform.system().lower() == "windows"
is_linux = platform.system().lower() == "linux"

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
        self._init_engine()
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.speaking_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _init_engine(self):
        print("[SpeakManager] Initializing pyttsx3 engine")
        try:
            if is_windows:
                self.engine = pyttsx3.init(driverName='sapi5')
            elif is_linux:
                self.engine = pyttsx3.init(driverName='espeak')
            else:
                self.engine = pyttsx3.init()  # Default cross-platform
        except Exception as e:
            print(f"Failed to init TTS engine: {e}")
            self._create_dummy_engine()

    def _create_dummy_engine(self):
        class DummyEngine:
            def say(self, text): print(f"[TTS FALLBACK] Speaking: {text}")
            def runAndWait(self): pass
            def stop(self): pass
            def setProperty(self, prop, value): pass

        self.engine = DummyEngine()
        print("[SpeakManager] Using fallback dummy TTS engine")

    def set_voice_by_mood(self, mood=None):
        if not mood:
            mood = pan_emotions.get_mood()
        settings = emotion_voices.get(mood, emotion_voices['neutral'])
        self.engine.setProperty('rate', settings['rate'])
        self.engine.setProperty('volume', settings['volume'])

    def speak(self, text, mood_override=None):
        self.queue.put((text, mood_override or pan_emotions.get_mood()))

    def _worker(self):
        while True:
            text, mood = self.queue.get()
            try:
                self._speak_with_recovery(text, mood)
            except Exception:
                print("[TTS ERROR] Fatal Error in TTS Worker.")
                traceback.print_exc()
                self._init_engine()  # Re-initialize on failure
            finally:
                self.queue.task_done()

    def _speak_with_recovery(self, text, mood):
        with self.lock:
            self.engine.stop()
            self._init_engine()
            self.engine.setProperty('rate', emotion_voices.get(mood, emotion_voices['neutral'])['rate'])
            self.engine.setProperty('volume', emotion_voices.get(mood, emotion_voices['neutral'])['volume'])

            print("[SpeakManager] Speaking started")
            chunks = self._chunk_text(text)
            for chunk in chunks:
                self.engine.say(chunk)
                self.engine.runAndWait()

            print("[SpeakManager] Speaking ended")

    def _chunk_text(self, text):
        import re
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) <= 150:  # MAX_CHUNK_LENGTH
                current += (sentence + " ")
            else:
                chunks.append(current.strip())
                current = sentence + " "
        if current:
            chunks.append(current.strip())
        return chunks

# Global instance of SpeakManager to be used throughout the application
speak_manager = SpeakManager()

def speak(text, mood_override=None):
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
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start.")
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
        return None
