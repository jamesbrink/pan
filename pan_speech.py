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

# Maximum length of each speech chunk to ensure smooth TTS
MAX_CHUNK_LENGTH = 150

class SpeakManager:
    def __init__(self):
        self._init_engine()
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.speech_count = 0
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

    def set_voice_by_mood(self, mood=None):
        if not mood:
            mood = pan_emotions.get_mood()
        settings = emotion_voices.get(mood, emotion_voices['neutral'])
        self.engine.setProperty('rate', settings['rate'])
        self.engine.setProperty('volume', settings['volume'])

    def _chunk_text(self, text):
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
        class DummyEngine:
            def say(self, text): print(f"[TTS FALLBACK] Speaking: {text}")
            def runAndWait(self): pass
            def stop(self): pass
            def setProperty(self, prop, value): pass

        self.engine = DummyEngine()
        print("[SpeakManager] Using fallback dummy TTS engine")

    def _speak_chunk(self, chunk, mood):
        try:
            self.set_voice_by_mood(mood)
            self.engine.say(chunk)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS error in chunk: {e}")
            traceback.print_exc()

    def _worker(self):
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
        self.queue.put((text, mood_override))

# Global instance of SpeakManager to be used throughout the application
speak_manager = SpeakManager()

def speak(text, mood_override=None):
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
